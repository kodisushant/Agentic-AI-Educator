import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DB_PATH = Path(os.getenv("LEARNER_DB_PATH", Path(__file__).parent / "learner.db"))

_local = threading.local()


def get_db_connection() -> sqlite3.Connection:
    """
    Create and return a thread-local cached connection to the SQLite database.
    Configured with WAL mode and memory cache for low-latency operations (< 1 ms).
    """
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=15.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA cache_size = -64000;")
        _local.conn = conn
    return conn


def close_thread_connection() -> None:
    """Optionally close thread-local connection."""
    conn = getattr(_local, "conn", None)
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass
        _local.conn = None


def init_db(connection: Optional[sqlite3.Connection] = None) -> None:
    """Initialize database tables with complete constraints and indices."""
    conn = connection or get_db_connection()
    with conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            created_at TEXT NOT NULL,
            last_active TEXT NOT NULL
        );
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS concepts (
            tag TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            topic TEXT NOT NULL,
            description TEXT,
            difficulty TEXT DEFAULT 'beginner'
        );
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            concept_tag TEXT NOT NULL,
            question_id TEXT,
            is_correct INTEGER NOT NULL,
            time_spent_seconds REAL DEFAULT 15.0,
            misconceptions_json TEXT DEFAULT '[]',
            metadata_json TEXT DEFAULT '{}',
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(concept_tag) REFERENCES concepts(tag)
        );
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS mastery (
            user_id TEXT NOT NULL,
            concept_tag TEXT NOT NULL,
            score REAL NOT NULL,
            attempt_count INTEGER DEFAULT 0,
            last_attempt_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, concept_tag),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(concept_tag) REFERENCES concepts(tag)
        );
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS misconceptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            concept_tag TEXT NOT NULL,
            misconception_tag TEXT NOT NULL,
            frequency INTEGER DEFAULT 1,
            last_observed_at TEXT NOT NULL,
            UNIQUE (user_id, concept_tag, misconception_tag),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(concept_tag) REFERENCES concepts(tag)
        );
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_attempts_user_id ON attempts(user_id, id DESC);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_attempts_user_concept ON attempts(user_id, concept_tag);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_mastery_user ON mastery(user_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_misconceptions_user ON misconceptions(user_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_misconceptions_lookup ON misconceptions(user_id, concept_tag, frequency DESC);")
