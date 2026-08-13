import json
from datetime import datetime, timezone
from pathlib import Path

from yt_manager.db import connect
from yt_manager.scoring import classify_outlier


CONFIDENCE_LEVELS = {"HIGH", "MEDIUM", "LOW"}


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def load_channel_profile(path: str) -> dict:
    profile_path = Path(path)
    if not profile_path.exists():
        raise FileNotFoundError(f"Channel profile not found: {profile_path}")
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    if not isinstance(profile, dict):
        raise ValueError("Channel profile must be a JSON object")
    return profile


def build_strategy_context(
    db_path: str,
    profile_path: str,
    now: datetime | None = None,
) -> dict:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)

    profile = load_channel_profile(profile_path)
    with connect(db_path) as conn:
        run = conn.execute(
            """SELECT id, started_at, completed_at, candidate_count
            FROM runs
            WHERE status='completed'
            ORDER BY id DESC
            LIMIT 1"""
        ).fetchone()
        if not run:
            raise ValueError("No completed research run found")

        rows = conn.execute(
            """SELECT video_id, channel_id, channel_title, title, published_at,
                      views, baseline_views, outlier_score, url
            FROM candidates
            WHERE run_id=?
            ORDER BY outlier_score DESC""",
            (run["id"],),
        ).fetchall()
        if not rows:
            raise ValueError("Latest completed research run has no candidates")

        candidates = []
        for row in rows:
            published = _parse_timestamp(row["published_at"])
            age_hours = round(max((current - published).total_seconds() / 3600, 0), 1)

            current_snapshot = conn.execute(
                """SELECT observed_at, views
                FROM video_snapshots
                WHERE run_id=? AND video_id=?
                ORDER BY observed_at DESC
                LIMIT 1""",
                (run["id"], row["video_id"]),
            ).fetchone()
            previous_snapshot = None
            if current_snapshot:
                previous_snapshot = conn.execute(
                    """SELECT observed_at, views
                    FROM video_snapshots
                    WHERE video_id=? AND observed_at<?
                    ORDER BY observed_at DESC
                    LIMIT 1""",
                    (row["video_id"], current_snapshot["observed_at"]),
                ).fetchone()

            view_delta = None
            velocity_views_per_hour = None
            if current_snapshot and previous_snapshot:
                current_time = _parse_timestamp(current_snapshot["observed_at"])
                previous_time = _parse_timestamp(previous_snapshot["observed_at"])
                elapsed_hours = (current_time - previous_time).total_seconds() / 3600
                if elapsed_hours > 0:
                    view_delta = int(current_snapshot["views"]) - int(previous_snapshot["views"])
                    velocity_views_per_hour = round(view_delta / elapsed_hours, 2)

            candidates.append({
                "video_id": row["video_id"],
                "channel_id": row["channel_id"],
                "channel_title": row["channel_title"],
                "title": row["title"],
                "published_at": row["published_at"],
                "age_hours": age_hours,
                "provisional_under_48h": age_hours < 48,
                "views": int(row["views"]),
                "baseline_views": float(row["baseline_views"]),
                "raw_outlier": float(row["outlier_score"]),
                "performance_tier": classify_outlier(float(row["outlier_score"])),
                "view_delta_since_previous_snapshot": view_delta,
                "velocity_views_per_hour": velocity_views_per_hour,
                "url": row["url"],
            })

    return {
        "version": 1,
        "prepared_at": current.isoformat(),
        "research_run_id": int(run["id"]),
        "research_completed_at": run["completed_at"],
        "candidate_count": len(candidates),
        "channel_profile": profile,
        "decision_notes": [
            "Performance tier is evidence, not the final recommendation.",
            "Treat uploads under 48 hours old as provisional; prefer velocity when available.",
            "A relevant underperformer may still inspire an opportunity, but explain the weak performance signal.",
            "Do not copy competitor titles or claims; derive an original angle for this channel.",
        ],
        "candidates": candidates,
    }


def write_strategy_context(context: dict, output_dir: str) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    prepared = _parse_timestamp(context["prepared_at"])
    path = out / f"{prepared.date().isoformat()}-strategist-input.json"
    path.write_text(json.dumps(context, indent=2), encoding="utf-8")
    return path


