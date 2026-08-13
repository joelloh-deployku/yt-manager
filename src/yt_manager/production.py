"""Deterministic production handoff for QA-passed content packages."""

import json
from datetime import datetime, timezone
from pathlib import Path

from yt_manager.db import connect
from yt_manager.qa import ensure_qa_schema

PRODUCTION_SCHEMA = """
CREATE TABLE IF NOT EXISTS production_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    qa_report_id INTEGER NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    summary TEXT NOT NULL,
    raw_json TEXT NOT NULL,
    FOREIGN KEY(qa_report_id) REFERENCES qa_reports(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS production_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    production_report_id INTEGER NOT NULL,
    item_type TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    label TEXT NOT NULL,
    required_before_recording INTEGER NOT NULL,
    raw_json TEXT NOT NULL,
    UNIQUE(production_report_id, item_type, sort_order),
    FOREIGN KEY(production_report_id) REFERENCES production_reports(id) ON DELETE CASCADE
);
"""


def _now(now=None):
    value = now or datetime.now(timezone.utc)
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def ensure_production_schema(db_path: str) -> None:
    ensure_qa_schema(db_path)
    with connect(db_path) as conn:
        conn.executescript(PRODUCTION_SCHEMA)


def build_production_context(db_path: str, qa_report_id: int | None = None, now=None) -> dict:
    ensure_production_schema(db_path)
    where = "WHERE qr.id=?" if qa_report_id is not None else ""
    params = (qa_report_id,) if qa_report_id is not None else ()
    with connect(db_path) as conn:
        row = conn.execute(
            f"""SELECT qr.id qa_report_id, qr.status qa_status, qr.summary qa_summary,
                       qr.raw_json qa_json, tr.id thumbnail_report_id,
                       tr.recommended_rank, tr.raw_json thumbnail_json,
                       scr.id script_report_id, scr.word_count, scr.raw_json script_json,
                       sa.id approval_id, sa.strategy_report_id, sa.opportunity_rank,
                       sa.notes human_notes, sr.research_run_id,
                       so.angle, so.why_now, so.audience_fit, so.confidence, so.risks
                FROM qa_reports qr
                JOIN thumbnail_reports tr ON tr.id=qr.thumbnail_report_id
                JOIN script_reports scr ON scr.id=tr.script_report_id
                JOIN script_approvals sa ON sa.id=scr.approval_id
                JOIN strategy_reports sr ON sr.id=sa.strategy_report_id
                JOIN strategy_opportunities so
                  ON so.strategy_report_id=sa.strategy_report_id
                 AND so.rank=sa.opportunity_rank
                {where}
                ORDER BY qr.id DESC LIMIT 1""",
            params,
        ).fetchone()
    if not row:
        raise ValueError("No validated QA report found")
    if str(row["qa_status"]).upper() != "PASS":
        raise ValueError("Production handoff requires QA status PASS")

    qa = json.loads(row["qa_json"])
    script = json.loads(row["script_json"])
    thumbnails = json.loads(row["thumbnail_json"])
    rank = int(row["recommended_rank"])
    selected = next((x for x in thumbnails.get("concepts", []) if x.get("rank") == rank), None)
    if not selected:
        raise ValueError("Recommended thumbnail concept is missing")

    body = script.get("script", {})
    sections = ["HOOK"] + [
        str(x.get("heading", "")).strip()
        for x in body.get("sections", []) if isinstance(x, dict) and str(x.get("heading", "")).strip()
    ] + ["CONCLUSION", "CTA"]

    return {
        "version": 1,
        "prepared_at": _now(now).isoformat(),
        "qa_report_id": int(row["qa_report_id"]),
        "script_report_id": int(row["script_report_id"]),
        "thumbnail_report_id": int(row["thumbnail_report_id"]),
        "approval": {
            "approval_id": int(row["approval_id"]),
            "strategy_report_id": int(row["strategy_report_id"]),
            "research_run_id": int(row["research_run_id"]),
            "opportunity_rank": int(row["opportunity_rank"]),
            "human_notes": row["human_notes"],
        },
        "approved_strategy": {
            "angle": row["angle"], "why_now": row["why_now"],
            "audience_fit": row["audience_fit"], "confidence": row["confidence"],
            "risks": row["risks"],
        },
        "qa_pass": {
            "status": "PASS", "summary": row["qa_summary"],
            "strengths": qa.get("strengths", []), "findings": qa.get("findings", []),
            "recommended_next_action": qa.get("recommended_next_action", ""),
        },
        "validated_script": script,
        "validated_thumbnails": thumbnails,
        "selected_thumbnail_concept": selected,
        "open_human_items": {
            "creator_inputs_needed": script.get("creator_inputs_needed", []),
            "verification_notes": script.get("verification_notes", []),
        },
        "requirements": {
            "recommended_thumbnail_rank": rank,
            "allowed_script_sections": sections,
            "creator_input_count": len(script.get("creator_inputs_needed", [])),
            "verification_count": len(script.get("verification_notes", [])),
        },
        "rules": [
            "Cover every creator placeholder exactly once in recording_plan.",
            "Carry every verification note into verification_plan without marking it resolved.",
            "Preserve the validated script and recommended thumbnail concept.",
            "Do not generate images, edit video, publish, schedule, upload, or mutate accounts.",
        ],
    }


