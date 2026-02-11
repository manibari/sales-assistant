"""Settings service — CRUD for app_settings table (customizable page headers).

Public API:
    get_all_headers() → dict       # {key: value} for all settings
    update_header(key, value) → None  # upsert
"""

from database.connection import get_connection


def get_all_headers():
    """Return all settings as a dict {key: value}."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT key, value FROM app_settings ORDER BY key")
            return {row[0]: row[1] for row in cur.fetchall()}


def update_header(key, value):
    """Update a single setting. Creates it if it doesn't exist."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO app_settings (key, value) VALUES (%s, %s)
                   ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value""",
                (key, value),
            )
