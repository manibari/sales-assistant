"""Migrate data from local SQLite (nexus.db) to Supabase PostgreSQL.

Usage:
    DATABASE_URL=postgresql://... python scripts/migrate_to_supabase.py

Reads nexus.db from database/ directory, inserts all rows into the
remote PostgreSQL database in foreign-key-safe order, then syncs
SERIAL sequences.
"""

import json
import os
import sqlite3
import sys

import psycopg2
import psycopg2.extras

DB_DIR = os.path.join(os.path.dirname(__file__), "..", "database")
SQLITE_PATH = os.path.join(DB_DIR, "nexus.db")

# Tables in foreign-key-safe insertion order
TABLES = [
    # Legacy SPMS (no FK dependencies first)
    "app_settings",
    "stage_probability",
    "annual_plan",
    "crm",
    "project_list",
    "sales_plan",
    "work_log",
    "project_task",
    "contact",
    "account_contact",
    "project_contact",
    "project_meddic",
    "ai_task_queue",
    "email_log",
    "agent_actions",
    "stakeholder_relation",
    "intel",
    "intel_org",
    # Nexus tables
    "nx_client",
    "nx_partner",
    "nx_contact",
    "nx_intel",
    "nx_tag",
    "nx_entity_tag",
    "nx_tbd_item",
    "nx_document",
    "nx_deal",
    "nx_deal_partner",
    "nx_deal_intel",
    "nx_meeting",
    "nx_reminder",
    "nx_file",
    "nx_intel_entity",
    "nx_intel_field",
    "nx_subsidy",
    "nx_subsidy_deadline",
    "nx_subsidy_deal",
]

# Columns that were TEXT in SQLite but are JSONB in PostgreSQL
JSONB_COLUMNS = {
    "crm": {"decision_maker", "champions"},
    "ai_task_queue": {"result_data"},
    "agent_actions": {"action_data"},
    "nx_intel": {"parsed_json", "chat_history"},
    "nx_deal": {"meddic_json"},
    "nx_meeting": {"participants_json"},
    "nx_file": {"parsed_json"},
}

# Columns that were INTEGER (0/1) in SQLite but are BOOLEAN in PostgreSQL
BOOLEAN_COLUMNS = {
    "nx_tbd_item": {"resolved"},
    "nx_reminder": {"resolved"},
    "project_task": {"is_next_action"},
    "sales_plan": {"prime_contractor"},
}

# Tables with SERIAL primary keys that need sequence sync
SERIAL_TABLES = {
    "project_list": "project_id",
    "sales_plan": "plan_id",
    "work_log": "log_id",
    "project_task": "task_id",
    "contact": "contact_id",
    "ai_task_queue": "task_id",
    "email_log": "email_id",
    "agent_actions": "action_id",
    "stakeholder_relation": "id",
    "intel": "id",
    "nx_client": "id",
    "nx_partner": "id",
    "nx_contact": "id",
    "nx_intel": "id",
    "nx_tag": "id",
    "nx_entity_tag": "id",
    "nx_tbd_item": "id",
    "nx_document": "id",
    "nx_deal": "id",
    "nx_deal_partner": "id",
    "nx_deal_intel": "id",
    "nx_meeting": "id",
    "nx_reminder": "id",
    "nx_file": "id",
    "nx_intel_entity": "id",
    "nx_intel_field": "id",
    "nx_subsidy": "id",
    "nx_subsidy_deadline": "id",
    "nx_subsidy_deal": "id",
}


def get_sqlite_tables(sqlite_conn: sqlite3.Connection) -> set[str]:
    """Get set of table names that exist in SQLite."""
    cur = sqlite_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    return {row[0] for row in cur.fetchall()}


def get_sqlite_columns(sqlite_conn: sqlite3.Connection, table: str) -> list[str]:
    """Get column names for a SQLite table."""
    cur = sqlite_conn.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cur.fetchall()]


def get_pg_columns(pg_conn, table: str) -> set[str]:
    """Get column names for a PostgreSQL table."""
    with pg_conn.cursor() as cur:
        cur.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = %s",
            (table,),
        )
        return {row[0] for row in cur.fetchall()}


def convert_value(table: str, column: str, value):
    """Convert a SQLite value to PostgreSQL-compatible value."""
    if value is None:
        return None

    # JSONB columns: parse JSON string to dict/list for psycopg2 adapter
    if column in JSONB_COLUMNS.get(table, set()):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        return value

    # Boolean columns: SQLite INTEGER 0/1 -> Python bool
    if column in BOOLEAN_COLUMNS.get(table, set()):
        return bool(value)

    return value


