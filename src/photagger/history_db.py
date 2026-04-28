"""
Photagger — SQLite processing history database.
Stores every processing event for undo, history, and reporting.
"""
import sqlite3
import time
from pathlib import Path
from .logger import get_logger

log = get_logger("history")


class HistoryDB:
    """SQLite-backed processing history."""

    def __init__(self, db_path: str | Path = None):
        if db_path is None:
            import os
            appdata = os.environ.get("APPDATA", Path.home() / ".config")
            db_dir = Path(appdata) / "Photagger"
            db_dir.mkdir(parents=True, exist_ok=True)
            db_path = db_dir / "history.db"

        self.db_path = str(db_path)
        self._init_db()

    def _init_db(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processing_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    original_path TEXT,
                    final_path TEXT,
                    timestamp REAL NOT NULL,
                    blur_score REAL,
                    exposure_score REAL,
                    exposure_verdict TEXT,
                    star_rating INTEGER,
                    tags TEXT,
                    category TEXT,
                    status TEXT NOT NULL,
                    exif_summary TEXT,
                    session_id TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    start_time REAL NOT NULL,
                    end_time REAL,
                    total_processed INTEGER DEFAULT 0,
                    total_accepted INTEGER DEFAULT 0,
                    total_rejected INTEGER DEFAULT 0
                )
            """)
        log.info(f"History database ready: {self.db_path}")

    def start_session(self) -> str:
        """Create a new processing session. Returns session_id."""
        session_id = f"session_{int(time.time())}"
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO sessions (id, start_time) VALUES (?, ?)",
                (session_id, time.time())
            )
        return session_id

    def end_session(self, session_id: str):
        """Finalize a session with counts."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT COUNT(*), SUM(CASE WHEN status='accepted' THEN 1 ELSE 0 END), "
                "SUM(CASE WHEN status='rejected' THEN 1 ELSE 0 END) "
                "FROM processing_log WHERE session_id=?",
                (session_id,)
            ).fetchone()
            conn.execute(
                "UPDATE sessions SET end_time=?, total_processed=?, total_accepted=?, total_rejected=? WHERE id=?",
                (time.time(), row[0] or 0, row[1] or 0, row[2] or 0, session_id)
            )

    def log_processed(self, filename: str, original_path: str, final_path: str,
                      blur_score: float, exposure_score: float, exposure_verdict: str,
                      star_rating: int, tags: list[str], category: str,
                      status: str, exif_summary: str = "", session_id: str = ""):
        """Log a single processing event."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO processing_log "
                "(filename, original_path, final_path, timestamp, blur_score, "
                "exposure_score, exposure_verdict, star_rating, tags, category, "
                "status, exif_summary, session_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (filename, original_path, final_path, time.time(),
                 blur_score, exposure_score, exposure_verdict, star_rating,
                 ",".join(tags), category, status, exif_summary, session_id)
            )

    def get_session_stats(self, session_id: str) -> dict:
        """Get statistics for a session."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            session = conn.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
            if not session:
                return {}

            # Category breakdown
            cats = conn.execute(
                "SELECT category, COUNT(*) as cnt FROM processing_log "
                "WHERE session_id=? AND status='accepted' GROUP BY category",
                (session_id,)
            ).fetchall()

            return {
                "session_id": session["id"],
                "total_processed": session["total_processed"],
                "total_accepted": session["total_accepted"],
                "total_rejected": session["total_rejected"],
                "categories": {r["category"]: r["cnt"] for r in cats},
                "duration": (session["end_time"] or time.time()) - session["start_time"],
            }

    def get_recent_entries(self, limit: int = 100) -> list[dict]:
        """Get the most recent processing entries."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM processing_log ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_all_for_session(self, session_id: str) -> list[dict]:
        """Get all entries for a session."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM processing_log WHERE session_id=? ORDER BY timestamp",
                (session_id,)
            ).fetchall()
            return [dict(r) for r in rows]
