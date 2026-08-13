from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from yt_manager.scoring import calculate_baseline, calculate_outlier_score


def test_baseline_uses_median():
    assert calculate_baseline([100, 110, 120, 10000]) == 115.0


def test_outlier_score():
    assert calculate_outlier_score(500, 100) == 5.0


def test_zero_baseline_is_safe():
    assert calculate_outlier_score(500, 0) == 0.0