def migrate_table(
    sqlite_conn: sqlite3.Connection,
    pg_conn,
    table: str,
    pg_columns: set[str],
) -> int:
    """Migrate a single table. Returns row count."""
    sqlite_columns = get_sqlite_columns(sqlite_conn, table)

    # Only migrate columns that exist in both databases
    common_columns = [c for c in sqlite_columns if c in pg_columns]
    if not common_columns:
        print(f"  [SKIP] No common columns for {table}")
        return 0

    # Read all rows from SQLite
    col_list = ", ".join(common_columns)
    cur = sqlite_conn.execute(f"SELECT {col_list} FROM {table}")
    rows = cur.fetchall()

    if not rows:
        print(f"  [EMPTY] {table}: 0 rows")
        return 0

    # Convert values
    converted_rows = []
    for row in rows:
        converted = tuple(
            convert_value(table, col, val)
            for col, val in zip(common_columns, row)
        )
        converted_rows.append(converted)

    # Insert into PostgreSQL
    placeholders = ", ".join(["%s"] * len(common_columns))
    insert_sql = (
        f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) "
        f"ON CONFLICT DO NOTHING"
    )

    with pg_conn.cursor() as pg_cur:
        # Register JSONB adapter for dicts
        psycopg2.extras.register_default_jsonb(pg_cur, globally=False)
        for row in converted_rows:
            try:
                pg_cur.execute(insert_sql, row)
            except Exception as e:
                print(f"  [ERROR] {table} row: {e}")
                pg_conn.rollback()
                raise

    pg_conn.commit()
    print(f"  [OK] {table}: {len(converted_rows)} rows")
    return len(converted_rows)


def sync_sequences(pg_conn):
    """Sync SERIAL sequences to max(id) + 1 for each table."""
    print("\n--- Syncing sequences ---")
    with pg_conn.cursor() as cur:
        for table, pk_col in SERIAL_TABLES.items():
            try:
                # Find the sequence name
                cur.execute(
                    "SELECT pg_get_serial_sequence(%s, %s)",
                    (table, pk_col),
                )
                row = cur.fetchone()
                if not row or not row[0]:
                    continue
                seq_name = row[0]

                cur.execute(f"SELECT MAX({pk_col}) FROM {table}")
                max_val = cur.fetchone()[0]
                if max_val is not None:
                    cur.execute(f"SELECT setval(%s, %s)", (seq_name, max_val))
                    print(f"  [OK] {table}.{pk_col} sequence -> {max_val}")
            except Exception as e:
                print(f"  [WARN] {table}: {e}")
                pg_conn.rollback()

    pg_conn.commit()


def verify_counts(sqlite_conn: sqlite3.Connection, pg_conn):
    """Compare row counts between SQLite and PostgreSQL."""
    print("\n--- Verification ---")
    mismatches = []
    sqlite_tables = get_sqlite_tables(sqlite_conn)

    with pg_conn.cursor() as cur:
        for table in TABLES:
            if table not in sqlite_tables:
                continue
            sqlite_count = sqlite_conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                pg_count = cur.fetchone()[0]
            except Exception:
                pg_count = "N/A"
                pg_conn.rollback()

            status = "OK" if sqlite_count == pg_count else "MISMATCH"
            if status == "MISMATCH":
                mismatches.append(table)
            print(f"  {table}: SQLite={sqlite_count} PG={pg_count} [{status}]")

    if mismatches:
        print(f"\n[WARN] Mismatches in: {', '.join(mismatches)}")
    else:
        print("\n[OK] All row counts match!")


def main():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    if not os.path.exists(SQLITE_PATH):
        print(f"ERROR: SQLite database not found at {SQLITE_PATH}")
        sys.exit(1)

    print(f"Source: {SQLITE_PATH}")
    print(f"Target: {database_url[:50]}...")
    print()

    # Connect to both databases
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    pg_conn = psycopg2.connect(database_url)

    sqlite_tables = get_sqlite_tables(sqlite_conn)

    # First, run schema on PostgreSQL
    schema_path = os.path.join(DB_DIR, "schema.sql")
    print("--- Initializing PostgreSQL schema ---")
    with pg_conn.cursor() as cur:
        with open(schema_path, "r") as f:
            cur.execute(f.read())
    pg_conn.commit()
    print("  [OK] Schema applied\n")

    # Migrate each table
    print("--- Migrating data ---")
    total_rows = 0
    for table in TABLES:
        if table not in sqlite_tables:
            print(f"  [SKIP] {table}: not in SQLite")
            continue

        pg_columns = get_pg_columns(pg_conn, table)
        if not pg_columns:
            print(f"  [SKIP] {table}: not in PostgreSQL")
            continue

        count = migrate_table(sqlite_conn, pg_conn, table, pg_columns)
        total_rows += count

    print(f"\nTotal rows migrated: {total_rows}")

    # Sync sequences
    sync_sequences(pg_conn)

    # Verify
    verify_counts(sqlite_conn, pg_conn)

    sqlite_conn.close()
    pg_conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
