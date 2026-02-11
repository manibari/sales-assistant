"""S15 Migration — Validate JSONB vs normalized contact data consistency.

Compares decision_maker/champions JSONB fields against normalized
contact + account_contact tables. Reports discrepancies but does NOT
drop JSONB columns (safe to keep as historical reference)."""

import json

from database.connection import get_connection


def _parse_json(val):
    if val is None:
        return None
    if isinstance(val, str):
        return json.loads(val)
    return val


def migrate():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT client_id, decision_maker, champions FROM crm ORDER BY client_id")
            rows = cur.fetchall()

            total = len(rows)
            ok = 0
            mismatches = []

            for client_id, dm_jsonb, ch_jsonb in rows:
                dm_raw = _parse_json(dm_jsonb)
                ch_raw = _parse_json(ch_jsonb)

                # Get normalized contacts
                cur.execute("""
                    SELECT c.name, ac.role
                    FROM contact c
                    JOIN account_contact ac ON c.contact_id = ac.contact_id
                    WHERE ac.client_id = %s
                    ORDER BY ac.role DESC, ac.sort_order
                """, (client_id,))
                norm_rows = cur.fetchall()

                norm_dm_names = [r[0] for r in norm_rows if r[1] == "decision_maker"]
                norm_ch_names = sorted([r[0] for r in norm_rows if r[1] == "champion"])

                jsonb_dm_name = (dm_raw.get("name", "") if isinstance(dm_raw, dict) else "") or ""
                jsonb_ch_names = sorted([
                    c.get("name", "") for c in (ch_raw if isinstance(ch_raw, list) else [])
                    if c.get("name")
                ])

                dm_match = (jsonb_dm_name == (norm_dm_names[0] if norm_dm_names else ""))
                ch_match = (jsonb_ch_names == norm_ch_names)

                if dm_match and ch_match:
                    ok += 1
                else:
                    mismatches.append({
                        "client_id": client_id,
                        "dm_match": dm_match,
                        "ch_match": ch_match,
                        "jsonb_dm": jsonb_dm_name,
                        "norm_dm": norm_dm_names[0] if norm_dm_names else "",
                        "jsonb_ch": jsonb_ch_names,
                        "norm_ch": norm_ch_names,
                    })

            print(f"\n[S15] JSONB vs Normalized Validation Report")
            print(f"{'='*50}")
            print(f"Total clients: {total}")
            print(f"Consistent:    {ok}")
            print(f"Mismatches:    {len(mismatches)}")

            if mismatches:
                print(f"\nMismatch details:")
                for m in mismatches:
                    print(f"  {m['client_id']}:")
                    if not m["dm_match"]:
                        print(f"    DM: JSONB='{m['jsonb_dm']}' vs Norm='{m['norm_dm']}'")
                    if not m["ch_match"]:
                        print(f"    Champions: JSONB={m['jsonb_ch']} vs Norm={m['norm_ch']}")
            else:
                print("\nAll data is consistent. JSONB columns can be safely ignored.")

            print(f"\nNote: JSONB columns NOT dropped (kept as historical reference).")


if __name__ == "__main__":
    migrate()
    print("\nS15 validation complete.")
