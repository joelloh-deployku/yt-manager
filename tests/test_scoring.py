from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from yt_manager.scoring import (
    calculate_baseline,
    calculate_outlier_score,
    partition_by_candidate_window,
)


def test_baseline_uses_median():
    assert calculate_baseline([100, 110, 120, 10000]) == 115.0


def test_outlier_score():
    assert calculate_outlier_score(500, 100) == 5.0


def test_zero_baseline_is_safe():
    assert calculate_outlier_score(500, 0) == 0.0


def test_partition_uses_candidate_window():
    now = datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc)
    videos = [
        {"published_at": "2026-08-10T12:00:00Z", "views": 100},
        {"published_at": "2026-07-31T12:00:00Z", "views": 200},
        {"published_at": "2026-07-29T11:59:59Z", "views": 300},
    ]

    recent, historical = partition_by_candidate_window(videos, 14, now=now)

    assert [v["views"] for v in recent] == [100, 200]
    assert [v["views"] for v in historical] == [300]
