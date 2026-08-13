import json
from datetime import datetime, timezone
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from yt_manager.db import connect, initialize
from yt_manager.thumbnail_director import (
    build_thumbnail_context,
    persist_thumbnail,
    render_thumbnail_markdown,
    validate_thumbnail_payload,
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


def seed_validated_script(db_path: str) -> int:
    initialize(db_path)
    script_payload = {
        "approval_id": 1,
        "strategy_report_id": 1,
        "opportunity_rank": 1,
        "working_title": "What Happens When Your AI Agents Can Actually Run Code Safely",
        "title_options": [
            "What Happens When Your AI Agents Can Actually Run Code Safely",
            "I Put My AI Agent in a Sandbox",
            "The Safety Layer My AI Agents Were Missing",
        ],
        "brief": {
            "viewer_problem": "Agents need real execution without risking the host system.",
            "core_promise": "Show a practical isolation pattern and its tradeoffs.",
            "unique_angle": "Let the unsafe workflow fail first, then show the bounded version.",
            "opening_hook": "The same task behaves very differently once it is isolated.",
            "proof_plan": ["Compare unsafe and isolated runs."],
            "structure": ["Risk", "Sandbox", "Test"],
            "cta": "Start with one bounded workflow.",
        },
        "script": {
            "hook": "This agent is about to run code, and the first setup gives it too much access.",
            "sections": [],
            "conclusion": "Useful autonomy needs boundaries.",
            "cta": "Try the pattern on one bounded workflow.",
        },
        "inspiration_source_video_ids": ["source123"],
        "verification_notes": [{"item": "Sandbox capability", "reason": "Verify current product behavior."}],
        "creator_inputs_needed": [{"placeholder": "[JOEL: unsafe demo]", "needed": "Record the unsafe run."}],
    }

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
        strategy_report_id = conn.execute(
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
                strategy_report_id,
                "What Happens When Your AI Agents Can Actually Run Code Safely",
                "Demonstrate unsafe execution, then a sandboxed alternative.",
                "A mature software-factory breakout supports interest.",
                "Fits builders moving agents into real workflows.",
                json.dumps(["source123"]),
                "The visual must show proof rather than generic AI imagery.",
            ),
        )
        approval_id = conn.execute(
            """INSERT INTO script_approvals
            (strategy_report_id, opportunity_rank, approved_at, notes)
            VALUES (?, 1, ?, ?)""",
            (
                strategy_report_id,
                "2026-08-13T02:00:00+00:00",
                "Show the unsafe failure mode first, then the sandboxed version.",
            ),
        ).lastrowid
        script_payload["approval_id"] = approval_id
        script_payload["strategy_report_id"] = strategy_report_id
        script_report_id = conn.execute(
            """INSERT INTO script_reports
            (approval_id, created_at, working_title, word_count, raw_json)
            VALUES (?, ?, ?, ?, ?)""",
            (
                approval_id,
                "2026-08-13T03:00:00+00:00",
                script_payload["working_title"],
                852,
                json.dumps(script_payload),
            ),
        ).lastrowid
    return int(script_report_id)


def valid_payload(context: dict) -> dict:
    source_id = context["validated_script"]["inspiration_source_video_ids"][0]
    return {
        "script_report_id": context["script_report_id"],
        "summary": "Use concrete failure-versus-control visuals instead of generic AI imagery.",
        "recommended_rank": 1,
        "concepts": [
            {
                "rank": 1,
                "concept_name": "Unsafe vs Sandboxed",
                "thumbnail_text": "UNSAFE vs SAFE",
                "visual_hook": "A split screen showing a red unrestricted terminal on one side and a contained sandbox box on the other.",
                "composition": "Joel centered between two large terminal states with clear left/right contrast and generous negative space.",
                "title_alignment": "The title asks what safe execution looks like; the thumbnail instantly shows the contrast.",
                "emotional_tone": "Danger turning into control.",
                "rationale": "It visualizes the script's core before/after proof in one glance.",
                "render_prompt": "YouTube thumbnail, 16:9, Joel between two oversized terminal panels, left panel clearly risky and unrestricted, right panel visibly contained inside a simple sandbox boundary, minimal labels, strong readable contrast, no tiny UI text.",
                "creator_assets_needed": ["Joel cutout or portrait", "Unsafe terminal screenshot", "Sandboxed terminal screenshot"],
                "source_video_ids": [source_id],
                "risks": "The split screen can become busy if the terminal screenshots contain too much detail."
            },
            {
                "rank": 2,
                "concept_name": "The Boundary",
                "thumbnail_text": "ONE SAFE BOX",
                "visual_hook": "A glowing containment box around one agent process while dangerous-looking system files remain outside it.",
                "composition": "Large sandbox boundary occupies two-thirds of the frame; Joel points toward the boundary from the remaining third.",
                "title_alignment": "Adds the visual answer: safety comes from a clear execution boundary.",
                "emotional_tone": "Relief and control.",
                "rationale": "Reduces a technical idea to one strong visual metaphor that fits the script's architecture.",
                "render_prompt": "YouTube thumbnail, 16:9, one clean luminous rectangular sandbox boundary containing an AI coding process, host system elements visibly outside, Joel pointing at the boundary, very simple shapes, bold separation, minimal text.",
                "creator_assets_needed": ["Joel pointing pose"],
                "source_video_ids": [source_id],
                "risks": "The containment metaphor must still look like software execution rather than cybersecurity stock art."
            },
            {
                "rank": 3,
                "concept_name": "The Bad Command",
                "thumbnail_text": "WOULD YOU RUN THIS?",
                "visual_hook": "One huge dangerous command line with Joel reacting before it executes.",
                "composition": "Oversized terminal command dominates the frame; Joel reaction on the side; one small sandbox icon acts as the alternative.",
                "title_alignment": "Creates tension around the exact risk the title promises to solve without repeating the title.",
                "emotional_tone": "Tension and curiosity.",
                "rationale": "Makes the failure mode concrete and creates a strong curiosity gap before the safer pattern is revealed.",
                "render_prompt": "YouTube thumbnail, 16:9, one oversized terminal command as the central object, Joel reacting with concern, small clear sandbox shield or boundary icon nearby, uncluttered composition, no fake product branding, no tiny text.",
                "creator_assets_needed": ["Joel reaction pose", "Real demo command or sanitized command example"],
                "source_video_ids": [source_id],
                "risks": "A fabricated or overly dramatic command would weaken credibility, so use a real or clearly sanitized demo command."
            }
        ]
    }


