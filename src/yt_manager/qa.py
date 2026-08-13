"""Deterministic context, validation, persistence, and rendering for content QA."""

import json
from datetime import datetime, timezone
from pathlib import Path

from yt_manager.db import connect


QA_STATUSES = {"PASS", "NEEDS_CHANGES"}
QA_SEVERITIES = {"BLOCKER", "HIGH", "MEDIUM", "LOW"}
QA_AREAS = {
    "SCRIPT",
    "THUMBNAIL",
    "ALIGNMENT",
    "EVIDENCE",
    "CREATOR_INPUT",
    "FACT_CHECK",
    "WORKFLOW",
}

QA_SCHEMA = """
CREATE TABLE IF NOT EXISTS qa_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thumbnail_report_id INTEGER NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL,
    summary TEXT NOT NULL,
    raw_json TEXT NOT NULL,
    FOREIGN KEY(thumbnail_report_id) REFERENCES thumbnail_reports(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS qa_findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    qa_report_id INTEGER NOT NULL,
    finding_key TEXT NOT NULL,
    severity TEXT NOT NULL,
    area TEXT NOT NULL,
    finding TEXT NOT NULL,
    evidence TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    blocks_next_step INTEGER NOT NULL,
    UNIQUE(qa_report_id, finding_key),
    FOREIGN KEY(qa_report_id) REFERENCES qa_reports(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_qa_findings_report_severity
ON qa_findings(qa_report_id, severity);
"""


def _now_utc(now: datetime | None = None) -> datetime:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current


def ensure_qa_schema(db_path: str) -> None:
    with connect(db_path) as conn:
        conn.executescript(QA_SCHEMA)


def build_qa_context(
    db_path: str,
    thumbnail_report_id: int | None = None,
    now: datetime | None = None,
) -> dict:
    ensure_qa_schema(db_path)
    current = _now_utc(now)

    with connect(db_path) as conn:
        params: tuple = ()
        where = ""
        if thumbnail_report_id is not None:
            where = "WHERE tr.id=?"
            params = (thumbnail_report_id,)

        row = conn.execute(
            f"""SELECT
                tr.id AS thumbnail_report_id,
                tr.recommended_rank,
                tr.summary AS thumbnail_summary,
                tr.raw_json AS thumbnail_raw_json,
                scr.id AS script_report_id,
                scr.working_title,
                scr.word_count,
                scr.raw_json AS script_raw_json,
                sa.id AS approval_id,
                sa.strategy_report_id,
                sa.opportunity_rank,
                sa.notes AS human_notes,
                sr.research_run_id,
                so.angle,
                so.why_now,
                so.audience_fit,
                so.confidence,
                so.risks AS strategy_risks,
                so.source_video_ids
            FROM thumbnail_reports tr
            JOIN script_reports scr ON scr.id=tr.script_report_id
            JOIN script_approvals sa ON sa.id=scr.approval_id
            JOIN strategy_reports sr ON sr.id=sa.strategy_report_id
            JOIN strategy_opportunities so
              ON so.strategy_report_id=sa.strategy_report_id
             AND so.rank=sa.opportunity_rank
            {where}
            ORDER BY tr.id DESC
            LIMIT 1""",
            params,
        ).fetchone()
        if not row:
            if thumbnail_report_id is None:
                raise ValueError("No validated Thumbnail Director report found")
            raise ValueError(f"Thumbnail report {thumbnail_report_id} was not found")

    script_payload = json.loads(row["script_raw_json"])
    thumbnail_payload = json.loads(row["thumbnail_raw_json"])
    creator_inputs = script_payload.get("creator_inputs_needed", [])
    verification_notes = script_payload.get("verification_notes", [])
    concepts = thumbnail_payload.get("concepts", [])

    return {
        "version": 1,
        "prepared_at": current.isoformat(),
        "thumbnail_report_id": int(row["thumbnail_report_id"]),
        "script_report_id": int(row["script_report_id"]),
        "approval": {
            "approval_id": int(row["approval_id"]),
            "strategy_report_id": int(row["strategy_report_id"]),
            "research_run_id": int(row["research_run_id"]),
            "opportunity_rank": int(row["opportunity_rank"]),
            "human_notes": row["human_notes"],
        },
        "approved_strategy": {
            "angle": row["angle"],
            "why_now": row["why_now"],
            "audience_fit": row["audience_fit"],
            "confidence": row["confidence"],
            "risks": row["strategy_risks"],
            "source_video_ids": json.loads(row["source_video_ids"]),
        },
        "validated_script": script_payload,
        "validated_thumbnails": thumbnail_payload,
        "deterministic_checks": {
            "script_word_count": int(row["word_count"]),
            "thumbnail_concept_count": len(concepts),
            "recommended_thumbnail_rank": int(row["recommended_rank"]),
            "creator_inputs_needed_count": len(creator_inputs),
            "verification_notes_count": len(verification_notes),
        },
        "open_human_items": {
            "creator_inputs_needed": creator_inputs,
            "verification_notes": verification_notes,
        },
        "qa_rules": [
            "Review the validated script and thumbnail concepts as one package; do not rewrite them in the QA response.",
            "PASS means the generated package is coherent enough for Joel's next human production step. PASS is not publishing approval.",
            "Explicit [JOEL: ...] creator placeholders and verification_notes are expected open human tasks and are not automatic QA failures when they are clearly surfaced.",
            "Use NEEDS_CHANGES for real generated-package defects such as unsupported claims not flagged for verification, missing creator dependencies, contradictory hooks, weak title/thumbnail alignment, copied packaging, or workflow integrity problems.",
            "A BLOCKER or HIGH finding, or any finding with blocks_next_step=true, requires NEEDS_CHANGES.",
            "Do not invent factual problems or claim to have inspected assets that are not present in the input.",
            "QA may recommend edits, but it must not modify script, thumbnail, publishing, or account state.",
        ],
    }


