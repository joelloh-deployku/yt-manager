import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv
from yt_manager.db import initialize
from yt_manager.qa import build_qa_context, ensure_qa_schema, write_qa_context


def main() -> int:
    load_dotenv(ROOT / ".env")
    db_path = os.getenv("DATABASE_PATH", "data/yt_manager.db")
    output_dir = os.getenv("OUTPUT_DIR", "outputs")

    resolved_db = str(ROOT / db_path) if not Path(db_path).is_absolute() else db_path
    resolved_output = ROOT / output_dir if not Path(output_dir).is_absolute() else Path(output_dir)

    initialize(resolved_db)
    ensure_qa_schema(resolved_db)
    context = build_qa_context(resolved_db)
    path = write_qa_context(context, str(resolved_output))

    checks = context["deterministic_checks"]
    print(f"QA input ready: {path}")
    print(f"Script report: {context['script_report_id']}")
    print(f"Thumbnail report: {context['thumbnail_report_id']}")
    print(f"Thumbnail concepts: {checks['thumbnail_concept_count']}")
    print(f"Open creator inputs: {checks['creator_inputs_needed_count']}")
    print(f"Verification notes: {checks['verification_notes_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
