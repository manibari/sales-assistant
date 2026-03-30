"""Nexus graph service — adjacency-list knowledge graph via nx_graph_edge."""

from database.connection import get_connection, row_to_dict, rows_to_dicts


def add_edge(
    from_type: str,
    from_id: int,
    to_type: str,
    to_id: int,
    relation: str,
    weight: float = 1.0,
) -> dict | None:
    """Insert a directed edge (upsert — returns None on conflict)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_graph_edge
                   (from_type, from_id, to_type, to_id, relation, weight)
                   VALUES (%s, %s, %s, %s, %s, %s)
                   ON CONFLICT (from_type, from_id, to_type, to_id, relation) DO NOTHING
                   RETURNING *""",
                (from_type, from_id, to_type, to_id, relation, weight),
            )
            return row_to_dict(cur)


def batch_add_edges(edges: list[dict]) -> int:
    """Bulk-insert edges. Each dict must have from_type, from_id, to_type, to_id, relation.
    Returns count of new edges inserted."""
    if not edges:
        return 0
    inserted = 0
    with get_connection() as conn:
        with conn.cursor() as cur:
            for e in edges:
                cur.execute(
                    """INSERT INTO nx_graph_edge
                       (from_type, from_id, to_type, to_id, relation, weight)
                       VALUES (%s, %s, %s, %s, %s, %s)
                       ON CONFLICT (from_type, from_id, to_type, to_id, relation) DO NOTHING""",
                    (
                        e["from_type"],
                        e["from_id"],
                        e["to_type"],
                        e["to_id"],
                        e["relation"],
                        e.get("weight", 1.0),
                    ),
                )
                inserted += cur.rowcount
    return inserted


def get_neighbors(node_type: str, node_id: int) -> list[dict]:
    """Return all nodes directly connected FROM this node."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT * FROM nx_graph_edge
                   WHERE from_type = %s AND from_id = %s
                   ORDER BY relation, to_type, to_id""",
                (node_type, node_id),
            )
            return rows_to_dicts(cur)


def get_reverse_neighbors(node_type: str, node_id: int) -> list[dict]:
    """Return all nodes that point TO this node."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT * FROM nx_graph_edge
                   WHERE to_type = %s AND to_id = %s
                   ORDER BY relation, from_type, from_id""",
                (node_type, node_id),
            )
            return rows_to_dicts(cur)


def get_client_subgraph(client_id: int) -> dict:
    """Return a client's full subgraph: all nodes 1 hop from the client.

    Returns:
        {
            "client_id": int,
            "deals": [edge, ...],
            "intel": [edge, ...],
            "knowledge": [edge, ...],
            "plans": [edge, ...],
            "other": [edge, ...],
        }
    """
    edges = get_neighbors("client", client_id)
    result: dict = {
        "client_id": client_id,
        "deals": [],
        "intel": [],
        "knowledge": [],
        "plans": [],
        "other": [],
    }
    for e in edges:
        t = e.get("to_type", "")
        if t == "deal":
            result["deals"].append(e)
        elif t == "intel":
            result["intel"].append(e)
        elif t == "knowledge":
            result["knowledge"].append(e)
        elif t == "plan":
            result["plans"].append(e)
        else:
            result["other"].append(e)
    return result
