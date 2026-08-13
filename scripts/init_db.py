import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv
from yt_manager.db import initialize

load_dotenv(ROOT / ".env")
db_path = os.getenv("DATABASE_PATH", "data/yt_manager.db")
initialize(db_path)
print(f"Initialized SQLite database at {db_path}")
