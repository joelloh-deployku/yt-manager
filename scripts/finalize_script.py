import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv
from yt_manager.script_writer import (
    persist_script,
    render_script_markdown,
    script_word_count,
    validate_script_payload,
)


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit(
            "Usage: python scripts/finalize_script.py <script-input.json> <script-draft.json>"
        )

    load_dotenv(ROOT / ".env")
    db_path = os.getenv("DATABASE_PATH", "data/yt_manager.db")
    output_dir = os.getenv("OUTPUT_DIR", "outputs")
    resolved_db = str(ROOT / db_path) if not Path(db_path).is_absolute() else db_path
    resolved_output = ROOT / output_dir if not Path(output_dir).is_absolute() else Path(output_dir)

    input_path = Path(sys.argv[1])
    draft_path = Path(sys.argv[2])
    context = json.loads(input_path.read_text(encoding="utf-8"))
    payload = json.loads(draft_path.read_text(encoding="utf-8"))

    validate_script_payload(payload, context)
    report_id = persist_script(payload, context, resolved_db)

    prepared_date = context["prepared_at"][:10]
    resolved_output.mkdir(parents=True, exist_ok=True)
    json_path = resolved_output / f"{prepared_date}-script.json"
    markdown_path = resolved_output / f"{prepared_date}-script.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    markdown_path.write_text(render_script_markdown(payload, context), encoding="utf-8")

    print(f"Script validated and stored: report {report_id}")
    print(f"Word count: {script_word_count(payload)}")
    print(f"Canonical JSON: {json_path}")
    print(f"Script report: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
