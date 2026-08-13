import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from yt_manager.db import connect, initialize
from yt_manager.qa import build_qa_context, ensure_qa_schema, persist_qa, render_qa_markdown, validate_qa_payload


def seed_package(db_path: str) -> tuple[int, int]:
    initialize(db_path)
    ensure_qa_schema(db_path)
    with connect(db_path) as conn:
        run_id = conn.execute(
            "INSERT INTO runs(started_at, completed_at, status, candidate_count) VALUES (?, ?, 'completed', 1)",
            ("2026-08-13T00:00:00+00:00", "2026-08-13T00:05:00+00:00"),
        ).lastrowid
        strategy_id = conn.execute(
            "INSERT INTO strategy_reports(research_run_id, created_at, summary, raw_json) VALUES (?, ?, ?, '{}')",
            (run_id, "2026-08-13T01:00:00+00:00", "Strategy summary"),
        ).lastrowid
        conn.execute(
            """INSERT INTO strategy_opportunities
            (strategy_report_id, rank, working_title, angle, why_now, audience_fit,
             confidence, source_video_ids, risks)
            VALUES (?, 1, ?, ?, ?, ?, 'HIGH', ?, ?)""",
            (
                strategy_id,
                "Safer AI Agents",
                "Show unsafe execution first, then a sandboxed workflow.",
                "Strong practical interest.",
                "Fits solo builders.",
                json.dumps(["source123"]),
                "The demo must be concrete.",
            ),
        )
        approval_id = conn.execute(
            """INSERT INTO script_approvals
            (strategy_report_id, opportunity_rank, approved_at, notes)
            VALUES (?, 1, ?, ?)""",
            (strategy_id, "2026-08-13T02:00:00+00:00", "Show the unsafe failure first."),
        ).lastrowid

        script_payload = {
            "working_title": "What Happens When Your AI Agents Can Actually Run Code Safely",
            "title_options": ["Safe Agents", "Sandboxed Agents", "Agents With Boundaries"],
            "brief": {"core_promise": "Show a safer execution pattern."},
            "script": {"hook": "This agent is about to run code on my machine."},
            "creator_inputs_needed": [{
                "placeholder": "[JOEL: show the real terminal failure]",
                "needed": "Record the real failure during the demo."
            }],
            "verification_notes": [{
                "item": "Sandbox boundary behavior",
                "reason": "Confirm exact behavior before recording."
            }],
            "inspiration_source_video_ids": ["source123"],
        }
        script_id = conn.execute(
            """INSERT INTO script_reports
            (approval_id, created_at, working_title, word_count, raw_json)
            VALUES (?, ?, ?, 852, ?)""",
            (
                approval_id,
                "2026-08-13T03:00:00+00:00",
                script_payload["working_title"],
                json.dumps(script_payload),
            ),
        ).lastrowid

        thumbnail_payload = {
            "script_report_id": script_id,
            "summary": "Three distinct safety-oriented directions.",
            "recommended_rank": 1,
            "concepts": [
                {"rank": 1, "concept_name": "Contained Blast", "thumbnail_text": "RUN IT SAFELY"},
                {"rank": 2, "concept_name": "Before vs After", "thumbnail_text": "UNSAFE vs SAFE"},
                {"rank": 3, "concept_name": "Agent in a Box", "thumbnail_text": "NO HOST ACCESS"},
            ],
        }
        thumbnail_id = conn.execute(
            """INSERT INTO thumbnail_reports
            (script_report_id, created_at, recommended_rank, summary, raw_json)
            VALUES (?, ?, 1, ?, ?)""",
            (script_id, "2026-08-13T04:00:00+00:00", thumbnail_payload["summary"], json.dumps(thumbnail_payload)),
        ).lastrowid
    return int(script_id), int(thumbnail_id)


