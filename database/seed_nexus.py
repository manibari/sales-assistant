"""Seed data for Nexus Engine 1 — verifies schema + service layer end-to-end."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.connection import init_db
from services.nexus.clients import create_client, get_all_clients
from services.nexus.partners import create_partner, get_all_partners
from services.nexus.contacts import create_contact
from services.nexus.intel import create_intel, confirm_intel
from services.nexus.deals import (
    create_deal, get_deal, advance_stage, add_partner_to_deal,
    link_intel_to_deal, get_deals_by_urgency, get_meddic_progress,
)
from services.nexus.calendar import create_meeting, create_reminder
from services.nexus.documents import get_documents_by_client, create_file
from services.nexus.tags import create_tag, tag_entity, get_entity_tags
from services.nexus.tbd import create_tbd, get_open_tbds


def seed():
    print("Initializing database...")
    init_db()

    # --- Clients ---
    print("\n--- Creating clients ---")
    c1 = create_client("A 食品", industry="food", budget_range="100-500K")
    c2 = create_client("B 石化", industry="petrochemical", budget_range="1M+")
    print(f"  Created: {c1['name']} (id={c1['id']}), {c2['name']} (id={c2['id']})")

    # Check auto-created NDA/MOU
    docs = get_documents_by_client(c1["id"])
    print(f"  Auto-created docs for {c1['name']}: {[d['doc_type'] for d in docs]}")
    assert len(docs) == 2, f"Expected 2 docs, got {len(docs)}"

    # --- Partners ---
    print("\n--- Creating partners ---")
    p1 = create_partner("Vision 科技", trust_level="verified", team_size="10-50")
    p2 = create_partner("IoT 系統", trust_level="testing", team_size="1-10")
    print(f"  Created: {p1['name']} (trust={p1['trust_level']}), {p2['name']} (trust={p2['trust_level']})")

    # --- Contacts ---
    print("\n--- Creating contacts ---")
    ct1 = create_contact("陳副廠長", org_type="client", org_id=c1["id"], title="副廠長", role="decision_maker")
    ct2 = create_contact("林工程師", org_type="partner", org_id=p1["id"], title="技術長", role="engineer")
    print(f"  Created: {ct1['name']} ({ct1['org_type']}), {ct2['name']} ({ct2['org_type']})")

    # --- Tags ---
    print("\n--- Creating tags ---")
    t1 = create_tag("能源效率", "pain_point")
    t2 = create_tag("影像辨識", "capability")
    t3 = create_tag("食品業", "industry")
    tag_entity("client", c1["id"], t1["id"])
    tag_entity("client", c1["id"], t3["id"])
    tag_entity("partner", p1["id"], t2["id"])
    client_tags = get_entity_tags("client", c1["id"])
    print(f"  Tags for {c1['name']}: {[t['name'] for t in client_tags]}")

    # --- Intel ---
    print("\n--- Creating intel ---")
    i1 = create_intel(
        raw_input="A 食品陳副廠長提到今年重點是產線自動化，預算約 300K，希望先做 AOI",
        input_type="text",
        source_contact_id=ct1["id"],
    )
    i1 = confirm_intel(i1["id"], json.dumps({
        "pain_points": ["產線自動化", "AOI"],
        "budget": "300K",
        "timeline": "今年",
    }))
    print(f"  Intel #{i1['id']}: status={i1['status']}")

    # --- TBD ---
    print("\n--- Creating TBDs ---")
    create_tbd("確認 A 食品 ERP 系統", linked_type="client", linked_id=c1["id"], source="skip")
    create_tbd("確認是否需要 IoT 設備", linked_type="client", linked_id=c1["id"], source="meeting")
    open_tbds = get_open_tbds("client", c1["id"])
    print(f"  Open TBDs for {c1['name']}: {len(open_tbds)}")

    # --- Deal ---
    print("\n--- Creating deal ---")
    d1 = create_deal("A 食品 AOI 產線自動化", client_id=c1["id"], budget_range="100-500K", timeline="this_quarter")
    print(f"  Deal: {d1['name']} (stage={d1['stage']})")

    # Add partner to deal
    add_partner_to_deal(d1["id"], p1["id"], role="vision_provider")
    print(f"  Added partner: {p1['name']}")

    # Link intel to deal
    link_intel_to_deal(d1["id"], i1["id"])
    print(f"  Linked intel #{i1['id']}")

    # Check MEDDIC
    meddic = get_meddic_progress(d1["id"])
    print(f"  MEDDIC: {meddic['completed']}/{meddic['total']} (missing: {meddic['missing']})")

    # Advance stage
    advance_stage(d1["id"], "L1")
    deal = get_deal(d1["id"])
    print(f"  Advanced to: {deal['stage']}")

    # --- Meeting ---
    print("\n--- Creating meeting ---")
    m1 = create_meeting(
        deal_id=d1["id"],
        title="A 食品 — AOI 需求訪談",
        meeting_date="2026-03-15T14:00:00",
        participants_json=json.dumps([{"id": ct1["id"], "name": ct1["name"]}]),
    )
    print(f"  Meeting: {m1['title']} on {m1['meeting_date']}")

    # --- Reminder ---
    print("\n--- Creating reminder ---")
    r1 = create_reminder(
        due_date="2026-03-12",
        content="A 食品已 14 天未聯繫",
        reminder_type="push",
        deal_id=d1["id"],
    )
    print(f"  Reminder: {r1['content']} due {r1['due_date']}")

    # --- File ---
    print("\n--- Creating file ---")
    f1 = create_file(
        deal_id=d1["id"],
        file_type="proposal",
        file_name="A食品_AOI方案_v1.pptx",
        file_path="/uploads/a_food_aoi_v1.pptx",
        source_url="https://drive.google.com/file/d/xxx",
    )
    print(f"  File: {f1['file_name']} (parse_status={f1['parse_status']})")

    # --- Full deal detail ---
    print("\n--- Full deal detail ---")
    full = get_deal(d1["id"])
    print(f"  Deal: {full['name']}")
    print(f"  Client: {full['client_name']}")
    print(f"  Stage: {full['stage']}")

    # --- Pipeline view ---
    print("\n--- Pipeline (urgency view) ---")
    deals = get_deals_by_urgency()
    for deal in deals:
        print(f"  {deal['name']} | stage={deal['stage']} | idle={deal.get('idle_days', 0)} days")

    # --- Summary ---
    print("\n=== SEED COMPLETE ===")
    print(f"  Clients: {len(get_all_clients())}")
    print(f"  Partners: {len(get_all_partners())}")
    print(f"  Deals: {len(deals)}")
    print("  All tables verified working.\n")


if __name__ == "__main__":
    seed()
