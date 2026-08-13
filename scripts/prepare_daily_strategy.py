import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv
from yt_manager.strategy import build_strategy_context, write_strategy_context


def main() -> int:
    load_dotenv(ROOT / ".env")
    db_path = os.getenv("DATABASE_PATH", "data/yt_manager.db")
    output_dir = os.getenv("OUTPUT_DIR", "outputs")
    profile_path = os.getenv("CHANNEL_PROFILE_PATH", "config/channel-profile.json")

    context = build_strategy_context(
        str(ROOT / db_path) if not Path(db_path).is_absolute() else db_path,
        str(ROOT / profile_path) if not Path(profile_path).is_absolute() else profile_path,
    )
    output_path = write_strategy_context(
        context,
        str(ROOT / output_dir) if not Path(output_dir).is_absolute() else output_dir,
    )

    print(f"Strategist input ready: {output_path}")
    print(f"Research run: {context['research_run_id']}")
    print(f"Candidates available: {context['candidate_count']}")
    velocity_count = sum(
        1 for item in context["candidates"] if item["velocity_views_per_hour"] is not None
    )
    print(f"Candidates with velocity data: {velocity_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
