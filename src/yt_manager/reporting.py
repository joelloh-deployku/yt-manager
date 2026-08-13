from datetime import datetime, timezone
from pathlib import Path


def render_daily_report(candidates: list[dict], output_dir: str) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    path = out / f"{now.date().isoformat()}-daily-research.md"

    ranked = sorted(candidates, key=lambda x: x["outlier_score"], reverse=True)
    lines = [
        f"# Daily YouTube Research - {now.date().isoformat()}",
        "",
        f"Candidates analyzed: **{len(ranked)}**",
        "",
        "## Top opportunities",
        "",
    ]
    if not ranked:
        lines.append("No candidates were found.")
    else:
        for index, item in enumerate(ranked[:10], 1):
            lines.extend([
                f"### {index}. {item['title']}",
                f"- Channel: {item['channel_title']}",
                f"- Views: {item['views']:,}",
                f"- Channel baseline: {item['baseline_views']:,.0f}",
                f"- Outlier score: **{item['outlier_score']:.2f}x**",
                f"- Published: {item['published_at']}",
                f"- Source: {item['url']}",
                "",
            ])
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
