import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv
from yt_manager.db import initialize
from yt_manager.thumbnail_director import build_thumbnail_context, write_thumbnail_context


def main() -> int:
    load_dotenv(ROOT / ".env")
    db_path = os.getenv("DATABASE_PATH", "data/yt_manager.db")
    output_dir = os.getenv("OUTPUT_DIR", "outputs")
    profile_path = os.getenv("CHANNEL_PROFILE_PATH", "config/channel-profile.json")
    concept_count = int(os.getenv("THUMBNAIL_CONCEPT_COUNT", "3"))
    max_text_words = int(os.getenv("THUMBNAIL_MAX_TEXT_WORDS", "5"))

    resolved_db = str(ROOT / db_path) if not Path(db_path).is_absolute() else db_path
    resolved_output = ROOT / output_dir if not Path(output_dir).is_absolute() else Path(output_dir)
    resolved_profile = str(ROOT / profile_path) if not Path(profile_path).is_absolute() else profile_path

    initialize(resolved_db)
    context = build_thumbnail_context(
        resolved_db,
        resolved_profile,
        concept_count=concept_count,
        max_text_words=max_text_words,
    )
    path = write_thumbnail_context(context, str(resolved_output))

    print(f"Thumbnail Director input ready: {path}")
    print(f"Script report: {context['script_report_id']}")
    print(f"Video title: {context['validated_script']['working_title']}")
    print(f"Concepts required: {context['thumbnail_requirements']['concept_count']}")
    print(f"Max thumbnail text words: {context['thumbnail_requirements']['max_text_words']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
