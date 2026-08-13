import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv
from yt_manager.db import connect, initialize
from yt_manager.reporting import render_daily_report
from yt_manager.scoring import calculate_baseline, calculate_outlier_score
from yt_manager.youtube import YouTubeResearchClient


def main() -> int:
    load_dotenv(ROOT / ".env")
    api_key = os.getenv("YOUTUBE_API_KEY", "").strip()
    channel_ids = [x.strip() for x in os.getenv("COMPETITOR_CHANNEL_IDS", "").split(",") if x.strip()]
    videos_per_channel = int(os.getenv("VIDEOS_PER_CHANNEL", "15"))
    baseline_count = int(os.getenv("BASELINE_VIDEO_COUNT", "12"))
    db_path = os.getenv("DATABASE_PATH", "data/yt_manager.db")
    output_dir = os.getenv("OUTPUT_DIR", "outputs")

    if not channel_ids:
        raise SystemExit("COMPETITOR_CHANNEL_IDS must contain at least one YouTube channel ID")

    initialize(db_path)
    client = YouTubeResearchClient(api_key)
    started = datetime.now(timezone.utc).isoformat()

    with connect(db_path) as conn:
        cursor = conn.execute("INSERT INTO runs(started_at, status) VALUES (?, ?)", (started, "running"))
        run_id = cursor.lastrowid

    candidates = []
    try:
        for channel_id in channel_ids:
            videos = client.recent_videos(channel_id, max(videos_per_channel, baseline_count))
            baseline_sample = [v["views"] for v in videos[:baseline_count]]
            baseline = calculate_baseline(baseline_sample)
            for video in videos[:videos_per_channel]:
                item = dict(video)
                item["baseline_views"] = baseline
                item["outlier_score"] = calculate_outlier_score(item["views"], baseline)
                candidates.append(item)

        with connect(db_path) as conn:
            for item in candidates:
                conn.execute(
                    """INSERT INTO candidates
                    (run_id, video_id, channel_id, channel_title, title, published_at,
                     views, baseline_views, outlier_score, url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (run_id, item["video_id"], item["channel_id"], item["channel_title"],
                     item["title"], item["published_at"], item["views"],
                     item["baseline_views"], item["outlier_score"], item["url"]),
                )
            conn.execute(
                "UPDATE runs SET completed_at=?, status=?, candidate_count=? WHERE id=?",
                (datetime.now(timezone.utc).isoformat(), "completed", len(candidates), run_id),
            )

        report = render_daily_report(candidates, output_dir)
        print(f"Research complete: {len(candidates)} candidates")
        print(f"Report: {report}")
        return 0
    except Exception as exc:
        with connect(db_path) as conn:
            conn.execute(
                "UPDATE runs SET completed_at=?, status=?, error=? WHERE id=?",
                (datetime.now(timezone.utc).isoformat(), "failed", str(exc), run_id),
            )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
