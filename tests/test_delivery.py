import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from yt_manager.db import connect, initialize
from yt_manager.production import (
    build_production_context,
    ensure_production_schema,
    validate_production_payload,
)
from yt_manager.production_output import persist_production, render_production_markdown
from yt_manager.qa import ensure_qa_schema


def seed_qa_package(db_path: str, status: str = "PASS") -> None:
    initialize(db_path)
    ensure_qa_schema(db_path)
    ensure_production_schema(db_path)
    with connect(db_path) as conn:
        run_id = conn.execute(
            "INSERT INTO runs(started_at, completed_at, status, candidate_count) VALUES (?, ?, 'completed', 0)",
            ("2026-08-13T00:00:00+00:00", "2026-08-13T00:05:00+00:00"),
        ).lastrowid
        strategy_id = conn.execute(
            "INSERT INTO strategy_reports(research_run_id, created_at, summary, raw_json) VALUES (?, ?, ?, '{}')",
            (run_id, "2026-08-13T01:00:00+00:00", "Strategy"),
        ).lastrowid
        conn.execute(
            """INSERT INTO strategy_opportunities
            (strategy_report_id, rank, working_title, angle, why_now, audience_fit,
             confidence, source_video_ids, risks)
            VALUES (?, 1, ?, ?, ?, ?, 'HIGH', '[]', ?)""",
            (strategy_id, "Safer agents", "Unsafe first, sandbox second", "Timely", "Builders", "Demo risk"),
        )
        approval_id = conn.execute(
            "INSERT INTO script_approvals(strategy_report_id, opportunity_rank, approved_at, notes) VALUES (?, 1, ?, ?)",
            (strategy_id, "2026-08-13T02:00:00+00:00", "Show the unsafe failure first."),
        ).lastrowid
        script = {
            "working_title": "I Let My AI Agent Run Code Unsandboxed. Here's What Broke.",
            "script": {
                "hook": "The agent can touch the host.",
                "sections": [
                    {"heading": "Unsafe demo", "narration": "Show the failure."},
                    {"heading": "Sandboxed demo", "narration": "Show containment."},
                    {"heading": "Tradeoffs", "narration": "Explain tradeoffs."}
                ],
                "conclusion": "Use boundaries.",
                "cta": "Test one bounded workflow."
            },
            "creator_inputs_needed": [
                {"placeholder": "[JOEL: show the real failure]", "needed": "Record the failure."},
                {"placeholder": "[JOEL: explain your tradeoff]", "needed": "Give a first-hand tradeoff."}
            ],
            "verification_notes": [
                {"item": "Sandbox tool choice", "reason": "Match the real demo."},
                {"item": "Performance overhead", "reason": "Verify any numbers used."}
            ]
        }
        script_id = conn.execute(
            "INSERT INTO script_reports(approval_id, created_at, working_title, word_count, raw_json) VALUES (?, ?, ?, 850, ?)",
            (approval_id, "2026-08-13T03:00:00+00:00", script["working_title"], json.dumps(script)),
        ).lastrowid
        thumbnails = {
            "recommended_rank": 1,
            "concepts": [
                {"rank": 1, "concept_name": "What Broke", "thumbnail_text": "WHAT BROKE", "creator_assets_needed": ["Terminal failure screenshot"]},
                {"rank": 2, "concept_name": "Unsafe vs Safe", "thumbnail_text": "UNSAFE / SAFE", "creator_assets_needed": []},
                {"rank": 3, "concept_name": "Agent Box", "thumbnail_text": "CONTAIN IT", "creator_assets_needed": []}
            ]
        }
        thumbnail_id = conn.execute(
            "INSERT INTO thumbnail_reports(script_report_id, created_at, recommended_rank, summary, raw_json) VALUES (?, ?, 1, ?, ?)",
            (script_id, "2026-08-13T04:00:00+00:00", "Concepts", json.dumps(thumbnails)),
        ).lastrowid
        qa = {
            "status": status,
            "summary": "Package review",
            "strengths": ["Aligned"],
            "findings": [],
            "recommended_next_action": "Proceed to human production review."
        }
        conn.execute(
            "INSERT INTO qa_reports(thumbnail_report_id, created_at, status, summary, raw_json) VALUES (?, ?, ?, ?, ?)",
            (thumbnail_id, "2026-08-13T05:00:00+00:00", status, qa["summary"], json.dumps(qa)),
        )