def write_qa_context(context: dict, output_dir: str) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    date = context["prepared_at"][:10]
    path = out / f"{date}-qa-input.json"
    path.write_text(json.dumps(context, indent=2), encoding="utf-8")
    return path


def validate_qa_payload(payload: dict, context: dict) -> None:
    if not isinstance(payload, dict):
        raise ValueError("QA payload must be a JSON object")
    if payload.get("thumbnail_report_id") != context.get("thumbnail_report_id"):
        raise ValueError("QA thumbnail_report_id does not match QA input")
    if payload.get("script_report_id") != context.get("script_report_id"):
        raise ValueError("QA script_report_id does not match QA input")

    status = str(payload.get("status", "")).upper()
    if status not in QA_STATUSES:
        raise ValueError("QA status must be PASS or NEEDS_CHANGES")
    if not str(payload.get("summary", "")).strip():
        raise ValueError("QA summary is required")
    if not str(payload.get("recommended_next_action", "")).strip():
        raise ValueError("QA recommended_next_action is required")

    strengths = payload.get("strengths")
    if not isinstance(strengths, list) or not strengths:
        raise ValueError("QA strengths must contain at least one item")
    if any(not isinstance(item, str) or not item.strip() for item in strengths):
        raise ValueError("QA strengths must contain non-empty strings")

    findings = payload.get("findings")
    if not isinstance(findings, list):
        raise ValueError("QA findings must be a list")

    keys = set()
    has_blocking = False
    for index, item in enumerate(findings, 1):
        if not isinstance(item, dict):
            raise ValueError(f"QA finding {index} must be a JSON object")
        finding_key = str(item.get("finding_key", "")).strip()
        if not finding_key:
            raise ValueError(f"QA finding {index} requires finding_key")
        if finding_key in keys:
            raise ValueError("QA finding_key values must be unique")
        keys.add(finding_key)

        severity = str(item.get("severity", "")).upper()
        if severity not in QA_SEVERITIES:
            raise ValueError(
                f"QA finding {finding_key} severity must be BLOCKER, HIGH, MEDIUM, or LOW"
            )
        area = str(item.get("area", "")).upper()
        if area not in QA_AREAS:
            raise ValueError(f"QA finding {finding_key} has invalid area")
        for field in ("finding", "evidence", "recommended_action"):
            if not str(item.get(field, "")).strip():
                raise ValueError(f"QA finding {finding_key} is missing {field}")
        if not isinstance(item.get("blocks_next_step"), bool):
            raise ValueError(f"QA finding {finding_key} blocks_next_step must be boolean")

        if severity in {"BLOCKER", "HIGH"} or item["blocks_next_step"]:
            has_blocking = True

    if status == "PASS" and has_blocking:
        raise ValueError("QA cannot PASS while blocking or HIGH/BLOCKER findings exist")
    if status == "NEEDS_CHANGES" and not has_blocking:
        raise ValueError("QA NEEDS_CHANGES requires at least one blocking or HIGH/BLOCKER finding")


