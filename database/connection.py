"""Database connection layer — PostgreSQL via psycopg2 (Supabase).

Reads DATABASE_URL from environment. Provides context-managed connections
with auto-commit on success and rollback on error.
"""

import logging
import os

from dotenv import load_dotenv

load_dotenv()

import psycopg2
import psycopg2.extras
from contextlib import contextmanager

logger = logging.getLogger(__name__)

_DATABASE_URL = os.getenv("DATABASE_URL", "")


@contextmanager
def get_connection():
    """Get a PostgreSQL connection. Auto-commits on success, rolls back on error."""
    conn = psycopg2.connect(_DATABASE_URL)
    try:
        yield conn
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
    """Execute schema file to create all tables."""
    db_dir = os.path.dirname(__file__)
    schema_path = os.path.join(db_dir, "schema.sql")
    conn = psycopg2.connect(_DATABASE_URL)
    try:
        with conn.cursor() as cur:
            with open(schema_path, "r") as f:
                cur.execute(f.read())
        conn.commit()
        logger.info("Database initialized via %s", schema_path)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
