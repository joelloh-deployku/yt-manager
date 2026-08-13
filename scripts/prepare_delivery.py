import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv
from yt_manager.db import initialize
from yt_manager.production import build_production_context, write_production_context


def main() -> int:
    load_dotenv(ROOT / ".env")
    db_path = os.getenv("DATABASE_PATH", "data/yt_manager.db")
    output_dir = os.getenv("OUTPUT_DIR", "outputs")
    resolved_db = str(ROOT / db_path) if not Path(db_path).is_absolute() else db_path
    resolved_output = ROOT / output_dir if not Path(output_dir).is_absolute() else Path(output_dir)
    initialize(resolved_db)
    context = build_production_context(resolved_db)
    path = write_production_context(context, str(resolved_output))
    selected = context["selected_thumbnail_concept"]
    print(f"Delivery input ready: {path}")
    print(f"QA report: {context['qa_report_id']} - PASS")
    print(f"Script report: {context['script_report_id']}")
    print(f"Thumbnail report: {context['thumbnail_report_id']}")
    print(f"Creator inputs to cover: {context['requirements']['creator_input_count']}")
    print(f"Verification items to carry: {context['requirements']['verification_count']}")
    print(f"Recommended thumbnail: #{selected['rank']} - {selected['concept_name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