def validate_strategy_payload(payload: dict, context: dict) -> None:
    if not isinstance(payload, dict):
        raise ValueError("Strategy payload must be a JSON object")
    if payload.get("research_run_id") != context.get("research_run_id"):
        raise ValueError("Strategy research_run_id does not match strategist input")

    summary = str(payload.get("summary", "")).strip()
    if not summary:
        raise ValueError("Strategy summary is required")

    opportunities = payload.get("opportunities")
    if not isinstance(opportunities, list):
        raise ValueError("Strategy opportunities must be a list")

    expected_count = min(3, len(context.get("candidates", [])))
    if len(opportunities) != expected_count:
        raise ValueError(f"Strategy must contain exactly {expected_count} opportunities")

    valid_video_ids = {item["video_id"] for item in context.get("candidates", [])}
    expected_ranks = list(range(1, expected_count + 1))
    ranks = [item.get("rank") for item in opportunities]
    if any(not isinstance(rank, int) for rank in ranks) or sorted(ranks) != expected_ranks:
        raise ValueError(f"Opportunity ranks must be exactly {expected_ranks}")

    required_text = ["working_title", "angle", "why_now", "audience_fit", "risks"]
    for item in opportunities:
        if not isinstance(item, dict):
            raise ValueError("Each opportunity must be a JSON object")
        for field in required_text:
            if not str(item.get(field, "")).strip():
                raise ValueError(f"Opportunity {item.get('rank')} is missing {field}")

        confidence = str(item.get("confidence", "")).upper()
        if confidence not in CONFIDENCE_LEVELS:
            raise ValueError(
                f"Opportunity {item.get('rank')} confidence must be HIGH, MEDIUM, or LOW"
            )

        source_video_ids = item.get("source_video_ids")
        if not isinstance(source_video_ids, list) or not source_video_ids:
            raise ValueError(f"Opportunity {item.get('rank')} needs at least one source_video_id")
        if any(not isinstance(video_id, str) or not video_id.strip() for video_id in source_video_ids):
            raise ValueError(f"Opportunity {item.get('rank')} has an invalid source_video_id")
        unknown = set(source_video_ids) - valid_video_ids
        if unknown:
            raise ValueError(
                f"Opportunity {item.get('rank')} references unknown source video IDs: {sorted(unknown)}"
            )


def render_strategy_markdown(payload: dict, context: dict) -> str:
    candidates_by_id = {item["video_id"]: item for item in context["candidates"]}
    lines = [
        f"# Daily Content Strategy - {_parse_timestamp(context['prepared_at']).date().isoformat()}",
        "",
        f"Research run: **{context['research_run_id']}**",
        "",
        "## Executive summary",
        "",
        payload["summary"].strip(),
        "",
    ]

    for item in sorted(payload["opportunities"], key=lambda x: x["rank"]):
        lines.extend([
            f"## {item['rank']}. {item['working_title']}",
            "",
            f"- Confidence: **{str(item['confidence']).upper()}**",
            f"- Angle: {item['angle']}",
            f"- Why now: {item['why_now']}",
            f"- Audience fit: {item['audience_fit']}",
            f"- Risks / caveats: {item['risks']}",
            "- Evidence:",
        ])
        for video_id in item["source_video_ids"]:
            source = candidates_by_id[video_id]
            velocity = source["velocity_views_per_hour"]
            velocity_text = "n/a" if velocity is None else f"{velocity:,.1f} views/hour"
            lines.append(
                f"  - {source['channel_title']} — {source['title']} — "
                f"{source['raw_outlier']:.2f}x — age {source['age_hours']:.1f}h — "
                f"velocity {velocity_text} — {source['url']}"
            )
        lines.append("")

    return "\n".join(lines)


def persist_strategy(payload: dict, context: dict, db_path: str) -> int:
    validate_strategy_payload(payload, context)
    created_at = datetime.now(timezone.utc).isoformat()
    raw_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)

    with connect(db_path) as conn:
        existing = conn.execute(
            "SELECT id FROM strategy_reports WHERE research_run_id=?",
            (context["research_run_id"],),
        ).fetchone()
        if existing:
            conn.execute("DELETE FROM strategy_reports WHERE id=?", (existing["id"],))

        cursor = conn.execute(
            """INSERT INTO strategy_reports(research_run_id, created_at, summary, raw_json)
            VALUES (?, ?, ?, ?)""",
            (context["research_run_id"], created_at, payload["summary"].strip(), raw_json),
        )
        report_id = int(cursor.lastrowid)

        for item in sorted(payload["opportunities"], key=lambda x: x["rank"]):
            conn.execute(
                """INSERT INTO strategy_opportunities
                (strategy_report_id, rank, working_title, angle, why_now, audience_fit,
                 confidence, source_video_ids, risks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    report_id,
                    item["rank"],
                    item["working_title"].strip(),
                    item["angle"].strip(),
                    item["why_now"].strip(),
                    item["audience_fit"].strip(),
                    str(item["confidence"]).upper(),
                    json.dumps(item["source_video_ids"]),
                    item["risks"].strip(),
                ),
            )

    return report_id
