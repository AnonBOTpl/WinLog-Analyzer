import sqlite3
import os
from datetime import datetime
from core.paths import data_file

DB_DIR = data_file("data")
DB_PATH = DB_DIR / "winlog_history.db"


def get_connection():
    """Get a SQLite connection to the analysis history database.

    The database and tables are created on first access.
    Returns a connection with row_factory set to sqlite3.Row.
    """
    return _get_conn()


def _get_conn():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source TEXT,
            event_id INTEGER,
            level TEXT,
            message TEXT,
            provider TEXT,
            ai_explanation TEXT,
            ai_severity TEXT,
            ai_steps TEXT,
            ai_tip TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_analyses_analyzed_at ON analyses(analyzed_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_analyses_source_event ON analyses(source, event_id)")
    conn.commit()
    return conn


def save_analysis(event: dict, result: dict, provider: str):
    """Save an AI analysis result to the history database."""
    conn = _get_conn()
    conn.execute(
        """
        INSERT INTO analyses (source, event_id, level, message, provider,
                              ai_explanation, ai_severity, ai_steps, ai_tip)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event.get("SourceName", ""),
            event.get("EventID", 0),
            event.get("Level", ""),
            event.get("Message", "")[:500],
            provider,
            result.get("explanation", ""),
            result.get("severity", ""),
            result.get("steps", ""),
            result.get("tip", ""),
        ),
    )
    conn.commit()
    conn.close()


def get_history(limit: int = 50) -> list[dict]:
    """Get the most recent analysis records."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM analyses ORDER BY analyzed_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_history_by_date(date_from: str, date_to: str) -> list[dict]:
    """Get analysis records within a date range (ISO format strings)."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM analyses WHERE analyzed_at BETWEEN ? AND ? ORDER BY analyzed_at DESC",
        (date_from, date_to),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def clear_history():
    """Delete all analysis records from the database."""
    conn = _get_conn()
    conn.execute("DELETE FROM analyses")
    conn.commit()
    conn.close()
