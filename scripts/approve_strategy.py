import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv
from yt_manager.script_writer import approve_opportunity


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Explicitly approve one strategist opportunity for script writing."
    )
    parser.add_argument("--rank", type=int, required=True, help="Opportunity rank to approve")
    parser.add_argument("--notes", default="", help="Optional human direction for the Script Writer")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    db_path = os.getenv("DATABASE_PATH", "data/yt_manager.db")
    resolved_db = str(ROOT / db_path) if not Path(db_path).is_absolute() else db_path

    approval = approve_opportunity(resolved_db, args.rank, args.notes)
    print(f"Approved strategy opportunity #{approval['opportunity_rank']} for scripting")
    print(f"Approval ID: {approval['approval_id']}")
    print(f"Strategy report: {approval['strategy_report_id']}")
    print(f"Working title: {approval['working_title']}")
    if approval["notes"]:
        print(f"Human notes: {approval['notes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
