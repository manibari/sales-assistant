"""Nexus project service — delivery projects created from won deals."""

from database.connection import get_connection, row_to_dict, rows_to_dicts

VALID_STATUSES = {"planning", "active", "completed", "paused"}


def create_project(
    deal_id: int,
    name: str,
    pm_id: int | None = None,
    csm_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    notes: str | None = None,
) -> dict:
    """Create a delivery project linked to a won deal. Client is derived from the deal."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_project
                   (deal_id, name, status, pm_id, csm_id,
                    start_date, end_date, notes)
                   VALUES (%s, %s, 'planning', %s, %s, %s, %s, %s)
                   RETURNING *""",
                (deal_id, name, pm_id, csm_id, start_date, end_date, notes),
            )
            return row_to_dict(cur)


def get_project(project_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT p.*,
                          d.client_id,
                          d.name AS deal_name,
                          c.name AS client_name,
                          pm.name AS pm_name,
                          csm.name AS csm_name
                   FROM nx_project p
                   JOIN nx_deal d ON d.id = p.deal_id
                   LEFT JOIN nx_client c ON c.id = d.client_id
                   LEFT JOIN nx_user pm ON pm.id = p.pm_id
                   LEFT JOIN nx_user csm ON csm.id = p.csm_id
                   WHERE p.id = %s""",
                (project_id,),
            )
            return row_to_dict(cur)


def get_project_by_deal(deal_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT p.*, d.client_id
                   FROM nx_project p
                   JOIN nx_deal d ON d.id = p.deal_id
                   WHERE p.deal_id = %s
                   ORDER BY p.created_at DESC LIMIT 1""",
                (deal_id,),
            )
            return row_to_dict(cur)


def list_projects(
    status: str | None = None,
    client_id: int | None = None,
    pm_id: int | None = None,
) -> list[dict]:
    clauses = []
    params: list = []
    if status is not None:
        clauses.append("p.status = %s")
        params.append(status)
    if client_id is not None:
        # Client is derived from deal, not stored on project
        clauses.append("d.client_id = %s")
        params.append(client_id)
    if pm_id is not None:
        clauses.append("p.pm_id = %s")
        params.append(pm_id)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT p.*,
                           d.client_id,
                           d.name AS deal_name,
                           c.name AS client_name,
                           pm.name AS pm_name,
                           csm.name AS csm_name
                    FROM nx_project p
                    JOIN nx_deal d ON d.id = p.deal_id
                    LEFT JOIN nx_client c ON c.id = d.client_id
                    LEFT JOIN nx_user pm ON pm.id = p.pm_id
                    LEFT JOIN nx_user csm ON csm.id = p.csm_id
                    {where}
                    ORDER BY p.created_at DESC""",
                params,
            )
            return rows_to_dicts(cur)


def update_project(
    project_id: int,
    status: str | None = None,
    pm_id: int | None = None,
    csm_id: int | None = None,
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
    if pm_id is not None:
        fields.append("pm_id = %s")
        params.append(pm_id)
    if csm_id is not None:
        fields.append("csm_id = %s")
        params.append(csm_id)
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


def get_project_members(project_id: int) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT pm.*, u.name AS user_name, u.email AS user_email
                   FROM nx_project_member pm
                   JOIN nx_user u ON u.id = pm.user_id
                   WHERE pm.project_id = %s
                   ORDER BY pm.created_at ASC""",
                (project_id,),
            )
            return rows_to_dicts(cur)


def add_project_member(project_id: int, user_id: int) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_project_member (project_id, user_id)
                   VALUES (%s, %s)
                   ON CONFLICT (project_id, user_id) DO NOTHING
                   RETURNING *""",
                (project_id, user_id),
            )
            row = row_to_dict(cur)
            if not row:
                # Already existed — fetch it
                cur.execute(
                    "SELECT * FROM nx_project_member WHERE project_id = %s AND user_id = %s",
                    (project_id, user_id),
                )
                row = row_to_dict(cur)
            return row


def remove_project_member(project_id: int, user_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM nx_project_member WHERE project_id = %s AND user_id = %s",
                (project_id, user_id),
            )
            return cur.rowcount > 0
