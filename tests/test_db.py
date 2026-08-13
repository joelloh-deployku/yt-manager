from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from yt_manager.db import connect, initialize


def test_initialize_creates_video_snapshots_table(tmp_path):
    db_path = tmp_path / "yt_manager.db"
    initialize(str(db_path))

    with connect(str(db_path)) as conn:
        table = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='video_snapshots'"
        ).fetchone()
        indexes = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='video_snapshots'"
            ).fetchall()
        }

    assert table is not None
    assert "idx_video_snapshots_video_time" in indexes