def pass_payload(context: dict) -> dict:
    return {
        "thumbnail_report_id": context["thumbnail_report_id"],
        "script_report_id": context["script_report_id"],
        "status": "PASS",
        "summary": "The package is coherent enough for human production review.",
        "strengths": ["The script and packaging focus on the same safer-execution promise."],
        "findings": [],
        "recommended_next_action": "Proceed to human production review and complete the listed open items.",
    }


def blocking_finding() -> dict:
    return {
        "finding_key": "QA-1",
        "severity": "HIGH",
        "area": "ALIGNMENT",
        "finding": "The packaging promises a different outcome from the script.",
        "evidence": "The supplied title/thumbnail promise conflicts with the script core promise.",
        "recommended_action": "Realign the packaging with the script promise.",
        "blocks_next_step": True,
    }


def test_context_requires_validated_thumbnail(tmp_path):
    db_path = str(tmp_path / "test.db")
    initialize(db_path)
    ensure_qa_schema(db_path)
    with pytest.raises(ValueError, match="No validated Thumbnail Director report"):
        build_qa_context(db_path)


def test_context_packages_open_human_items(tmp_path):
    db_path = str(tmp_path / "test.db")
    script_id, thumbnail_id = seed_package(db_path)
    context = build_qa_context(db_path)
    assert context["script_report_id"] == script_id
    assert context["thumbnail_report_id"] == thumbnail_id
    assert context["deterministic_checks"]["thumbnail_concept_count"] == 3
    assert context["deterministic_checks"]["creator_inputs_needed_count"] == 1
    assert context["deterministic_checks"]["verification_notes_count"] == 1


def test_pass_allows_explicit_open_human_items(tmp_path):
    db_path = str(tmp_path / "test.db")
    seed_package(db_path)
    context = build_qa_context(db_path)
    validate_qa_payload(pass_payload(context), context)


def test_pass_rejects_high_or_blocking_finding(tmp_path):
    db_path = str(tmp_path / "test.db")
    seed_package(db_path)
    context = build_qa_context(db_path)
    payload = pass_payload(context)
    payload["findings"] = [blocking_finding()]
    with pytest.raises(ValueError, match="cannot PASS"):
        validate_qa_payload(payload, context)


def test_needs_changes_requires_real_blocker(tmp_path):
    db_path = str(tmp_path / "test.db")
    seed_package(db_path)
    context = build_qa_context(db_path)
    payload = pass_payload(context)
    payload["status"] = "NEEDS_CHANGES"
    payload["findings"] = [{
        "finding_key": "QA-1",
        "severity": "MEDIUM",
        "area": "SCRIPT",
        "finding": "A transition could be tighter.",
        "evidence": "One setup idea is repeated.",
        "recommended_action": "Tighten it during human editing.",
        "blocks_next_step": False,
    }]
    with pytest.raises(ValueError, match="requires at least one"):
        validate_qa_payload(payload, context)


def test_render_and_persist_needs_changes(tmp_path):
    db_path = str(tmp_path / "test.db")
    seed_package(db_path)
    context = build_qa_context(db_path)
    payload = pass_payload(context)
    payload["status"] = "NEEDS_CHANGES"
    payload["summary"] = "One material alignment defect must be fixed."
    payload["findings"] = [blocking_finding()]
    payload["recommended_next_action"] = "Fix the alignment defect, then rerun QA."

    markdown = render_qa_markdown(payload, context)
    assert "Status: **NEEDS_CHANGES**" in markdown
    assert "## Open creator inputs" in markdown
    assert "## Verify before recording" in markdown

    report_id = persist_qa(payload, context, db_path)
    with connect(db_path) as conn:
        report = conn.execute("SELECT status FROM qa_reports WHERE id=?", (report_id,)).fetchone()
        count = conn.execute("SELECT COUNT(*) AS count FROM qa_findings WHERE qa_report_id=?", (report_id,)).fetchone()["count"]
    assert report["status"] == "NEEDS_CHANGES"
    assert count == 1
