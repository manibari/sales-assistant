"""Nexus document service — NDA/MOU tracking + file uploads."""

from database.connection import get_connection, row_to_dict, rows_to_dicts

# --- NDA/MOU Document Tracking ---


def get_all_documents() -> list[dict]:
    """Get all NDA/MOU documents with client names."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT d.*, c.name AS client_name
                   FROM nx_document d
                   JOIN nx_client c ON d.client_id = c.id
                   ORDER BY d.expiry_date ASC NULLS LAST""")
            return rows_to_dicts(cur)


def get_documents_by_client(client_id: int) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM nx_document WHERE client_id = %s ORDER BY doc_type",
                (client_id,),
            )
            return rows_to_dicts(cur)


def update_document(doc_id: int, **fields) -> dict | None:
    if not fields:
        return _get_document(doc_id)
    allowed = {"status", "sign_date", "expiry_date", "file_path", "notes"}
    filtered = {k: v for k, v in fields.items() if k in allowed}
    if not filtered:
        return _get_document(doc_id)
    set_clause = ", ".join(f"{k} = %s" for k in filtered)
    values = list(filtered.values()) + [doc_id]
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE nx_document SET {set_clause}, updated_at = NOW() WHERE id = %s RETURNING *",
                values,
            )
            return row_to_dict(cur)


def _get_document(doc_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM nx_document WHERE id = %s", (doc_id,))
            return row_to_dict(cur)


def get_expiring_documents(within_days: int = 30) -> list[dict]:
    """Get documents expiring within N days."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT d.*, c.name AS client_name
                   FROM nx_document d
                   JOIN nx_client c ON d.client_id = c.id
                   WHERE d.status = 'signed'
                     AND d.expiry_date IS NOT NULL
                     AND (d.expiry_date - CURRENT_DATE) <= %s
                     AND (d.expiry_date - CURRENT_DATE) > 0
                   ORDER BY d.expiry_date ASC""",
                (within_days,),
            )
            return rows_to_dicts(cur)


# --- File Uploads ---


def create_file(
    deal_id: int | None = None,
    file_type: str = "attachment",
    file_name: str = "",
    file_path: str = "",
    file_size: int | None = None,
    source_url: str | None = None,
    intel_id: int | None = None,
    client_id: int | None = None,
) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_file (deal_id, intel_id, client_id, file_type, file_name, file_path, file_size, source_url)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING *""",
                (
                    deal_id,
                    intel_id,
                    client_id,
                    file_type,
                    file_name,
                    file_path,
                    file_size,
                    source_url,
                ),
            )
            return row_to_dict(cur)


def get_files_by_deal(deal_id: int) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM nx_file WHERE deal_id = %s ORDER BY created_at DESC",
                (deal_id,),
            )
            return rows_to_dicts(cur)


def get_files_by_intel(intel_id: int) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM nx_file WHERE intel_id = %s ORDER BY created_at DESC",
                (intel_id,),
            )
            return rows_to_dicts(cur)


def update_file(file_id: int, **fields) -> dict | None:
    if not fields:
        return get_file(file_id)
    allowed = {"file_name", "file_type"}
    filtered = {k: v for k, v in fields.items() if k in allowed}
    if not filtered:
        return get_file(file_id)
    set_clause = ", ".join(f"{k} = %s" for k in filtered)
    values = list(filtered.values()) + [file_id]
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE nx_file SET {set_clause} WHERE id = %s RETURNING *",
                values,
            )
            return row_to_dict(cur)


def update_file_parse(
    file_id: int, parsed_json: str, parse_status: str = "parsed"
) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE nx_file SET parsed_json = %s, parse_status = %s
                   WHERE id = %s RETURNING *""",
                (parsed_json, parse_status, file_id),
            )
            return row_to_dict(cur)


def get_file(file_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM nx_file WHERE id = %s", (file_id,))
            return row_to_dict(cur)


def delete_file(file_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM nx_file WHERE id = %s", (file_id,))
            return cur.rowcount > 0


# --- Client-centric document queries ---


def get_files_by_client(client_id: int) -> list[dict]:
    """Get all files for a client: direct client_id + via deal.client_id."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT f.*, d.name AS deal_name
                   FROM nx_file f
                   LEFT JOIN nx_deal d ON f.deal_id = d.id
                   WHERE f.client_id = %s
                      OR (f.deal_id IS NOT NULL AND d.client_id = %s)
                   ORDER BY f.created_at DESC""",
                (client_id, client_id),
            )
            return rows_to_dicts(cur)


def get_clients_with_doc_summary() -> list[dict]:
    """Return all clients that have files or documents, with summary stats."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    c.id, c.name, c.industry,
                    -- project file count (direct + via deal)
                    (SELECT COUNT(*) FROM nx_file f
                     LEFT JOIN nx_deal d2 ON f.deal_id = d2.id
                     WHERE f.client_id = c.id OR d2.client_id = c.id
                    ) AS file_count,
                    -- contract doc count
                    (SELECT COUNT(*) FROM nx_document doc WHERE doc.client_id = c.id
                    ) AS contract_count,
                    -- NDA status
                    (SELECT doc.status FROM nx_document doc
                     WHERE doc.client_id = c.id AND doc.doc_type = 'nda'
                     ORDER BY doc.sign_date DESC NULLS LAST LIMIT 1
                    ) AS nda_status,
                    -- MOU status
                    (SELECT doc.status FROM nx_document doc
                     WHERE doc.client_id = c.id AND doc.doc_type = 'mou'
                     ORDER BY doc.sign_date DESC NULLS LAST LIMIT 1
                    ) AS mou_status,
                    -- earliest expiring contract
                    (SELECT MIN(doc.expiry_date) FROM nx_document doc
                     WHERE doc.client_id = c.id
                       AND doc.status = 'signed'
                       AND doc.expiry_date IS NOT NULL
                    ) AS earliest_expiry
                FROM nx_client c
                WHERE c.status = 'active'
                  AND (
                    EXISTS (SELECT 1 FROM nx_file f
                            LEFT JOIN nx_deal d2 ON f.deal_id = d2.id
                            WHERE f.client_id = c.id OR d2.client_id = c.id)
                    OR EXISTS (SELECT 1 FROM nx_document doc WHERE doc.client_id = c.id)
                    OR EXISTS (SELECT 1 FROM nx_deal d3 WHERE d3.client_id = c.id)
                  )
                ORDER BY c.name
            """)
            return rows_to_dicts(cur)
