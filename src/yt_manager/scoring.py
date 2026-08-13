from datetime import datetime, timedelta, timezone
from statistics import median

BREAKOUT_THRESHOLD = 1.25
WATCHLIST_THRESHOLD = 0.80


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


def classify_outlier(score: float) -> str:
    """Classify raw outlier performance without mixing in topic relevance."""
    if score >= BREAKOUT_THRESHOLD:
        return "breakout"
    if score >= WATCHLIST_THRESHOLD:
        return "watchlist"
    return "underperformer"


def partition_by_candidate_window(
    videos: list[dict],
    window_days: int,
    now: datetime | None = None,
) -> tuple[list[dict], list[dict]]:
    """Split uploads into recent candidates and older videos for baseline calculation."""
    if window_days <= 0:
        raise ValueError("window_days must be positive")

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    cutoff = current - timedelta(days=window_days)

    candidates = []
    historical = []
    for video in videos:
        published = datetime.fromisoformat(video["published_at"].replace("Z", "+00:00"))
        if cutoff <= published <= current:
            candidates.append(video)
        elif published < cutoff:
            historical.append(video)

    return candidates, historical