def write_production_context(context: dict, output_dir: str) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{context['prepared_at'][:10]}-production-input.json"
    path.write_text(json.dumps(context, indent=2), encoding="utf-8")
    return path


def _strings(value, label):
    if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
        raise ValueError(f"{label} must be a list of non-empty strings")
    return [x.strip() for x in value]


def validate_production_payload(payload: dict, context: dict) -> None:
    if not isinstance(payload, dict):
        raise ValueError("Production payload must be a JSON object")
    for key in ("qa_report_id", "script_report_id", "thumbnail_report_id"):
        if payload.get(key) != context.get(key):
            raise ValueError(f"Production {key} does not match input")
    if not str(payload.get("summary", "")).strip():
        raise ValueError("Production summary is required")

    plan = payload.get("recording_plan")
    if not isinstance(plan, list) or len(plan) < 3:
        raise ValueError("recording_plan must contain at least 3 segments")
    orders = [x.get("order") for x in plan if isinstance(x, dict)]
    if orders != list(range(1, len(plan) + 1)):
        raise ValueError("recording_plan orders must be sequential starting at 1")
    covered = []
    allowed = set(context["requirements"]["allowed_script_sections"])
    for item in plan:
        for key in ("segment_name", "script_section", "objective", "capture_notes"):
            if not str(item.get(key, "")).strip():
                raise ValueError(f"Recording segment is missing {key}")
        if item["script_section"] not in allowed:
            raise ValueError(f"Unknown script_section: {item['script_section']}")
        covered += _strings(item.get("creator_inputs", []), "creator_inputs")
        _strings(item.get("b_roll", []), "b_roll")
    if len(covered) != len(set(covered)):
        raise ValueError("Creator placeholders may appear in only one recording segment")
    required = {x["placeholder"].strip() for x in context["open_human_items"]["creator_inputs_needed"]}
    if set(covered) != required:
        raise ValueError("Production creator input coverage does not match QA-passed script")

    checks = payload.get("verification_plan")
    if not isinstance(checks, list):
        raise ValueError("verification_plan must be a list")
    seen = []
    for item in checks:
        if not str(item.get("item", "")).strip() or not str(item.get("action", "")).strip():
            raise ValueError("Each verification_plan item requires item and action")
        if not isinstance(item.get("required_before_recording"), bool):
            raise ValueError("verification required_before_recording must be boolean")
        seen.append(item["item"].strip())
    expected = {x["item"].strip() for x in context["open_human_items"]["verification_notes"]}
    if len(seen) != len(set(seen)) or set(seen) != expected:
        raise ValueError("Production verification coverage does not match QA-passed script")

    handoff = payload.get("thumbnail_handoff")
    selected = context["selected_thumbnail_concept"]
    if not isinstance(handoff, dict):
        raise ValueError("thumbnail_handoff must be a JSON object")
    if handoff.get("recommended_rank") != context["requirements"]["recommended_thumbnail_rank"]:
        raise ValueError("thumbnail_handoff recommended_rank does not match validated concept")
    for key in ("concept_name", "thumbnail_text"):
        if str(handoff.get(key, "")).strip() != str(selected.get(key, "")).strip():
            raise ValueError(f"thumbnail_handoff {key} does not match validated concept")
    handed_assets = set(_strings(handoff.get("creator_assets_needed", []), "thumbnail creator_assets_needed"))
    selected_assets = {x.strip() for x in selected.get("creator_assets_needed", []) if isinstance(x, str) and x.strip()}
    if handed_assets != selected_assets:
        raise ValueError("thumbnail creator assets must exactly match validated concept")
    _strings(handoff.get("capture_during_recording", []), "capture_during_recording")

    assets = payload.get("asset_plan")
    if not isinstance(assets, list):
        raise ValueError("asset_plan must be a list")
    planned = set()
    for item in assets:
        for key in ("asset", "source", "purpose"):
            if not str(item.get(key, "")).strip():
                raise ValueError(f"Asset plan item is missing {key}")
        if not isinstance(item.get("required_before_recording"), bool):
            raise ValueError("Asset required_before_recording must be boolean")
        planned.add(item["asset"].strip())
    if not selected_assets.issubset(planned):
        raise ValueError("asset_plan must include all recommended thumbnail assets")

    notes = payload.get("editing_notes")
    if not isinstance(notes, list) or not notes:
        raise ValueError("editing_notes must contain at least one item")
    for item in notes:
        if not str(item.get("moment", "")).strip() or not str(item.get("direction", "")).strip():
            raise ValueError("Each editing note requires moment and direction")

    checklist = payload.get("pre_recording_checklist")
    if not isinstance(checklist, list) or not checklist:
        raise ValueError("pre_recording_checklist must contain at least one item")
    for item in checklist:
        if not str(item.get("item", "")).strip() or not str(item.get("source", "")).strip():
            raise ValueError("Each checklist item requires item and source")
        if not isinstance(item.get("required"), bool):
            raise ValueError("Checklist required must be boolean")
    _strings(payload.get("risks", []), "risks")
