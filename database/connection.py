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
    """Execute schema_sqlite.sql to create all tables."""
    schema_path = os.path.join(os.path.dirname(__file__), "schema_sqlite.sql")
    with open(schema_path, "r") as f:
        sql = f.read()
    conn = sqlite3.connect(_get_db_path())
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(sql)
    conn.commit()
    conn.close()
    logger.info("Database initialized at %s", _get_db_path())