def render_qa_markdown(payload: dict, context: dict) -> str:
    lines = [
        f"# Content QA - {context['prepared_at'][:10]}",
        "",
        f"Status: **{str(payload['status']).upper()}**",
        f"Script report: **{context['script_report_id']}**",
        f"Thumbnail report: **{context['thumbnail_report_id']}**",
        "",
        "## Summary",
        "",
        payload["summary"].strip(),
        "",
        "## Strengths",
        "",
    ]
    for strength in payload["strengths"]:
        lines.append(f"- {strength}")

    lines.extend(["", "## QA findings", ""])
    if payload["findings"]:
        for item in payload["findings"]:
            blocked = "yes" if item["blocks_next_step"] else "no"
            lines.extend([
                f"### {item['finding_key']} — {str(item['severity']).upper()} — {str(item['area']).upper()}",
                "",
                f"- Finding: {item['finding']}",
                f"- Evidence: {item['evidence']}",
                f"- Recommended action: {item['recommended_action']}",
                f"- Blocks next step: **{blocked}**",
                "",
            ])
    else:
        lines.append("No QA defects identified.")

    open_items = context["open_human_items"]
    lines.extend(["", "## Open creator inputs", ""])
    if open_items["creator_inputs_needed"]:
        for item in open_items["creator_inputs_needed"]:
            placeholder = item.get("placeholder", "[JOEL]") if isinstance(item, dict) else "[JOEL]"
            needed = item.get("needed", str(item)) if isinstance(item, dict) else str(item)
            lines.append(f"- `{placeholder}` — {needed}")
    else:
        lines.append("None.")

    lines.extend(["", "## Verify before recording", ""])
    if open_items["verification_notes"]:
        for item in open_items["verification_notes"]:
            if isinstance(item, dict):
                lines.append(f"- **{item.get('item', 'Verification item')}** — {item.get('reason', '')}")
            else:
                lines.append(f"- {item}")
    else:
        lines.append("None.")

    lines.extend([
        "",
        "## Recommended next action",
        "",
        payload["recommended_next_action"].strip(),
        "",
        "> QA status is a production-readiness signal only. It is not publishing approval and does not authorize account mutation.",
        "",
    ])
    return "\n".join(lines)


def persist_qa(payload: dict, context: dict, db_path: str) -> int:
    ensure_qa_schema(db_path)
    validate_qa_payload(payload, context)
    created_at = datetime.now(timezone.utc).isoformat()
    raw_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)

    with connect(db_path) as conn:
        existing = conn.execute(
            "SELECT id FROM qa_reports WHERE thumbnail_report_id=?",
            (context["thumbnail_report_id"],),
        ).fetchone()
        if existing:
            conn.execute("DELETE FROM qa_reports WHERE id=?", (existing["id"],))

        cursor = conn.execute(
            """INSERT INTO qa_reports
            (thumbnail_report_id, created_at, status, summary, raw_json)
            VALUES (?, ?, ?, ?, ?)""",
            (
                context["thumbnail_report_id"],
                created_at,
                str(payload["status"]).upper(),
                payload["summary"].strip(),
                raw_json,
            ),
        )
        report_id = int(cursor.lastrowid)

        for item in payload["findings"]:
            conn.execute(
                """INSERT INTO qa_findings
                (qa_report_id, finding_key, severity, area, finding, evidence,
                 recommended_action, blocks_next_step)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    report_id,
                    item["finding_key"].strip(),
                    str(item["severity"]).upper(),
                    str(item["area"]).upper(),
                    item["finding"].strip(),
                    item["evidence"].strip(),
                    item["recommended_action"].strip(),
                    1 if item["blocks_next_step"] else 0,
                ),
            )

    return report_id
