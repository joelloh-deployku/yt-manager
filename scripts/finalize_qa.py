import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv
from yt_manager.qa import persist_qa, render_qa_markdown, validate_qa_payload


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python scripts/finalize_qa.py <qa-input.json> <qa-draft.json>")

    load_dotenv(ROOT / ".env")
    db_path = os.getenv("DATABASE_PATH", "data/yt_manager.db")
    output_dir = os.getenv("OUTPUT_DIR", "outputs")
    resolved_db = str(ROOT / db_path) if not Path(db_path).is_absolute() else db_path
    resolved_output = ROOT / output_dir if not Path(output_dir).is_absolute() else Path(output_dir)

    input_path = Path(sys.argv[1])
    draft_path = Path(sys.argv[2])
    context = json.loads(input_path.read_text(encoding="utf-8"))
    payload = json.loads(draft_path.read_text(encoding="utf-8"))

    validate_qa_payload(payload, context)
    report_id = persist_qa(payload, context, resolved_db)

    prepared_date = context["prepared_at"][:10]
    resolved_output.mkdir(parents=True, exist_ok=True)
    json_path = resolved_output / f"{prepared_date}-qa.json"
    markdown_path = resolved_output / f"{prepared_date}-qa.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    markdown_path.write_text(render_qa_markdown(payload, context), encoding="utf-8")

    print(f"QA validated and stored: report {report_id}")
    print(f"QA status: {str(payload['status']).upper()}")
    print(f"Canonical JSON: {json_path}")
    print(f"QA report: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
