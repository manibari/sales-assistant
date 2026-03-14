"""Database connection layer — SQLite with psycopg2-compatible interface.

Provides the same API as the original PostgreSQL version so all services
work unchanged. Key adaptations:
- %s placeholders → ? (handled by cursor wrapper)
- NOW() → datetime('now') (handled by SQL registration)
- RETURNING clause works in SQLite 3.35+
"""

import logging
import os
import re
import sqlite3
from contextlib import contextmanager

logger = logging.getLogger(__name__)

_DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "nexus.db"))


def _get_db_path() -> str:
    return _DB_PATH


class _CursorWrapper:
    """Wraps sqlite3.Cursor to accept psycopg2-style %s placeholders."""

    def __init__(self, cursor: sqlite3.Cursor):
        self._cur = cursor

    @property
    def description(self):
        return self._cur.description

    def execute(self, sql: str, params=None):
        sql = _adapt_sql(sql)
        if params:
            return self._cur.execute(sql, params)
        return self._cur.execute(sql)

    def executescript(self, sql: str):
        return self._cur.executescript(sql)

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    def __iter__(self):
        return iter(self._cur)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class _ConnectionWrapper:
    """Wraps sqlite3.Connection to return wrapped cursors."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def cursor(self):
        return _CursorWrapper(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


def _adapt_sql(sql: str) -> str:
    """Convert PostgreSQL SQL to SQLite-compatible SQL."""
    # %s → ? (but not inside strings or %% escapes)
    sql = re.sub(r'(?<!%)%s', '?', sql)
    # NOW() → datetime('now')
    sql = sql.replace("NOW()", "datetime('now')")
    return sql


@contextmanager
def get_connection():
    """Get a SQLite connection. Auto-commits on success, rolls back on error."""
    conn = sqlite3.connect(_get_db_path())
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    wrapped = _ConnectionWrapper(conn)
    try:
        yield wrapped
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def read_sql_file(file_name: str) -> str:
    query_path = os.path.join(os.path.dirname(__file__), "queries", file_name)
    try:
        with open(query_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error("SQL file not found at %s", query_path)
        raise


def row_to_dict(cur):
    """Convert single cursor row to dict. Returns None if no row."""
    row = cur.fetchone()
    if row is None:
        return None
    cols = [d[0] for d in cur.description]
    return dict(zip(cols, row))


def rows_to_dicts(cur):
    """Convert all cursor rows to list of dicts."""
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def init_db():
    """Execute both legacy and Nexus schema files to create all tables."""
    db_dir = os.path.dirname(__file__)
    schema_files = ["schema_sqlite.sql", "schema_nexus.sql"]
    conn = sqlite3.connect(_get_db_path())
    conn.execute("PRAGMA foreign_keys=ON")
    # Run migrations first so new columns exist before schema indexes
    _run_migrations(conn)
    for schema_file in schema_files:
        schema_path = os.path.join(db_dir, schema_file)
        if os.path.exists(schema_path):
            with open(schema_path, "r") as f:
                conn.executescript(f.read())
    conn.commit()
    conn.close()
    logger.info("Database initialized at %s", _get_db_path())


def _get_table_columns(conn: sqlite3.Connection, table_name: str) -> set[str] | None:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    if not cur.fetchone():
        return None
    cur = conn.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cur.fetchall()}


def _run_migrations(conn: sqlite3.Connection):
    """Add columns missing from older schema versions."""
    file_columns = _get_table_columns(conn, "nx_file")
    if file_columns is not None and "intel_id" not in file_columns:
        conn.execute("ALTER TABLE nx_file ADD COLUMN intel_id INTEGER REFERENCES nx_intel(id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_nx_file_intel ON nx_file(intel_id)")
        logger.info("Migration: added intel_id to nx_file")

    # Migration: duration_minutes on nx_meeting
    meeting_columns = _get_table_columns(conn, "nx_meeting")
    if meeting_columns is not None and "duration_minutes" not in meeting_columns:
        conn.execute("ALTER TABLE nx_meeting ADD COLUMN duration_minutes INTEGER NOT NULL DEFAULT 60")
        logger.info("Migration: added duration_minutes to nx_meeting")

    # Migration: budget_amount + budget_year on nx_deal
    deal_columns = _get_table_columns(conn, "nx_deal")
    if deal_columns is not None and "budget_amount" not in deal_columns:
        conn.execute("ALTER TABLE nx_deal ADD COLUMN budget_amount REAL")
        conn.execute("ALTER TABLE nx_deal ADD COLUMN budget_year INTEGER DEFAULT 2026")
        # Backfill from budget_range
        mapping = {
            "<100K": 100000,
            "100-500K": 300000,
            "500K-1M": 750000,
            "1M+": 1000000,
        }
        for text_val, amount in mapping.items():
            conn.execute(
                "UPDATE nx_deal SET budget_amount = ? WHERE budget_range = ?",
                (amount, text_val),
            )
        conn.execute(
            "UPDATE nx_deal SET budget_year = 2026 WHERE budget_year IS NULL"
        )
        logger.info("Migration: added budget_amount, budget_year to nx_deal + backfill")

    # Migration: aliases on nx_client
    client_columns = _get_table_columns(conn, "nx_client")
    if client_columns is not None and "aliases" not in client_columns:
        conn.execute("ALTER TABLE nx_client ADD COLUMN aliases TEXT")
        logger.info("Migration: added aliases to nx_client")

    intel_columns = _get_table_columns(conn, "nx_intel")
    if intel_columns is not None and "title" not in intel_columns:
        conn.execute("ALTER TABLE nx_intel ADD COLUMN title TEXT")
        logger.info("Migration: added title to nx_intel")
    if intel_columns is not None and "chat_history" not in intel_columns:
        conn.execute("ALTER TABLE nx_intel ADD COLUMN chat_history TEXT")
        logger.info("Migration: added chat_history to nx_intel")
