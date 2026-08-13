"""Rendering and persistence for Milestone 6 production handoffs."""

import json
from datetime import datetime, timezone

from yt_manager.db import connect
from yt_manager.production import ensure_production_schema, validate_production_payload


def render_production_markdown(payload: dict, context: dict) -> str:
    title = context["validated_script"].get("working_title", "")
    lines = [
        f"# Production Handoff - {context['prepared_at'][:10]}",
        "",
        f"QA report: **{context['qa_report_id']} — PASS**",
        f"Script report: **{context['script_report_id']}**",
        f"Thumbnail report: **{context['thumbnail_report_id']}**",
        f"Working title: **{title}**",
        "",
        "## Summary",
        "",
        payload["summary"].strip(),
        "",
        "## Recording plan",
        "",
    ]
    for item in payload["recording_plan"]:
        lines += [
            f"### {item['order']}. {item['segment_name']}", "",
            f"- Script section: {item['script_section']}",
            f"- Objective: {item['objective']}",
            f"- Capture notes: {item['capture_notes']}",
            "- Creator inputs:",
        ]
        lines += [f"  - `{x}`" for x in item["creator_inputs"]] or ["  - None"]
        lines.append("- B-roll / supporting capture:")
        lines += [f"  - {x}" for x in item["b_roll"]] or ["  - None"]
        lines.append("")

    lines += ["## Verification before recording", ""]
    lines += [
        f"- **{x['item']}** — {x['action']} — "
        f"{'required before recording' if x['required_before_recording'] else 'can remain open until later'}"
        for x in payload["verification_plan"]
    ] or ["None."]

    thumb = payload["thumbnail_handoff"]
    lines += [
        "", "## Thumbnail handoff", "",
        f"- Recommended concept: **#{thumb['recommended_rank']} — {thumb['concept_name']}**",
        f"- Thumbnail text: **{thumb['thumbnail_text'] or '(no text)'}**",
        "- Creator assets needed:",
    ]
    lines += [f"  - {x}" for x in thumb["creator_assets_needed"]] or ["  - None"]
    lines.append("- Capture during recording:")
    lines += [f"  - {x}" for x in thumb["capture_during_recording"]] or ["  - None"]

    lines += ["", "## Asset plan", ""]
    lines += [
        f"- **{x['asset']}** — {x['purpose']} — source: {x['source']} — "
        f"{'required before recording' if x['required_before_recording'] else 'can be captured later'}"
        for x in payload["asset_plan"]
    ] or ["None."]

    lines += ["", "## Editing notes", ""]
    lines += [f"- **{x['moment']}** — {x['direction']}" for x in payload["editing_notes"]]

    lines += ["", "## Pre-recording checklist", ""]
    for item in payload["pre_recording_checklist"]:
        label = "[ ]" if item["required"] else "[ ] optional"
        lines.append(f"- {label} {item['item']} — source: {item['source']}")

    lines += ["", "## QA findings carried forward", ""]
    findings = context["qa_pass"]["findings"]
    if findings:
        for item in findings:
            lines.append(
                f"- **{item.get('finding_key', 'QA')} — {str(item.get('severity', '')).upper()}** — "
                f"{item.get('finding', '')} — action: {item.get('recommended_action', '')}"
            )
    else:
        lines.append("No QA defects were carried forward.")

    lines += ["", "## Risks", ""]
    lines += [f"- {x}" for x in payload["risks"]] or ["None identified."]
    lines += [
        "",
        "> This handoff organizes a QA-passed package for human recording and editing. It does not authorize image generation, editing automation, upload, scheduling, publishing, or account mutation.",
        "",
    ]
    return "\n".join(lines)


def persist_production(payload: dict, context: dict, db_path: str) -> int:
    ensure_production_schema(db_path)
    validate_production_payload(payload, context)
    created_at = datetime.now(timezone.utc).isoformat()
    raw_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    with connect(db_path) as conn:
        existing = conn.execute(
            "SELECT id FROM production_reports WHERE qa_report_id=?",
            (context["qa_report_id"],),
        ).fetchone()
        if existing:
            conn.execute("DELETE FROM production_reports WHERE id=?", (existing["id"],))
        cursor = conn.execute(
            "INSERT INTO production_reports(qa_report_id, created_at, summary, raw_json) VALUES (?, ?, ?, ?)",
            (context["qa_report_id"], created_at, payload["summary"].strip(), raw_json),
        )
        report_id = int(cursor.lastrowid)

        groups = [
            ("RECORDING", payload["recording_plan"], "segment_name", None),
            ("VERIFICATION", payload["verification_plan"], "item", "required_before_recording"),
            ("ASSET", payload["asset_plan"], "asset", "required_before_recording"),
            ("EDITING", payload["editing_notes"], "moment", None),
            ("CHECKLIST", payload["pre_recording_checklist"], "item", "required"),
        ]
        for item_type, items, label_key, required_key in groups:
            for sort_order, item in enumerate(items, 1):
                conn.execute(
                    """INSERT INTO production_items
                    (production_report_id, item_type, sort_order, label, required_before_recording, raw_json)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        report_id, item_type, sort_order, str(item.get(label_key, "")).strip(),
                        1 if required_key and item.get(required_key) else 0,
                        json.dumps(item, separators=(",", ":"), sort_keys=True),
                    ),
                )
    return report_id
