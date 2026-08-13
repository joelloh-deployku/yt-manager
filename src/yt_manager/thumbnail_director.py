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


def _normalize_text(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def _text_word_count(value: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", value))


def build_thumbnail_context(
    db_path: str,
    profile_path: str,
    script_report_id: int | None = None,
    concept_count: int = 3,
    max_text_words: int = 5,
    now: datetime | None = None,
) -> dict:
    if concept_count <= 0:
        raise ValueError("concept_count must be positive")
    if max_text_words < 0:
        raise ValueError("max_text_words may not be negative")

    current = _now_utc(now)
    profile = load_channel_profile(profile_path)

    with connect(db_path) as conn:
        params: tuple = ()
        where = ""
        if script_report_id is not None:
            where = "WHERE scr.id=?"
            params = (script_report_id,)

        row = conn.execute(
            f"""SELECT
                scr.id AS script_report_id,
                scr.approval_id,
                scr.created_at AS script_created_at,
                scr.working_title,
                scr.word_count,
                scr.raw_json AS script_raw_json,
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
            FROM script_reports scr
            JOIN script_approvals sa ON sa.id=scr.approval_id
            JOIN strategy_reports sr ON sr.id=sa.strategy_report_id
            JOIN strategy_opportunities so
              ON so.strategy_report_id=sa.strategy_report_id
             AND so.rank=sa.opportunity_rank
            {where}
            ORDER BY scr.id DESC
            LIMIT 1""",
            params,
        ).fetchone()
        if not row:
            if script_report_id is None:
                raise ValueError("No validated Script Writer report found")
            raise ValueError(f"Script report {script_report_id} was not found")

        script_payload = json.loads(row["script_raw_json"])
        source_ids = script_payload.get("inspiration_source_video_ids", [])
        if not isinstance(source_ids, list) or not source_ids:
            raise ValueError("Validated script has no inspiration source video IDs")

        sources = []
        for video_id in source_ids:
            source = conn.execute(
                """SELECT video_id, channel_title, title, published_at, views,
                          baseline_views, outlier_score, url
                FROM candidates
                WHERE run_id=? AND video_id=?""",
                (row["research_run_id"], video_id),
            ).fetchone()
            if not source:
                raise ValueError(
                    f"Validated script references source video missing from research run: {video_id}"
                )
            sources.append({
                "video_id": source["video_id"],
                "channel_title": source["channel_title"],
                "title": source["title"],
                "published_at": source["published_at"],
                "views": int(source["views"]),
                "baseline_views": float(source["baseline_views"]),
                "raw_outlier": float(source["outlier_score"]),
                "url": source["url"],
            })

    brief = script_payload.get("brief", {})
    script_body = script_payload.get("script", {})
    return {
        "version": 1,
        "prepared_at": current.isoformat(),
        "script_report_id": int(row["script_report_id"]),
        "approval": {
            "approval_id": int(row["approval_id"]),
            "strategy_report_id": int(row["strategy_report_id"]),
            "research_run_id": int(row["research_run_id"]),
            "opportunity_rank": int(row["opportunity_rank"]),
            "human_notes": row["human_notes"],
        },
        "channel_profile": profile,
        "approved_strategy": {
            "angle": row["angle"],
            "why_now": row["why_now"],
            "audience_fit": row["audience_fit"],
            "confidence": row["confidence"],
            "risks": row["strategy_risks"],
            "source_video_ids": json.loads(row["source_video_ids"]),
        },
        "validated_script": {
            "working_title": script_payload.get("working_title", row["working_title"]),
            "title_options": script_payload.get("title_options", []),
            "word_count": int(row["word_count"]),
            "brief": brief,
            "hook": script_body.get("hook", ""),
            "conclusion": script_body.get("conclusion", ""),
            "creator_inputs_needed": script_payload.get("creator_inputs_needed", []),
            "verification_notes": script_payload.get("verification_notes", []),
            "inspiration_source_video_ids": source_ids,
        },
        "inspiration_sources": sources,
        "evidence_limits": [
            "Competitor records contain titles and performance metadata only; there are no competitor thumbnail images in this context.",
            "Do not infer or imitate a competitor's thumbnail composition, facial expression, colors, objects, or text from a video title.",
            "Use competitor performance only as evidence that the topic or packaging territory may be interesting.",
            "Do not invent Joel assets. If a concept needs Joel's face, a screenshot, product UI, terminal output, diagram, or other real asset, list it in creator_assets_needed.",
            "Thumbnail concepts are creative directions only. They do not authorize image generation, publishing, or account mutation.",
        ],
        "thumbnail_requirements": {
            "concept_count": concept_count,
            "max_text_words": max_text_words,
            "recommended_concept_required": True,
            "render_prompt_required": True,
        },
    }


def write_thumbnail_context(context: dict, output_dir: str) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    date = context["prepared_at"][:10]
    path = out / f"{date}-thumbnail-input.json"
    path.write_text(json.dumps(context, indent=2), encoding="utf-8")
    return path


def validate_thumbnail_payload(payload: dict, context: dict) -> None:
    if not isinstance(payload, dict):
        raise ValueError("Thumbnail payload must be a JSON object")
    if payload.get("script_report_id") != context.get("script_report_id"):
        raise ValueError("Thumbnail script_report_id does not match thumbnail input")

    summary = str(payload.get("summary", "")).strip()
    if not summary:
        raise ValueError("Thumbnail summary is required")

    concepts = payload.get("concepts")
    expected_count = int(context["thumbnail_requirements"]["concept_count"])
    if not isinstance(concepts, list) or len(concepts) != expected_count:
        raise ValueError(f"Thumbnail payload must contain exactly {expected_count} concepts")

    expected_ranks = list(range(1, expected_count + 1))
    ranks = [item.get("rank") for item in concepts if isinstance(item, dict)]
    if len(ranks) != expected_count or any(not isinstance(rank, int) for rank in ranks):
        raise ValueError("Every thumbnail concept requires an integer rank")
    if sorted(ranks) != expected_ranks:
        raise ValueError(f"Thumbnail concept ranks must be exactly {expected_ranks}")

    recommended_rank = payload.get("recommended_rank")
    if not isinstance(recommended_rank, int) or recommended_rank not in expected_ranks:
        raise ValueError(f"recommended_rank must be one of {expected_ranks}")

    allowed_source_ids = set(context["validated_script"]["inspiration_source_video_ids"])
    source_titles = {
        _normalize_text(source["title"])
        for source in context.get("inspiration_sources", [])
    }
    working_title = _normalize_text(context["validated_script"]["working_title"])
    max_text_words = int(context["thumbnail_requirements"]["max_text_words"])

    concept_names = []
    visual_hooks = []
    for item in concepts:
        if not isinstance(item, dict):
            raise ValueError("Each thumbnail concept must be a JSON object")

        for field in (
            "concept_name",
            "visual_hook",
            "composition",
            "title_alignment",
            "emotional_tone",
            "rationale",
            "render_prompt",
            "risks",
        ):
            if not str(item.get(field, "")).strip():
                raise ValueError(f"Thumbnail concept {item.get('rank')} is missing {field}")

        thumbnail_text = item.get("thumbnail_text")
        if not isinstance(thumbnail_text, str):
            raise ValueError(f"Thumbnail concept {item.get('rank')} thumbnail_text must be a string")
        if _text_word_count(thumbnail_text) > max_text_words:
            raise ValueError(
                f"Thumbnail concept {item.get('rank')} text exceeds {max_text_words} words"
            )
        normalized_text = _normalize_text(thumbnail_text)
        if normalized_text and normalized_text in source_titles:
            raise ValueError("Thumbnail text may not copy a competitor source title")
        if normalized_text and normalized_text == working_title:
            raise ValueError("Thumbnail text should complement the video title, not repeat it")

        creator_assets = item.get("creator_assets_needed")
        if not isinstance(creator_assets, list):
            raise ValueError(
                f"Thumbnail concept {item.get('rank')} creator_assets_needed must be a list"
            )
        if any(not isinstance(asset, str) or not asset.strip() for asset in creator_assets):
            raise ValueError(
                f"Thumbnail concept {item.get('rank')} has an invalid creator asset"
            )

        source_ids = item.get("source_video_ids")
        if not isinstance(source_ids, list) or not source_ids:
            raise ValueError(
                f"Thumbnail concept {item.get('rank')} needs at least one source_video_id"
            )
        if any(not isinstance(video_id, str) or not video_id.strip() for video_id in source_ids):
            raise ValueError(
                f"Thumbnail concept {item.get('rank')} has an invalid source_video_id"
            )
        unknown = set(source_ids) - allowed_source_ids
        if unknown:
            raise ValueError(
                f"Thumbnail concept {item.get('rank')} references unapproved source video IDs: {sorted(unknown)}"
            )

        concept_names.append(_normalize_text(item["concept_name"]))
        visual_hooks.append(_normalize_text(item["visual_hook"]))

    if len(set(concept_names)) != expected_count:
        raise ValueError("Thumbnail concepts must have distinct concept names")
    if len(set(visual_hooks)) != expected_count:
        raise ValueError("Thumbnail concepts must use distinct visual hooks")


def render_thumbnail_markdown(payload: dict, context: dict) -> str:
    sources_by_id = {
        source["video_id"]: source
        for source in context.get("inspiration_sources", [])
    }
    lines = [
        f"# Thumbnail Direction - {context['prepared_at'][:10]}",
        "",
        f"Script report: **{context['script_report_id']}**",
        f"Video title: **{context['validated_script']['working_title']}**",
        f"Recommended concept: **#{payload['recommended_rank']}**",
        "",
        "## Direction summary",
        "",
        payload["summary"].strip(),
        "",
    ]

    for item in sorted(payload["concepts"], key=lambda x: x["rank"]):
        recommended = " — **RECOMMENDED**" if item["rank"] == payload["recommended_rank"] else ""
        text = item["thumbnail_text"].strip() or "(no text)"
        lines.extend([
            f"## {item['rank']}. {item['concept_name']}{recommended}",
            "",
            f"- Thumbnail text: **{text}**",
            f"- Visual hook: {item['visual_hook']}",
            f"- Composition: {item['composition']}",
            f"- Title alignment: {item['title_alignment']}",
            f"- Emotional tone: {item['emotional_tone']}",
            f"- Rationale: {item['rationale']}",
            f"- Risks / caveats: {item['risks']}",
            "- Creator assets needed:",
        ])
        if item["creator_assets_needed"]:
            for asset in item["creator_assets_needed"]:
                lines.append(f"  - {asset}")
        else:
            lines.append("  - None identified")

        lines.append("- Inspiration evidence:")
        for video_id in item["source_video_ids"]:
            source = sources_by_id[video_id]
            lines.append(
                f"  - {source['channel_title']} — {source['title']} — "
                f"{source['raw_outlier']:.2f}x — {source['url']}"
            )
        lines.extend([
            "",
            "### Render prompt",
            "",
            item["render_prompt"].strip(),
            "",
        ])

    lines.extend([
        "> Competitor evidence above is topic/performance evidence only. No competitor thumbnail images were supplied or imitated.",
        "",
        "> These are creative directions only. Image generation and publishing still require separate human action.",
        "",
    ])
    return "\n".join(lines)


def persist_thumbnail(payload: dict, context: dict, db_path: str) -> int:
    validate_thumbnail_payload(payload, context)
    created_at = datetime.now(timezone.utc).isoformat()
    raw_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)

    with connect(db_path) as conn:
        existing = conn.execute(
            "SELECT id FROM thumbnail_reports WHERE script_report_id=?",
            (context["script_report_id"],),
        ).fetchone()
        if existing:
            conn.execute("DELETE FROM thumbnail_reports WHERE id=?", (existing["id"],))

        cursor = conn.execute(
            """INSERT INTO thumbnail_reports
            (script_report_id, created_at, recommended_rank, summary, raw_json)
            VALUES (?, ?, ?, ?, ?)""",
            (
                context["script_report_id"],
                created_at,
                payload["recommended_rank"],
                payload["summary"].strip(),
                raw_json,
            ),
        )
        report_id = int(cursor.lastrowid)

        for item in sorted(payload["concepts"], key=lambda x: x["rank"]):
            conn.execute(
                """INSERT INTO thumbnail_concepts
                (thumbnail_report_id, rank, concept_name, thumbnail_text, visual_hook,
                 composition, title_alignment, emotional_tone, rationale, render_prompt,
                 creator_assets_needed, source_video_ids, risks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    report_id,
                    item["rank"],
                    item["concept_name"].strip(),
                    item["thumbnail_text"].strip(),
                    item["visual_hook"].strip(),
                    item["composition"].strip(),
                    item["title_alignment"].strip(),
                    item["emotional_tone"].strip(),
                    item["rationale"].strip(),
                    item["render_prompt"].strip(),
                    json.dumps(item["creator_assets_needed"]),
                    json.dumps(item["source_video_ids"]),
                    item["risks"].strip(),
                ),
            )

    return report_id