def valid_payload(context: dict) -> dict:
    selected = context["selected_thumbnail_concept"]
    return {
        "qa_report_id": context["qa_report_id"],
        "script_report_id": context["script_report_id"],
        "thumbnail_report_id": context["thumbnail_report_id"],
        "summary": "Record the unsafe demo first, then the contained version and tradeoffs.",
        "recording_plan": [
            {"order": 1, "segment_name": "Hook", "script_section": "HOOK", "objective": "Set the risk.", "creator_inputs": [], "capture_notes": "Talking head plus terminal setup.", "b_roll": []},
            {"order": 2, "segment_name": "Unsafe demo", "script_section": "Unsafe demo", "objective": "Show the real failure.", "creator_inputs": ["[JOEL: show the real failure]"], "capture_notes": "Record the failure continuously.", "b_roll": ["Terminal close-up"]},
            {"order": 3, "segment_name": "Tradeoffs", "script_section": "Tradeoffs", "objective": "Add first-hand judgment.", "creator_inputs": ["[JOEL: explain your tradeoff]"], "capture_notes": "Talking-head reflection.", "b_roll": []}
        ],
        "verification_plan": [
            {"item": "Sandbox tool choice", "action": "Confirm the exact tool used in the demo.", "required_before_recording": True},
            {"item": "Performance overhead", "action": "Verify any performance number before saying it on camera.", "required_before_recording": True}
        ],
        "thumbnail_handoff": {
            "recommended_rank": 1,
            "concept_name": selected["concept_name"],
            "thumbnail_text": selected["thumbnail_text"],
            "creator_assets_needed": selected["creator_assets_needed"],
            "capture_during_recording": ["Capture the actual failure frame at readable scale."]
        },
        "asset_plan": [
            {"asset": "Terminal failure screenshot", "source": "THUMBNAIL", "purpose": "Recommended thumbnail evidence.", "required_before_recording": False}
        ],
        "editing_notes": [
            {"moment": "Unsafe demo", "direction": "Keep the failure visible long enough to understand what happened."}
        ],
        "pre_recording_checklist": [
            {"item": "Confirm sandbox tool and test environment", "required": True, "source": "VERIFICATION"}
        ],
        "risks": ["Do not demonstrate destructive behavior outside a disposable test environment."]
    }


def test_context_requires_qa_report(tmp_path):
    db_path = str(tmp_path / "test.db")
    initialize(db_path)
    ensure_qa_schema(db_path)
    with pytest.raises(ValueError, match="No validated QA report"):
        build_production_context(db_path)


def test_context_rejects_non_pass_qa(tmp_path):
    db_path = str(tmp_path / "test.db")
    seed_qa_package(db_path, status="NEEDS_CHANGES")
    with pytest.raises(ValueError, match="requires QA status PASS"):
        build_production_context(db_path)


def test_context_packages_pass_and_recommended_thumbnail(tmp_path):
    db_path = str(tmp_path / "test.db")
    seed_qa_package(db_path)
    context = build_production_context(db_path)
    assert context["qa_pass"]["status"] == "PASS"
    assert context["selected_thumbnail_concept"]["concept_name"] == "What Broke"
    assert context["requirements"]["creator_input_count"] == 2
    assert context["requirements"]["verification_count"] == 2


def test_validator_rejects_missing_creator_placeholder(tmp_path):
    db_path = str(tmp_path / "test.db")
    seed_qa_package(db_path)
    context = build_production_context(db_path)
    payload = valid_payload(context)
    payload["recording_plan"][2]["creator_inputs"] = []
    with pytest.raises(ValueError, match="creator input coverage"):
        validate_production_payload(payload, context)


def test_validator_rejects_missing_verification_item(tmp_path):
    db_path = str(tmp_path / "test.db")
    seed_qa_package(db_path)
    context = build_production_context(db_path)
    payload = valid_payload(context)
    payload["verification_plan"] = payload["verification_plan"][:1]
    with pytest.raises(ValueError, match="verification coverage"):
        validate_production_payload(payload, context)


def test_valid_delivery_renders_and_persists(tmp_path):
    db_path = str(tmp_path / "test.db")
    seed_qa_package(db_path)
    context = build_production_context(db_path)
    payload = valid_payload(context)
    validate_production_payload(payload, context)
    markdown = render_production_markdown(payload, context)
    assert "## Recording plan" in markdown
    assert "## Verification before recording" in markdown
    assert "## Pre-recording checklist" in markdown
    report_id = persist_production(payload, context, db_path)
    with connect(db_path) as conn:
        report = conn.execute("SELECT qa_report_id FROM production_reports WHERE id=?", (report_id,)).fetchone()
        count = conn.execute("SELECT COUNT(*) count FROM production_items WHERE production_report_id=?", (report_id,)).fetchone()["count"]
    assert report["qa_report_id"] == context["qa_report_id"]
    assert count == 8
