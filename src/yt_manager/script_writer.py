import json
import re
from datetime import datetime, timezone
from pathlib import Path

from yt_manager.db import connect
from yt_manager.strategy import load_channel_profile


def _now_utc(now: datetime | None = None) -> datetime:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current


def _normalize_title(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def approve_opportunity(
    db_path: str,
    rank: int,
    notes: str = "",
    now: datetime | None = None,
) -> dict:
    if rank <= 0:
        raise ValueError("Opportunity rank must be positive")

    approved_at = _now_utc(now).isoformat()
    with connect(db_path) as conn:
        report = conn.execute(
            """SELECT id, research_run_id
            FROM strategy_reports
            ORDER BY id DESC
            LIMIT 1"""
        ).fetchone()
        if not report:
            raise ValueError("No validated strategy report found")

        opportunity = conn.execute(
            """SELECT working_title
            FROM strategy_opportunities
            WHERE strategy_report_id=? AND rank=?""",
            (report["id"], rank),
        ).fetchone()
        if not opportunity:
            raise ValueError(f"Strategy report has no opportunity at rank {rank}")

        existing = conn.execute(
            """SELECT id FROM script_approvals
            WHERE strategy_report_id=? AND opportunity_rank=?""",
            (report["id"], rank),
        ).fetchone()
        if existing:
            approval_id = int(existing["id"])
            conn.execute(
                "UPDATE script_approvals SET approved_at=?, notes=? WHERE id=?",
                (approved_at, notes.strip(), approval_id),
            )
        else:
            cursor = conn.execute(
                """INSERT INTO script_approvals
                (strategy_report_id, opportunity_rank, approved_at, notes)
                VALUES (?, ?, ?, ?)""",
                (report["id"], rank, approved_at, notes.strip()),
            )
            approval_id = int(cursor.lastrowid)

    return {
        "approval_id": approval_id,
        "strategy_report_id": int(report["id"]),
        "research_run_id": int(report["research_run_id"]),
        "opportunity_rank": rank,
        "working_title": opportunity["working_title"],
        "approved_at": approved_at,
        "notes": notes.strip(),
    }


def build_script_context(
    db_path: str,
    profile_path: str,
    approval_id: int | None = None,
    minimum_words: int = 600,
    now: datetime | None = None,
) -> dict:
    if minimum_words <= 0:
        raise ValueError("minimum_words must be positive")

    current = _now_utc(now)
    profile = load_channel_profile(profile_path)

    with connect(db_path) as conn:
        params: tuple = ()
        where = ""
        if approval_id is not None:
            where = "WHERE sa.id=?"
            params = (approval_id,)

        approval = conn.execute(
            f"""SELECT
                sa.id AS approval_id,
                sa.strategy_report_id,
                sa.opportunity_rank,
                sa.approved_at,
                sa.notes,
                sr.research_run_id,
                sr.summary AS strategy_summary,
                so.working_title,
                so.angle,
                so.why_now,
                so.audience_fit,
                so.confidence,
                so.source_video_ids,
                so.risks
            FROM script_approvals sa
            JOIN strategy_reports sr ON sr.id=sa.strategy_report_id
            JOIN strategy_opportunities so
              ON so.strategy_report_id=sa.strategy_report_id
             AND so.rank=sa.opportunity_rank
            {where}
            ORDER BY sa.id DESC
            LIMIT 1""",
            params,
        ).fetchone()
        if not approval:
            if approval_id is None:
                raise ValueError("No human-approved strategy opportunity found")
            raise ValueError(f"Script approval {approval_id} was not found")

        source_ids = json.loads(approval["source_video_ids"])
        sources = []
        for video_id in source_ids:
            row = conn.execute(
                """SELECT video_id, channel_title, title, published_at, views,
                          baseline_views, outlier_score, url
                FROM candidates
                WHERE run_id=? AND video_id=?""",
                (approval["research_run_id"], video_id),
            ).fetchone()
            if not row:
                raise ValueError(
                    f"Approved opportunity references source video missing from research run: {video_id}"
                )
            sources.append({
                "video_id": row["video_id"],
                "channel_title": row["channel_title"],
                "title": row["title"],
                "published_at": row["published_at"],
                "views": int(row["views"]),
                "baseline_views": float(row["baseline_views"]),
                "raw_outlier": float(row["outlier_score"]),
                "url": row["url"],
            })

    return {
        "version": 1,
        "prepared_at": current.isoformat(),
        "approval": {
            "approval_id": int(approval["approval_id"]),
            "strategy_report_id": int(approval["strategy_report_id"]),
            "research_run_id": int(approval["research_run_id"]),
            "opportunity_rank": int(approval["opportunity_rank"]),
            "approved_at": approval["approved_at"],
            "human_notes": approval["notes"],
        },
        "channel_profile": profile,
        "approved_opportunity": {
            "working_title": approval["working_title"],
            "angle": approval["angle"],
            "why_now": approval["why_now"],
            "audience_fit": approval["audience_fit"],
            "confidence": approval["confidence"],
            "risks": approval["risks"],
            "strategy_summary": approval["strategy_summary"],
            "source_video_ids": source_ids,
        },
        "inspiration_sources": sources,
        "evidence_limits": [
            "Competitor source records contain titles and performance metadata, not transcripts.",
            "Use competitor metrics to justify topic timing or packaging insight only; do not claim knowledge of what a competitor said or demonstrated.",
            "Do not invent product facts, benchmark results, prices, release details, or Joel's first-hand experience.",
            "When the script needs a current fact not present in this input, add it to verification_notes instead of asserting it as settled fact.",
            "When the script needs Joel's personal result, opinion, screenshot, or demo outcome, use an explicit [JOEL: ...] placeholder and list it in creator_inputs_needed.",
        ],
        "script_requirements": {
            "minimum_words": minimum_words,
            "title_options": 3,
            "minimum_body_sections": 3,
            "full_script_required": True,
        },
    }


def write_script_context(context: dict, output_dir: str) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    date = context["prepared_at"][:10]
    path = out / f"{date}-script-input.json"
    path.write_text(json.dumps(context, indent=2), encoding="utf-8")
    return path


def script_word_count(payload: dict) -> int:
    script = payload.get("script", {})
    text_parts = [str(script.get("hook", ""))]
    for section in script.get("sections", []) if isinstance(script.get("sections"), list) else []:
        if isinstance(section, dict):
            text_parts.append(str(section.get("narration", "")))
    text_parts.extend([
        str(script.get("conclusion", "")),
        str(script.get("cta", "")),
    ])
    return len(re.findall(r"\b[\w'-]+\b", "\n".join(text_parts)))


def validate_script_payload(payload: dict, context: dict) -> None:
    if not isinstance(payload, dict):
        raise ValueError("Script payload must be a JSON object")

    approval = context["approval"]
    for field in ("approval_id", "strategy_report_id", "opportunity_rank"):
        if payload.get(field) != approval.get(field):
            raise ValueError(f"Script {field} does not match approved script input")

    working_title = str(payload.get("working_title", "")).strip()
    if not working_title:
        raise ValueError("Script working_title is required")

    title_options = payload.get("title_options")
    expected_titles = int(context["script_requirements"]["title_options"])
    if not isinstance(title_options, list) or len(title_options) != expected_titles:
        raise ValueError(f"Script must contain exactly {expected_titles} title_options")
    cleaned_titles = [str(title).strip() for title in title_options]
    if any(not title for title in cleaned_titles) or len(set(cleaned_titles)) != expected_titles:
        raise ValueError("Script title_options must be non-empty and unique")
    if working_title not in cleaned_titles:
        raise ValueError("working_title must be one of title_options")

    source_titles = {
        _normalize_title(item["title"])
        for item in context.get("inspiration_sources", [])
    }
    for title in cleaned_titles:
        if _normalize_title(title) in source_titles:
            raise ValueError("Script title_options may not copy a competitor source title")

    brief = payload.get("brief")
    if not isinstance(brief, dict):
        raise ValueError("Script brief must be a JSON object")
    for field in ("viewer_problem", "core_promise", "unique_angle", "opening_hook", "cta"):
        if not str(brief.get(field, "")).strip():
            raise ValueError(f"Script brief is missing {field}")
    proof_plan = brief.get("proof_plan")
    if not isinstance(proof_plan, list) or not proof_plan or any(not str(x).strip() for x in proof_plan):
        raise ValueError("Script brief proof_plan must contain at least one item")
    structure = brief.get("structure")
    min_sections = int(context["script_requirements"]["minimum_body_sections"])
    if not isinstance(structure, list) or len(structure) < min_sections:
        raise ValueError(f"Script brief structure must contain at least {min_sections} items")

    script = payload.get("script")
    if not isinstance(script, dict):
        raise ValueError("Script body must be a JSON object")
    for field in ("hook", "conclusion", "cta"):
        if not str(script.get(field, "")).strip():
            raise ValueError(f"Script body is missing {field}")
    sections = script.get("sections")
    if not isinstance(sections, list) or len(sections) < min_sections:
        raise ValueError(f"Script must contain at least {min_sections} body sections")
    for index, section in enumerate(sections, 1):
        if not isinstance(section, dict):
            raise ValueError(f"Script section {index} must be a JSON object")
        if not str(section.get("heading", "")).strip() or not str(section.get("narration", "")).strip():
            raise ValueError(f"Script section {index} requires heading and narration")

    word_count = script_word_count(payload)
    minimum_words = int(context["script_requirements"]["minimum_words"])
    if word_count < minimum_words:
        raise ValueError(
            f"Full script is too short: {word_count} words; minimum is {minimum_words}"
        )

    source_ids = payload.get("inspiration_source_video_ids")
    allowed_source_ids = set(context["approved_opportunity"]["source_video_ids"])
    if not isinstance(source_ids, list) or not source_ids:
        raise ValueError("Script needs at least one inspiration_source_video_id")
    unknown = set(source_ids) - allowed_source_ids
    if unknown:
        raise ValueError(f"Script references unapproved source video IDs: {sorted(unknown)}")

    verification_notes = payload.get("verification_notes")
    if not isinstance(verification_notes, list):
        raise ValueError("verification_notes must be a list")
    for index, note in enumerate(verification_notes, 1):
        if not isinstance(note, dict):
            raise ValueError(f"verification note {index} must be a JSON object")
        if not str(note.get("item", "")).strip() or not str(note.get("reason", "")).strip():
            raise ValueError(f"verification note {index} requires item and reason")

    creator_inputs = payload.get("creator_inputs_needed")
    if not isinstance(creator_inputs, list):
        raise ValueError("creator_inputs_needed must be a list")
    for index, item in enumerate(creator_inputs, 1):
        if not isinstance(item, dict):
            raise ValueError(f"creator input {index} must be a JSON object")
        if not str(item.get("placeholder", "")).strip() or not str(item.get("needed", "")).strip():
            raise ValueError(f"creator input {index} requires placeholder and needed")

    script_text = json.dumps(script)
    if "[JOEL:" in script_text and not creator_inputs:
        raise ValueError("Script contains [JOEL: ...] placeholders but creator_inputs_needed is empty")


def render_script_markdown(payload: dict, context: dict) -> str:
    lines = [
        f"# Video Script - {context['prepared_at'][:10]}",
        "",
        f"Approval: **{context['approval']['approval_id']}** | Strategy report: **{context['approval']['strategy_report_id']}** | Opportunity: **#{context['approval']['opportunity_rank']}**",
        f"Word count: **{script_word_count(payload):,}**",
        "",
        "## Working title",
        "",
        payload["working_title"],
        "",
        "## Title options",
        "",
    ]
    for title in payload["title_options"]:
        lines.append(f"- {title}")

    brief = payload["brief"]
    lines.extend([
        "",
        "## Video brief",
        "",
        f"- Viewer problem: {brief['viewer_problem']}",
        f"- Core promise: {brief['core_promise']}",
        f"- Unique angle: {brief['unique_angle']}",
        f"- Opening hook: {brief['opening_hook']}",
        f"- CTA: {brief['cta']}",
        "- Proof plan:",
    ])
    for item in brief["proof_plan"]:
        lines.append(f"  - {item}")
    lines.append("- Structure:")
    for item in brief["structure"]:
        lines.append(f"  - {item}")

    lines.extend(["", "## Inspiration evidence", ""])
    selected_sources = set(payload["inspiration_source_video_ids"])
    for source in context["inspiration_sources"]:
        if source["video_id"] in selected_sources:
            lines.append(
                f"- {source['channel_title']} — {source['title']} — "
                f"{source['raw_outlier']:.2f}x — {source['views']:,} views — {source['url']}"
            )
    lines.extend([
        "",
        "> These competitor records are topic/packaging evidence only. They are not transcript or factual sources for the script.",
        "",
        "## Creator inputs needed",
        "",
    ])
    if payload["creator_inputs_needed"]:
        for item in payload["creator_inputs_needed"]:
            lines.append(f"- `{item['placeholder']}` — {item['needed']}")
    else:
        lines.append("None identified.")

    lines.extend(["", "## Verify before recording", ""])
    if payload["verification_notes"]:
        for note in payload["verification_notes"]:
            lines.append(f"- **{note['item']}** — {note['reason']}")
    else:
        lines.append("No unresolved factual checks identified by the Script Writer.")

    script = payload["script"]
    lines.extend([
        "",
        "## Full script",
        "",
        "### Hook",
        "",
        script["hook"],
        "",
    ])
    for section in script["sections"]:
        lines.extend([
            f"### {section['heading']}",
            "",
            section["narration"],
            "",
        ])
    lines.extend([
        "### Conclusion",
        "",
        script["conclusion"],
        "",
        "### CTA",
        "",
        script["cta"],
        "",
    ])
    return "\n".join(lines)


def persist_script(payload: dict, context: dict, db_path: str) -> int:
    validate_script_payload(payload, context)
    created_at = datetime.now(timezone.utc).isoformat()
    raw_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    word_count = script_word_count(payload)
    approval_id = int(context["approval"]["approval_id"])

    with connect(db_path) as conn:
        existing = conn.execute(
            "SELECT id FROM script_reports WHERE approval_id=?",
            (approval_id,),
        ).fetchone()
        if existing:
            conn.execute("DELETE FROM script_reports WHERE id=?", (existing["id"],))

        cursor = conn.execute(
            """INSERT INTO script_reports
            (approval_id, created_at, working_title, word_count, raw_json)
            VALUES (?, ?, ?, ?, ?)""",
            (
                approval_id,
                created_at,
                payload["working_title"].strip(),
                word_count,
                raw_json,
            ),
        )
        return int(cursor.lastrowid)
