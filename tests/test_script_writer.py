import json
from datetime import datetime, timezone
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from yt_manager.db import connect, initialize
from yt_manager.script_writer import (
    approve_opportunity,
    build_script_context,
    persist_script,
    render_script_markdown,
    script_word_count,
    validate_script_payload,
)


def seed_strategy(db_path: str) -> None:
    initialize(db_path)
    with connect(db_path) as conn:
        run_id = conn.execute(
            """INSERT INTO runs(started_at, completed_at, status, candidate_count)
            VALUES (?, ?, 'completed', 1)""",
            ("2026-08-13T00:00:00+00:00", "2026-08-13T00:05:00+00:00"),
        ).lastrowid
        conn.execute(
            """INSERT INTO candidates
            (run_id, video_id, channel_id, channel_title, title, published_at,
             views, baseline_views, outlier_score, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id,
                "source123",
                "channel123",
                "Example Channel",
                "Competitor Software Factory Title",
                "2026-08-03T13:00:00Z",
                38000,
                25000,
                1.52,
                "https://www.youtube.com/watch?v=source123",
            ),
        )
        report_id = conn.execute(
            """INSERT INTO strategy_reports(research_run_id, created_at, summary, raw_json)
            VALUES (?, ?, ?, ?)""",
            (run_id, "2026-08-13T01:00:00+00:00", "Strategy summary", "{}"),
        ).lastrowid
        conn.execute(
            """INSERT INTO strategy_opportunities
            (strategy_report_id, rank, working_title, angle, why_now, audience_fit,
             confidence, source_video_ids, risks)
            VALUES (?, 1, ?, ?, ?, ?, 'HIGH', ?, ?)""",
            (
                report_id,
                "Build Safer AI Agents",
                "Test agent sandboxes with a real workflow.",
                "A mature breakout supports interest in practical agent infrastructure.",
                "Fits solo builders moving agents into real workflows.",
                json.dumps(["source123"]),
                "Needs a distinct, evidence-based demo.",
            ),
        )


def write_profile(path: Path) -> None:
    path.write_text(
        json.dumps({
            "channel_name": "Joel Michael Loh",
            "positioning": "Practical AI agents and automation for builders.",
            "target_audience": ["solo builders"],
            "content_pillars": ["practical AI agents"],
        }),
        encoding="utf-8",
    )


def valid_payload(context: dict) -> dict:
    narration = " ".join(["word"] * 210)
    return {
        "approval_id": context["approval"]["approval_id"],
        "strategy_report_id": context["approval"]["strategy_report_id"],
        "opportunity_rank": context["approval"]["opportunity_rank"],
        "working_title": "I Put My AI Agent in a Sandbox",
        "title_options": [
            "I Put My AI Agent in a Sandbox",
            "The Safety Layer My AI Agents Were Missing",
            "I Tested a Safer Way to Let AI Run Code",
        ],
        "brief": {
            "viewer_problem": "Agents need real execution without risking the host system.",
            "core_promise": "Show a practical isolation pattern and its tradeoffs.",
            "unique_angle": "A real test with explicit failure modes rather than an architecture overview.",
            "opening_hook": "Let the agent break the unsafe setup before showing the safer one.",
            "proof_plan": ["Run the same task with and without isolation."],
            "structure": ["The risk", "The sandbox", "The test"],
            "cta": "Try the pattern on one bounded workflow.",
        },
        "script": {
            "hook": "This agent is about to run code on my machine, and I want it to fail safely.",
            "sections": [
                {"heading": "The risk", "narration": narration},
                {"heading": "The sandbox", "narration": narration},
                {"heading": "The test", "narration": narration},
            ],
            "conclusion": "The point is not maximum autonomy. It is useful autonomy with boundaries.",
            "cta": "Start with one bounded workflow and make the failure mode visible.",
        },
        "inspiration_source_video_ids": ["source123"],
        "verification_notes": [],
        "creator_inputs_needed": [],
    }


def test_script_context_requires_human_approval(tmp_path):
    db_path = str(tmp_path / "test.db")
    profile_path = tmp_path / "profile.json"
    seed_strategy(db_path)
    write_profile(profile_path)

    with pytest.raises(ValueError, match="No human-approved"):
        build_script_context(db_path, str(profile_path))


def test_approval_builds_source_backed_script_context(tmp_path):
    db_path = str(tmp_path / "test.db")
    profile_path = tmp_path / "profile.json"
    seed_strategy(db_path)
    write_profile(profile_path)

    approval = approve_opportunity(
        db_path,
        1,
        notes="Make the demo concrete.",
        now=datetime(2026, 8, 13, 2, 0, tzinfo=timezone.utc),
    )
    context = build_script_context(
        db_path,
        str(profile_path),
        approval_id=approval["approval_id"],
        minimum_words=600,
        now=datetime(2026, 8, 13, 2, 5, tzinfo=timezone.utc),
    )

    assert context["approval"]["opportunity_rank"] == 1
    assert context["approval"]["human_notes"] == "Make the demo concrete."
    assert context["inspiration_sources"][0]["video_id"] == "source123"
    assert context["script_requirements"]["minimum_words"] == 600


def test_valid_script_can_render_and_persist(tmp_path):
    db_path = str(tmp_path / "test.db")
    profile_path = tmp_path / "profile.json"
    seed_strategy(db_path)
    write_profile(profile_path)
    approval = approve_opportunity(db_path, 1)
    context = build_script_context(db_path, str(profile_path), approval_id=approval["approval_id"])
    payload = valid_payload(context)

    validate_script_payload(payload, context)
    assert script_word_count(payload) >= 600
    markdown = render_script_markdown(payload, context)
    assert "## Full script" in markdown
    assert "topic/packaging evidence only" in markdown

    report_id = persist_script(payload, context, db_path)
    with connect(db_path) as conn:
        row = conn.execute("SELECT word_count FROM script_reports WHERE id=?", (report_id,)).fetchone()
    assert row["word_count"] >= 600


def test_script_rejects_unapproved_source_id(tmp_path):
    db_path = str(tmp_path / "test.db")
    profile_path = tmp_path / "profile.json"
    seed_strategy(db_path)
    write_profile(profile_path)
    approval = approve_opportunity(db_path, 1)
    context = build_script_context(db_path, str(profile_path), approval_id=approval["approval_id"])
    payload = valid_payload(context)
    payload["inspiration_source_video_ids"] = ["hallucinated"]

    with pytest.raises(ValueError, match="unapproved source"):
        validate_script_payload(payload, context)


def test_script_rejects_copied_competitor_title(tmp_path):
    db_path = str(tmp_path / "test.db")
    profile_path = tmp_path / "profile.json"
    seed_strategy(db_path)
    write_profile(profile_path)
    approval = approve_opportunity(db_path, 1)
    context = build_script_context(db_path, str(profile_path), approval_id=approval["approval_id"])
    payload = valid_payload(context)
    payload["working_title"] = "Competitor Software Factory Title"
    payload["title_options"][0] = "Competitor Software Factory Title"

    with pytest.raises(ValueError, match="copy a competitor"):
        validate_script_payload(payload, context)
