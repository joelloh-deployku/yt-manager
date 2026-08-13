from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from yt_manager.reporting import format_candidate_age, render_daily_report


def _candidate(title: str, score: float, published_at: str) -> dict:
    return {
        "title": title,
        "channel_title": "Example Channel",
        "views": 1500,
        "baseline_views": 1000.0,
        "outlier_score": score,
        "published_at": published_at,
        "url": "https://www.youtube.com/watch?v=example",
    }


def test_candidate_age_in_days():
    now = datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc)
    assert format_candidate_age("2026-08-10T12:00:00Z", now) == "3 days ago"


def test_report_groups_performance_tiers(tmp_path):
    now = datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc)
    candidates = [
        _candidate("Breakout video", 1.50, "2026-08-10T12:00:00Z"),
        _candidate("Watch video", 1.00, "2026-08-11T12:00:00Z"),
        _candidate("Weak video", 0.50, "2026-08-12T12:00:00Z"),
    ]

    path = render_daily_report(candidates, str(tmp_path), now=now)
    report = path.read_text(encoding="utf-8")

    assert "## Breakouts (>= 1.25x)" in report
    assert "## Watchlist (0.80x - 1.24x)" in report
    assert "## Underperformers (< 0.80x)" in report
    assert "Breakouts: **1** | Watchlist: **1** | Underperformers: **1**" in report
    assert "- Age: 3 days ago" in report
    assert "- Raw outlier: **1.50x**" in report
