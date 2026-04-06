"""Nexus project service — delivery projects created from won deals."""

from database.connection import get_connection, row_to_dict, rows_to_dicts

VALID_STATUSES = {"planning", "active", "completed", "paused"}


def create_project(
    deal_id: int,
    client_id: int,
    name: str,
    postsale_owner: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    notes: str | None = None,
) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_project
                   (deal_id, client_id, name, status, postsale_owner,
                    start_date, end_date, notes)
                   VALUES (%s, %s, %s, 'planning', %s, %s, %s, %s)
                   RETURNING *""",
                (deal_id, client_id, name, postsale_owner, start_date, end_date, notes),
            )
            return row_to_dict(cur)


def get_project(project_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM nx_project WHERE id = %s", (project_id,))
            return row_to_dict(cur)


def get_project_by_deal(deal_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM nx_project WHERE deal_id = %s ORDER BY created_at DESC LIMIT 1",
                (deal_id,),
            )
            return row_to_dict(cur)


def list_projects(
    status: str | None = None,
    client_id: int | None = None,
    postsale_owner: int | None = None,
) -> list[dict]:
    clauses = []
    params: list = []
    if status is not None:
        clauses.append("status = %s")
        params.append(status)
    if client_id is not None:
        clauses.append("client_id = %s")
        params.append(client_id)
    if postsale_owner is not None:
        clauses.append("postsale_owner = %s")
        params.append(postsale_owner)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT * FROM nx_project {where} ORDER BY created_at DESC",
                params,
            )
            return rows_to_dicts(cur)


def update_project(
    project_id: int,
    status: str | None = None,
    postsale_owner: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    notes: str | None = None,
    name: str | None = None,
) -> dict | None:
    fields: list[str] = []
    params: list = []

    if status is not None:
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}")
        fields.append("status = %s")
        params.append(status)
    if postsale_owner is not None:
        fields.append("postsale_owner = %s")
        params.append(postsale_owner)
    if start_date is not None:
        fields.append("start_date = %s")
        params.append(start_date)
    if end_date is not None:
        fields.append("end_date = %s")
        params.append(end_date)
    if notes is not None:
        fields.append("notes = %s")
        params.append(notes)
    if name is not None:
        fields.append("name = %s")
        params.append(name)

    if not fields:
        return get_project(project_id)

    fields.append("updated_at = NOW()")
    params.append(project_id)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE nx_project SET {', '.join(fields)} WHERE id = %s RETURNING *",
                params,
            )
            return row_to_dict(cur)
