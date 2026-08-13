import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv
from yt_manager.script_writer import build_script_context, write_script_context


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare Script Writer input from a human-approved opportunity.")
    parser.add_argument("--approval-id", type=int, help="Optional specific approval ID; defaults to latest")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    db_path = os.getenv("DATABASE_PATH", "data/yt_manager.db")
    output_dir = os.getenv("OUTPUT_DIR", "outputs")
    profile_path = os.getenv("CHANNEL_PROFILE_PATH", "config/channel-profile.json")
    minimum_words = int(os.getenv("SCRIPT_MIN_WORDS", "600"))

    resolved_db = str(ROOT / db_path) if not Path(db_path).is_absolute() else db_path
    resolved_output = str(ROOT / output_dir) if not Path(output_dir).is_absolute() else output_dir
    resolved_profile = str(ROOT / profile_path) if not Path(profile_path).is_absolute() else profile_path

    context = build_script_context(
        resolved_db,
        resolved_profile,
        approval_id=args.approval_id,
        minimum_words=minimum_words,
    )
    path = write_script_context(context, resolved_output)

    print(f"Script Writer input ready: {path}")
    print(f"Approval ID: {context['approval']['approval_id']}")
    print(f"Strategy opportunity: #{context['approval']['opportunity_rank']}")
    print(f"Approved title: {context['approved_opportunity']['working_title']}")
    print(f"Minimum script words: {context['script_requirements']['minimum_words']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
