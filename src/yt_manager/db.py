import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL,
    candidate_count INTEGER NOT NULL DEFAULT 0,
    error TEXT
);

CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    video_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    channel_title TEXT NOT NULL,
    title TEXT NOT NULL,
    published_at TEXT NOT NULL,
    views INTEGER NOT NULL,
    baseline_views REAL NOT NULL,
    outlier_score REAL NOT NULL,
    url TEXT NOT NULL,
    UNIQUE(run_id, video_id),
    FOREIGN KEY(run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS video_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    video_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    views INTEGER NOT NULL,
    UNIQUE(run_id, video_id),
    FOREIGN KEY(run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS strategy_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    research_run_id INTEGER NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    summary TEXT NOT NULL,
    raw_json TEXT NOT NULL,
    FOREIGN KEY(research_run_id) REFERENCES runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS strategy_opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_report_id INTEGER NOT NULL,
    rank INTEGER NOT NULL,
    working_title TEXT NOT NULL,
    angle TEXT NOT NULL,
    why_now TEXT NOT NULL,
    audience_fit TEXT NOT NULL,
    confidence TEXT NOT NULL,
    source_video_ids TEXT NOT NULL,
    risks TEXT NOT NULL,
    UNIQUE(strategy_report_id, rank),
    FOREIGN KEY(strategy_report_id) REFERENCES strategy_reports(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS script_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_report_id INTEGER NOT NULL,
    opportunity_rank INTEGER NOT NULL,
    approved_at TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    UNIQUE(strategy_report_id, opportunity_rank),
    FOREIGN KEY(strategy_report_id) REFERENCES strategy_reports(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS script_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    approval_id INTEGER NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    working_title TEXT NOT NULL,
    word_count INTEGER NOT NULL,
    raw_json TEXT NOT NULL,
    FOREIGN KEY(approval_id) REFERENCES script_approvals(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_candidates_run_score
ON candidates(run_id, outlier_score DESC);

CREATE INDEX IF NOT EXISTS idx_video_snapshots_video_time
ON video_snapshots(video_id, observed_at);

CREATE INDEX IF NOT EXISTS idx_strategy_opportunities_report_rank
ON strategy_opportunities(strategy_report_id, rank);

CREATE INDEX IF NOT EXISTS idx_script_approvals_report_rank
ON script_approvals(strategy_report_id, opportunity_rank);
"""


def connect(path: str) -> sqlite3.Connection:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize(path: str) -> None:
    with connect(path) as conn:
        conn.executescript(SCHEMA)
