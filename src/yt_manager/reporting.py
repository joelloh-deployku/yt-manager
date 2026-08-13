from datetime import datetime, timedelta, timezone
from pathlib import Path

from yt_manager.scoring import classify_outlier


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def format_candidate_age(published_at: str, now: datetime) -> str:
    published = _parse_timestamp(published_at)
    delta = max(now - published, timedelta(0))
    total_hours = max(int(delta.total_seconds() // 3600), 0)
    if total_hours < 24:
        unit = "hour" if total_hours == 1 else "hours"
        return f"{total_hours} {unit} ago"
    days = total_hours // 24
    unit = "day" if days == 1 else "days"
    return f"{days} {unit} ago"


def _render_section(lines: list[str], title: str, items: list[dict], now: datetime) -> None:
    lines.extend([f"## {title}", ""])
    if not items:
        lines.extend(["None.", ""])
        return

    for index, item in enumerate(items, 1):
        lines.extend([
            f"### {index}. {item['title']}",
            f"- Channel: {item['channel_title']}",
            f"- Views: {item['views']:,}",
            f"- Channel baseline: {item['baseline_views']:,.0f}",
            f"- Raw outlier: **{item['outlier_score']:.2f}x**",
            f"- Age: {format_candidate_age(item['published_at'], now)}",
            f"- Published: {item['published_at']}",
            f"- Source: {item['url']}",
            "",
        ])


def render_daily_report(
    candidates: list[dict],
    output_dir: str,
    now: datetime | None = None,
) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    path = out / f"{current.date().isoformat()}-daily-research.md"

    ranked = sorted(candidates, key=lambda x: x["outlier_score"], reverse=True)
    groups = {"breakout": [], "watchlist": [], "underperformer": []}
    for item in ranked:
        groups[classify_outlier(item["outlier_score"])].append(item)

    lines = [
        f"# Daily YouTube Research - {current.date().isoformat()}",
        "",
        f"Candidates analyzed: **{len(ranked)}**",
        f"Breakouts: **{len(groups['breakout'])}** | Watchlist: **{len(groups['watchlist'])}** | Underperformers: **{len(groups['underperformer'])}**",
        "",
    ]

    _render_section(lines, "Breakouts (>= 1.25x)", groups["breakout"][:10], current)
    _render_section(lines, "Watchlist (0.80x - 1.24x)", groups["watchlist"][:10], current)
    _render_section(lines, "Underperformers (< 0.80x)", groups["underperformer"][:10], current)

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
