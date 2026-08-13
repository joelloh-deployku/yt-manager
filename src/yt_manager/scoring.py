from statistics import median


def calculate_baseline(view_counts: list[int]) -> float:
    """Return a robust recent-channel baseline using median views."""
    clean = [int(v) for v in view_counts if int(v) >= 0]
    if not clean:
        return 0.0
    return float(median(clean))


def calculate_outlier_score(views: int, baseline_views: float) -> float:
    """Views divided by channel baseline. Zero baseline yields 0, not infinity."""
    if baseline_views <= 0:
        return 0.0
    return round(int(views) / float(baseline_views), 2)
