"""PostgreSQL connection pool management using psycopg2."""

import os
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv()

_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        _pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            dbname=os.getenv("DB_NAME", "spms"),
            user=os.getenv("DB_USER", "spms_user"),
            password=os.getenv("DB_PASSWORD", "spms_pass"),
        )
    return _pool


@contextmanager
def get_connection():
    """Get a connection from the pool. Auto-commits on success, rolls back on error."""
    p = _get_pool()
    conn = p.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn)


def read_sql_file(file_name: str) -> str:
    """
    Reads a SQL query from a file in the database/queries directory.
    """
    # Construct the full path to the SQL file
    query_path = os.path.join(os.path.dirname(__file__), "queries", file_name)
    try:
        with open(query_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERROR: SQL file not found at {query_path}")
        raise


def init_db():
    """Execute schema.sql to create all tables."""
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r") as f:
        sql = f.read()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
