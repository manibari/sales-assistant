"""Project service — CRUD + state machine + contact linking for project_list.
S31: Refactored connection management to prevent nested connections.
"""

import streamlit as st
import yaml
from constants import PRESALE_STATUS_CODES, POSTSALE_STATUS_CODES, VALID_TRANSITIONS
from database.connection import get_connection, read_sql_file
from services import meddic as meddic_svc

# --- Rule Loading (S27) ---
def _load_rules():
    """Loads business rules from the rules.yml file."""
    try:
        with open("rules.yml", "r", encoding="utf-8") as f:
            rules = yaml.safe_load(f)
            return rules.get("meddic_gate_rules", {})
    except FileNotFoundError:
        print("WARNING: rules.yml not found. MEDDIC gating will be disabled.")
        return {}

_MEDDIC_GATE_RULES = _load_rules()


def _check_meddic_gate(project_id: int, new_status: str):
    """
    Checks if the project meets the MEDDIC criteria to transition to the new status.
    Raises ValueError if the gate is not passed.
    """
    rule = _MEDDIC_GATE_RULES.get(new_status)
    if not rule:
        return # No gate for this status

    meddic_data = meddic_svc.get_by_project(project_id)
    if not meddic_data:
        meddic_data = {}

    missing_fields = [
        rule["label"] for field in rule["fields"] if not meddic_data.get(field)
    ]

    if missing_fields:
        raise ValueError(
            f"無法進入 {new_status} 狀態。請至 MEDDIC 分頁填寫以下項目：{', '.join(missing_fields)}"
        )


def create(project_name, client_id=None, product_id=None, status_code="L0",
           presale_owner=None, postsale_owner=None, sales_owner=None, priority="Medium",
           channel=None):
    """Public method to create a project. Manages its own connection."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            return _create(cur, project_name, client_id, product_id, status_code,
                           presale_owner, postsale_owner, sales_owner, priority, channel)


def find_or_create_project(client_id: str, project_name: str, status_code: str) -> int | None:
    """
    Finds a project by name for a given client. If not found, creates a new one.
    This function manages a single connection for the entire find-or-create transaction.
    Returns the project_id.
    """
    if not all([client_id, project_name, status_code]):
        return None

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Try to find an existing project with a similar name for this client
            cur.execute(
                "SELECT project_id FROM project_list WHERE client_id = %s AND project_name = %s",
                (client_id, project_name)
            )
            row = cur.fetchone()
            if row:
                return row[0]

            # If not found, create a new one using the internal function
            new_project_id = _create(
                cur,
                project_name=project_name,
                client_id=client_id,
                status_code=status_code,
                channel="direct sales" # Mark as created by AI
            )
            return new_project_id


@st.cache_data
def get_all():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM project_list ORDER BY project_id")
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_by_id(project_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM project_list WHERE project_id = %s", (project_id,))
            row = cur.fetchone()
            if row is None:
                return None
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))


def get_presale():
    """Get projects in pre-sale stages (L0-L7, LOST, HOLD)."""
    presale_codes = list(PRESALE_STATUS_CODES.keys()) + ["LOST", "HOLD"]
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM project_list WHERE status_code = ANY(%s) ORDER BY project_id",
                (presale_codes,),
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_postsale():
    """Get projects in post-sale stages (P0-P2)."""
    postsale_codes = list(POSTSALE_STATUS_CODES.keys())
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM project_list WHERE status_code = ANY(%s) ORDER BY project_id",
                (postsale_codes,),
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_closed():
    """Get projects in closed states (P2, LOST, HOLD) with client info."""
    closed_codes = ["P2", "LOST", "HOLD"]
    with get_connection() as conn:
        with conn.cursor() as cur:
            sql = read_sql_file("project_get_closed.sql")
            cur.execute(sql, (closed_codes,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def update(project_id, project_name, client_id, product_id,
           presale_owner, postsale_owner, priority, sales_owner=None, channel=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE project_list
                   SET project_name = %s, client_id = %s, product_id = %s,
                       presale_owner = %s, sales_owner = %s, postsale_owner = %s,
                       priority = %s, channel = %s, updated_at = NOW()
                   WHERE project_id = %s""",
                (project_name, client_id, product_id,
                 presale_owner, sales_owner, postsale_owner, priority, channel,
                 project_id),
            )


def delete(project_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM project_list WHERE project_id = %s", (project_id,))


def transition_status(project_id, new_status, force=False):
    """
    Transition project status.
    Raises ValueError if transition is illegal and force is False.
    If force is True, bypasses validation rules.
    """
    project = get_by_id(project_id)
    if project is None:
        raise ValueError(f"Project {project_id} not found")

    if not force:
        # 1. Check MEDDIC gate rules
        _check_meddic_gate(project_id, new_status)

        # 2. Check standard transition rules
        current = project["status_code"]
        allowed = VALID_TRANSITIONS.get(current, [])

        if new_status not in allowed:
            raise ValueError(
                f"無法從 {current} 轉換至 {new_status}. "
                f"允許的轉換: {allowed}"
            )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE project_list
                   SET status_code = %s, status_updated_at = NOW(), updated_at = NOW()
                   WHERE project_id = %s""",
                (new_status, project_id),
            )

            # Auto-chain: L7 (簽約) automatically transitions to P0 (售後規劃)
            if new_status == "L7":
                cur.execute(
                    """UPDATE project_list
                       SET status_code = 'P0', status_updated_at = NOW(), updated_at = NOW()
                       WHERE project_id = %s""",
                    (project_id,),
                )


def link_contact(project_id, contact_id, role="participant"):
    """Link a contact to a project."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO project_contact (project_id, contact_id, role)
                   VALUES (%s, %s, %s)
                   ON CONFLICT (project_id, contact_id) DO UPDATE SET role = %s""",
                (project_id, contact_id, role, role),
            )


def unlink_contact(project_id, contact_id):
    """Remove a contact from a project."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM project_contact WHERE project_id = %s AND contact_id = %s",
                (project_id, contact_id),
            )


def get_contacts(project_id):
    """Get all contacts linked to a project."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT c.*, pc.role
                   FROM contact c
                   JOIN project_contact pc ON c.contact_id = pc.contact_id
                   WHERE pc.project_id = %s
                   ORDER BY c.name""",
                (project_id,),
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

# --- Internal Helpers ---

def _create(cur, project_name, client_id=None, product_id=None, status_code="L0",
            presale_owner=None, postsale_owner=None, sales_owner=None, priority="Medium",
            channel=None):
    """Internal method to create a project using a provided cursor."""
    cur.execute(
        """INSERT INTO project_list
           (project_name, client_id, product_id, status_code,
            presale_owner, sales_owner, postsale_owner, priority, channel)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
           RETURNING project_id""",
        (project_name, client_id, product_id, status_code,
         presale_owner, sales_owner, postsale_owner, priority, channel),
    )
    return cur.fetchone()[0]