def test_thumbnail_context_requires_validated_script(tmp_path):
    db_path = str(tmp_path / "test.db")
    profile_path = tmp_path / "profile.json"
    initialize(db_path)
    write_profile(profile_path)

    with pytest.raises(ValueError, match="No validated Script Writer report"):
        build_thumbnail_context(db_path, str(profile_path))


def test_thumbnail_context_carries_validated_script_and_sources(tmp_path):
    db_path = str(tmp_path / "test.db")
    profile_path = tmp_path / "profile.json"
    write_profile(profile_path)
    script_report_id = seed_validated_script(db_path)

    context = build_thumbnail_context(
        db_path,
        str(profile_path),
        script_report_id=script_report_id,
        now=datetime(2026, 8, 13, 4, 0, tzinfo=timezone.utc),
    )

    assert context["script_report_id"] == script_report_id
    assert context["validated_script"]["word_count"] == 852
    assert context["validated_script"]["inspiration_source_video_ids"] == ["source123"]
    assert context["thumbnail_requirements"]["concept_count"] == 3
    assert context["thumbnail_requirements"]["max_text_words"] == 5


def test_valid_thumbnail_can_render_and_persist(tmp_path):
    db_path = str(tmp_path / "test.db")
    profile_path = tmp_path / "profile.json"
    write_profile(profile_path)
    script_report_id = seed_validated_script(db_path)
    context = build_thumbnail_context(db_path, str(profile_path), script_report_id=script_report_id)
    payload = valid_payload(context)

    validate_thumbnail_payload(payload, context)
    markdown = render_thumbnail_markdown(payload, context)
    assert "RECOMMENDED" in markdown
    assert "creative directions only" in markdown

    report_id = persist_thumbnail(payload, context, db_path)
    with connect(db_path) as conn:
        report = conn.execute("SELECT recommended_rank FROM thumbnail_reports WHERE id=?", (report_id,)).fetchone()
        count = conn.execute("SELECT COUNT(*) AS n FROM thumbnail_concepts WHERE thumbnail_report_id=?", (report_id,)).fetchone()["n"]
    assert report["recommended_rank"] == 1
    assert count == 3


def test_thumbnail_rejects_text_over_word_limit(tmp_path):
    db_path = str(tmp_path / "test.db")
    profile_path = tmp_path / "profile.json"
    write_profile(profile_path)
    script_report_id = seed_validated_script(db_path)
    context = build_thumbnail_context(db_path, str(profile_path), script_report_id=script_report_id)
    payload = valid_payload(context)
    payload["concepts"][0]["thumbnail_text"] = "THIS TEXT HAS WAY TOO MANY WORDS"

    with pytest.raises(ValueError, match="exceeds 5 words"):
        validate_thumbnail_payload(payload, context)


def test_thumbnail_rejects_unapproved_source_id(tmp_path):
    db_path = str(tmp_path / "test.db")
    profile_path = tmp_path / "profile.json"
    write_profile(profile_path)
    script_report_id = seed_validated_script(db_path)
    context = build_thumbnail_context(db_path, str(profile_path), script_report_id=script_report_id)
    payload = valid_payload(context)
    payload["concepts"][1]["source_video_ids"] = ["hallucinated"]

    with pytest.raises(ValueError, match="unapproved source"):
        validate_thumbnail_payload(payload, context)


def test_thumbnail_rejects_duplicate_visual_hooks(tmp_path):
    db_path = str(tmp_path / "test.db")
    profile_path = tmp_path / "profile.json"
    write_profile(profile_path)
    script_report_id = seed_validated_script(db_path)
    context = build_thumbnail_context(db_path, str(profile_path), script_report_id=script_report_id)
    payload = valid_payload(context)
    payload["concepts"][1]["visual_hook"] = payload["concepts"][0]["visual_hook"]

    with pytest.raises(ValueError, match="distinct visual hooks"):
        validate_thumbnail_payload(payload, context)
