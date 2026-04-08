"""Invoice service — create, read, and update invoices linked to deals/projects/SOW."""

from database.connection import get_connection, row_to_dict, rows_to_dicts

VALID_STATUSES = {"draft", "issued", "paid", "cancelled"}


def create_invoice(
    deal_id: int,
    client_id: int,
    invoice_no: str,
    amount: float,
    created_by: int,
    tax_rate: float = 0.05,
    currency: str = "TWD",
    issue_date: str | None = None,
    due_date: str | None = None,
    notes: str | None = None,
    project_id: int | None = None,
    sow_doc_id: int | None = None,
    milestone_index: int | None = None,
) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_invoice
                   (deal_id, client_id, invoice_no, amount, tax_rate, currency,
                    status, issue_date, due_date, notes, created_by,
                    project_id, sow_doc_id, milestone_index)
                   VALUES (%s, %s, %s, %s, %s, %s, 'draft', %s, %s, %s, %s, %s, %s, %s)
                   RETURNING *""",
                (deal_id, client_id, invoice_no, amount, tax_rate, currency,
                 issue_date, due_date, notes, created_by,
                 project_id, sow_doc_id, milestone_index),
            )
            return row_to_dict(cur)


def get_invoice(invoice_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT i.*,
                          c.name AS client_name,
                          d.name AS deal_name,
                          p.name AS project_name
                   FROM nx_invoice i
                   LEFT JOIN nx_client c ON c.id = i.client_id
                   LEFT JOIN nx_deal d ON d.id = i.deal_id
                   LEFT JOIN nx_project p ON p.id = i.project_id
                   WHERE i.id = %s""",
                (invoice_id,),
            )
            return row_to_dict(cur)


def list_invoices(
    deal_id: int | None = None,
    client_id: int | None = None,
    project_id: int | None = None,
    status: str | None = None,
) -> list[dict]:
    clauses: list[str] = []
    params: list = []
    if deal_id is not None:
        clauses.append("i.deal_id = %s")
        params.append(deal_id)
    if client_id is not None:
        clauses.append("i.client_id = %s")
        params.append(client_id)
    if project_id is not None:
        clauses.append("i.project_id = %s")
        params.append(project_id)
    if status is not None:
        clauses.append("i.status = %s")
        params.append(status)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT i.*,
                           c.name AS client_name,
                           d.name AS deal_name,
                           p.name AS project_name
                    FROM nx_invoice i
                    LEFT JOIN nx_client c ON c.id = i.client_id
                    LEFT JOIN nx_deal d ON d.id = i.deal_id
                    LEFT JOIN nx_project p ON p.id = i.project_id
                    {where}
                    ORDER BY i.created_at DESC""",
                params,
            )
            return rows_to_dicts(cur)


def update_invoice(
    invoice_id: int,
    status: str | None = None,
    paid_date: str | None = None,
    issue_date: str | None = None,
    due_date: str | None = None,
    notes: str | None = None,
    amount: float | None = None,
    invoice_no: str | None = None,
    currency: str | None = None,
) -> dict | None:
    fields: list[str] = []
    params: list = []

    if status is not None:
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}")
        fields.append("status = %s")
        params.append(status)
    if paid_date is not None:
        fields.append("paid_date = %s")
        params.append(paid_date)
    if issue_date is not None:
        fields.append("issue_date = %s")
        params.append(issue_date)
    if due_date is not None:
        fields.append("due_date = %s")
        params.append(due_date)
    if notes is not None:
        fields.append("notes = %s")
        params.append(notes)
    if amount is not None:
        fields.append("amount = %s")
        params.append(amount)
    if invoice_no is not None:
        fields.append("invoice_no = %s")
        params.append(invoice_no)
    if currency is not None:
        fields.append("currency = %s")
        params.append(currency)

    if not fields:
        return get_invoice(invoice_id)

    fields.append("updated_at = NOW()")
    params.append(invoice_id)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE nx_invoice SET {', '.join(fields)} WHERE id = %s RETURNING *",
                params,
            )
            return row_to_dict(cur)
