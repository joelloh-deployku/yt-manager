import json
from datetime import datetime, timezone
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from yt_manager.db import connect, initialize
from yt_manager.strategy import (
    build_strategy_context,
    persist_strategy,
    render_strategy_markdown,
    validate_strategy_payload,
)


def _seed_strategy_db(db_path: str) -> None:
    initialize(db_path)
    with connect(db_path) as conn:
        prior = conn.execute(
            "INSERT INTO runs(started_at, completed_at, status, candidate_count) VALUES (?, ?, ?, ?)",
            ("2026-08-12T12:00:00+00:00", "2026-08-12T12:05:00+00:00", "completed", 1),
        ).lastrowid
        current = conn.execute(
            "INSERT INTO runs(started_at, completed_at, status, candidate_count) VALUES (?, ?, ?, ?)",
            ("2026-08-13T12:00:00+00:00", "2026-08-13T12:05:00+00:00", "completed", 3),
        ).lastrowid

        conn.execute(
            "INSERT INTO video_snapshots(run_id, video_id, channel_id, observed_at, views) VALUES (?, ?, ?, ?, ?)",
            (prior, "v1", "c1", "2026-08-12T12:00:00+00:00", 100),
        )

        candidates = [
            (current, "v1", "c1", "Channel One", "Agent Factory", "2026-08-12T12:00:00Z", 150, 100.0, 1.5, "https://youtu.be/v1"),
            (current, "v2", "c2", "Channel Two", "Shared AI Memory", "2026-08-10T12:00:00Z", 95, 100.0, 0.95, "https://youtu.be/v2"),
            (current, "v3", "c3", "Channel Three", "AI Business", "2026-08-03T12:00:00Z", 60, 100.0, 0.6, "https://youtu.be/v3"),
        ]
        conn.executemany(
            """INSERT INTO candidates
            (run_id, video_id, channel_id, channel_title, title, published_at,
             views, baseline_views, outlier_score, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            candidates,
        )
        conn.executemany(
            "INSERT INTO video_snapshots(run_id, video_id, channel_id, observed_at, views) VALUES (?, ?, ?, ?, ?)",
            [
                (current, "v1", "c1", "2026-08-13T12:00:00+00:00", 150),
                (current, "v2", "c2", "2026-08-13T12:00:00+00:00", 95),
                (current, "v3", "c3", "2026-08-13T12:00:00+00:00", 60),
            ],
        )


def _profile(path: Path) -> None:
    path.write_text(
        json.dumps({
            "channel_name": "Joel Michael Loh",
            "positioning": "Practical AI agents and automation",
            "content_pillars": ["agents", "automation"],
        }),
        encoding="utf-8",
    )


def _valid_payload(run_id: int) -> dict:
    return {
        "research_run_id": run_id,
        "summary": "Agentic software and shared memory are the strongest transferable signals.",
        "opportunities": [
            {
                "rank": 1,
                "working_title": "I Built a One-Person AI Software Factory",
                "angle": "Build and demonstrate an agentic software factory.",
                "why_now": "A mature relevant breakout is outperforming its channel baseline.",
                "audience_fit": "Strong match for solo builders using AI agents.",
                "confidence": "HIGH",
                "source_video_ids": ["v1"],
                "risks": "Needs a concrete build to avoid becoming generic commentary."
            },
            {
                "rank": 2,
                "working_title": "Give Every AI Agent the Same Memory",
                "angle": "Show a shared-memory workflow across tools.",
                "why_now": "The topic is relevant and performing near baseline.",
                "audience_fit": "Useful infrastructure for multi-agent builders.",
                "confidence": "MEDIUM",
                "source_video_ids": ["v2"],
                "risks": "Performance signal is not a breakout."
            },
            {
                "rank": 3,
                "working_title": "Can AI Run a One-Person Business?",
                "angle": "Test a narrow business workflow end to end.",
                "why_now": "The business framing is relevant despite weaker measured performance.",
                "audience_fit": "Directly serves entrepreneurs and creators.",
                "confidence": "LOW",
                "source_video_ids": ["v3"],
                "risks": "Source video is a mature underperformer."
            }
        ]
    }


def test_strategy_context_includes_velocity_and_provisional_state(tmp_path):
    db_path = str(tmp_path / "test.db")
    profile_path = tmp_path / "profile.json"
    _seed_strategy_db(db_path)
    _profile(profile_path)

    context = build_strategy_context(
        db_path,
        str(profile_path),
        now=datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc),
    )

    assert context["research_run_id"] == 2
    assert context["candidate_count"] == 3
    first = context["candidates"][0]
    assert first["video_id"] == "v1"
    assert first["performance_tier"] == "breakout"
    assert first["provisional_under_48h"] is True
    assert first["view_delta_since_previous_snapshot"] == 50
    assert first["velocity_views_per_hour"] == 2.08


def test_strategy_validation_rejects_unknown_source(tmp_path):
    db_path = str(tmp_path / "test.db")
    profile_path = tmp_path / "profile.json"
    _seed_strategy_db(db_path)
    _profile(profile_path)
    context = build_strategy_context(db_path, str(profile_path))
    payload = _valid_payload(context["research_run_id"])
    payload["opportunities"][0]["source_video_ids"] = ["not-in-run"]

    with pytest.raises(ValueError, match="unknown source video IDs"):
        validate_strategy_payload(payload, context)


def test_strategy_persists_and_renders_source_evidence(tmp_path):
    db_path = str(tmp_path / "test.db")
    profile_path = tmp_path / "profile.json"
    _seed_strategy_db(db_path)
    _profile(profile_path)
    context = build_strategy_context(
        db_path,
        str(profile_path),
        now=datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc),
    )
    payload = _valid_payload(context["research_run_id"])

    validate_strategy_payload(payload, context)
    report_id = persist_strategy(payload, context, db_path)
    markdown = render_strategy_markdown(payload, context)

    assert report_id > 0
    assert "I Built a One-Person AI Software Factory" in markdown
    assert "https://youtu.be/v1" in markdown
    with connect(db_path) as conn:
        report_count = conn.execute("SELECT COUNT(*) FROM strategy_reports").fetchone()[0]
        opportunity_count = conn.execute("SELECT COUNT(*) FROM strategy_opportunities").fetchone()[0]
    assert report_count == 1
    assert opportunity_count == 3
