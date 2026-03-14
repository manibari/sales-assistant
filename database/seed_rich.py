"""Rich seed data for Nexus — multiple deals, meetings, reminders for UI testing."""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.connection import init_db, get_connection
from services.nexus.clients import create_client
from services.nexus.partners import create_partner
from services.nexus.contacts import create_contact
from services.nexus.intel import create_intel, confirm_intel
from services.nexus.deals import (
    create_deal, advance_stage, add_partner_to_deal,
    link_intel_to_deal, update_deal,
)
from services.nexus.calendar import create_meeting, create_reminder
from services.nexus.documents import create_file
from services.nexus.tags import create_tag, tag_entity
from services.nexus.tbd import create_tbd


def seed():
    print("Initializing database...")
    init_db()

    # Clear existing nx_ data for clean seed
    with get_connection() as conn:
        with conn.cursor() as cur:
            for table in [
                "nx_file", "nx_reminder", "nx_meeting", "nx_deal_intel",
                "nx_deal_partner", "nx_entity_tag", "nx_tbd_item", "nx_intel",
                "nx_document", "nx_deal", "nx_contact", "nx_tag",
                "nx_partner", "nx_client",
            ]:
                cur.execute(f"DELETE FROM {table}")
        conn.commit()
    print("Cleared existing data.")

    # --- Clients ---
    c1 = create_client("A 食品", industry="food", budget_range="100-500K")
    c2 = create_client("B 石化", industry="petrochemical", budget_range="1M+")
    c3 = create_client("C 半導體", industry="semiconductor", budget_range="500K-1M")
    c4 = create_client("D 製造", industry="manufacturing", budget_range="100-500K")
    print(f"Clients: {c1['name']}, {c2['name']}, {c3['name']}, {c4['name']}")

    # --- Partners ---
    p1 = create_partner("Vision 科技", trust_level="verified", team_size="10-50")
    p2 = create_partner("IoT 系統", trust_level="testing", team_size="1-10")
    p3 = create_partner("宏碁智雲", trust_level="core_team", team_size="50-200")
    p4 = create_partner("Delta Edge", trust_level="verified", team_size="10-50")
    print(f"Partners: {p1['name']}, {p2['name']}, {p3['name']}, {p4['name']}")

    # --- Contacts ---
    ct1 = create_contact("陳副廠長", org_type="client", org_id=c1["id"], title="副廠長", role="decision_maker")
    ct2 = create_contact("林工程師", org_type="partner", org_id=p1["id"], title="技術長", role="engineer")
    ct3 = create_contact("王經理", org_type="client", org_id=c2["id"], title="IT 經理", role="champion")
    ct4 = create_contact("張總監", org_type="client", org_id=c3["id"], title="技術總監", role="decision_maker")
    ct5 = create_contact("李副總", org_type="client", org_id=c4["id"], title="副總經理", role="economic_buyer")
    ct6 = create_contact("吳 PM", org_type="partner", org_id=p3["id"], title="專案經理", role="engineer")
    print(f"Contacts: {ct1['name']}, {ct2['name']}, {ct3['name']}, {ct4['name']}, {ct5['name']}, {ct6['name']}")

    # --- Tags ---
    t1 = create_tag("產線自動化", "pain_point")
    t2 = create_tag("影像辨識", "capability")
    t3 = create_tag("食品業", "industry")
    t4 = create_tag("能源管理", "pain_point")
    t5 = create_tag("IoT", "capability")
    tag_entity("client", c1["id"], t1["id"])
    tag_entity("client", c1["id"], t3["id"])
    tag_entity("client", c2["id"], t4["id"])
    tag_entity("partner", p1["id"], t2["id"])
    tag_entity("partner", p2["id"], t5["id"])

    # --- Intel ---
    i1 = create_intel(
        raw_input="A 食品陳副廠長提到今年重點是產線自動化，預算約 300K，希望先做 AOI。NDA 已簽。",
        input_type="text", source_contact_id=ct1["id"],
    )
    i1 = confirm_intel(i1["id"], json.dumps({
        "pain_points": ["產線自動化", "AOI"], "budget": "300K", "timeline": "今年",
    }))

    i2 = create_intel(
        raw_input="B 石化王經理希望導入能源監控系統，目前用 Excel 管理每月耗能，很痛苦。年底前要上線。",
        input_type="text", source_contact_id=ct3["id"],
    )
    i2 = confirm_intel(i2["id"], json.dumps({
        "pain_points": ["能源監控", "Excel 管理"], "budget": "1M+", "timeline": "年底",
    }))

    i3 = create_intel(
        raw_input="C 半導體張總監說他們明年 Q1 要更新 AOI 設備，正在評估供應商。預算 500K-800K。",
        input_type="text", source_contact_id=ct4["id"],
    )
    i3 = confirm_intel(i3["id"], json.dumps({
        "pain_points": ["AOI 設備更新"], "budget": "500K-800K", "timeline": "明年 Q1",
    }))

    i4 = create_intel(
        raw_input="D 製造李副總約下週三來看 demo，對 IoT 資料收集有興趣。團隊 4 人會來。",
        input_type="text", source_contact_id=ct5["id"],
    )

    i5 = create_intel(
        raw_input="宏碁智雲吳 PM 說他們最近拿到 Delta 的 edge computing 模組合作資格，可以一起提案。",
        input_type="text", source_contact_id=ct6["id"],
    )
    i5 = confirm_intel(i5["id"], json.dumps({
        "partner_update": "宏碁智雲 + Delta edge computing",
    }))

    print("Intel: 5 items (4 confirmed, 1 draft)")

    # --- TBDs ---
    create_tbd("確認 A 食品 ERP 系統版本", linked_type="client", linked_id=c1["id"], source="skip")
    create_tbd("確認是否需要 IoT 設備整合", linked_type="client", linked_id=c1["id"], source="meeting")
    create_tbd("B 石化 IT infra 現況", linked_type="client", linked_id=c2["id"], source="skip")
    create_tbd("C 半導體目前 AOI 供應商", linked_type="client", linked_id=c3["id"], source="meeting")
    create_tbd("D 製造 demo 環境確認", linked_type="client", linked_id=c4["id"], source="skip")
    print("TBDs: 5 items")

    # --- Deals ---
    today = datetime.now()

    # Deal 1: A 食品 — active, L2, some MEDDIC filled
    d1 = create_deal("A 食品 AOI 產線自動化", client_id=c1["id"], budget_range="100-500K", timeline="this_quarter", budget_amount=300000, budget_year=2026)
    advance_stage(d1["id"], "L1")
    advance_stage(d1["id"], "L2")
    meddic = {
        "metrics": "產線良率從 92% 提升到 97%",
        "economic_buyer": "陳副廠長 (已確認)",
        "decision_criteria": None,
        "decision_process": None,
        "identify_pain": "AOI 人工檢測效率低，每月 2 次漏檢",
        "champion": "陳副廠長",
    }
    update_deal(d1["id"], meddic_json=json.dumps(meddic))
    add_partner_to_deal(d1["id"], p1["id"], role="vision_provider")
    add_partner_to_deal(d1["id"], p3["id"], role="integration")
    link_intel_to_deal(d1["id"], i1["id"])
    # Make it idle for 10 days
    with get_connection() as conn:
        with conn.cursor() as cur:
            idle_date = (today - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
            cur.execute("UPDATE nx_deal SET last_activity_at = %s WHERE id = %s", (idle_date, d1["id"]))
        conn.commit()

    # Deal 2: B 石化 — L1, needs push (20 days idle)
    d2 = create_deal("B 石化能源監控平台", client_id=c2["id"], budget_range="1M+", timeline="this_year", budget_amount=1000000, budget_year=2026)
    advance_stage(d2["id"], "L1")
    meddic2 = {
        "metrics": None, "economic_buyer": None, "decision_criteria": None,
        "decision_process": None, "identify_pain": "Excel 管理耗能，效率極低",
        "champion": "王經理",
    }
    update_deal(d2["id"], meddic_json=json.dumps(meddic2))
    add_partner_to_deal(d2["id"], p2["id"], role="iot_provider")
    link_intel_to_deal(d2["id"], i2["id"])
    with get_connection() as conn:
        with conn.cursor() as cur:
            idle_date = (today - timedelta(days=20)).strftime("%Y-%m-%d %H:%M:%S")
            cur.execute("UPDATE nx_deal SET last_activity_at = %s WHERE id = %s", (idle_date, d2["id"]))
        conn.commit()

    # Deal 3: C 半導體 — L0, fresh
    d3 = create_deal("C 半導體 AOI 設備更新", client_id=c3["id"], budget_range="500K-1M", timeline="next_quarter", budget_amount=750000, budget_year=2026)
    link_intel_to_deal(d3["id"], i3["id"])

    # Deal 4: D 製造 — L1, recent activity
    d4 = create_deal("D 製造 IoT 資料收集 POC", client_id=c4["id"], budget_range="<100K", timeline="this_quarter", budget_amount=100000, budget_year=2026)
    advance_stage(d4["id"], "L1")
    add_partner_to_deal(d4["id"], p4["id"], role="edge_computing")
    link_intel_to_deal(d4["id"], i4["id"])

    # Deal 5: Closed deal
    d5 = create_deal("E 電子 MES 整合", client_id=c1["id"], budget_range="500K-1M", timeline="this_year", budget_amount=750000, budget_year=2026)
    advance_stage(d5["id"], "L1")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE nx_deal SET status = 'closed', stage = 'closed' WHERE id = %s",
                (d5["id"],),
            )
        conn.commit()

    print("Deals: d1(L2), d2(L1 idle), d3(L0), d4(L1), d5(closed)")

    # --- Meetings ---
    today_str = today.strftime("%Y-%m-%d")
    tomorrow_str = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    next_week_str = (today + timedelta(days=5)).strftime("%Y-%m-%d")

    create_meeting(d1["id"], "A 食品 — 技術方案討論", f"{today_str}T14:00:00",
                   json.dumps([{"id": ct1["id"], "name": ct1["name"]}]))
    create_meeting(d4["id"], "D 製造 — IoT Demo", f"{tomorrow_str}T10:00:00",
                   json.dumps([{"id": ct5["id"], "name": ct5["name"]}]))
    create_meeting(d2["id"], "B 石化 — 能源監控需求訪談", f"{next_week_str}T15:00:00",
                   json.dumps([{"id": ct3["id"], "name": ct3["name"]}]))
    print("Meetings: 3 (today, tomorrow, next week)")

    # --- Reminders ---
    create_reminder(today_str, "A 食品已 10 天未聯繫，需推進", "push", d1["id"])
    create_reminder(today_str, "B 石化已 20 天未聯繫，緊急", "push", d2["id"])
    create_reminder(tomorrow_str, "準備 D 製造 demo 環境", "prep", d4["id"])
    create_reminder((today + timedelta(days=3)).strftime("%Y-%m-%d"),
                    "跟進 C 半導體報價", "follow_up", d3["id"])
    print("Reminders: 4 (2 today, 1 tomorrow, 1 in 3 days)")

    # --- Files ---
    create_file(d1["id"], "proposal", "A食品_AOI方案_v2.pptx", "/uploads/a_food_aoi_v2.pptx",
                source_url="https://drive.google.com/file/d/abc123")
    create_file(d1["id"], "contract", "A食品_NDA_signed.pdf", "/uploads/a_food_nda.pdf")
    create_file(d2["id"], "proposal", "B石化_能源監控_概念書.pdf", "/uploads/b_petro_energy.pdf",
                source_url="https://drive.google.com/file/d/def456")
    create_file(d4["id"], "attachment", "D製造_場地照片.zip", "/uploads/d_mfg_photos.zip")
    # Mark one as parsed
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE nx_file SET parse_status = 'parsed' WHERE file_name LIKE '%NDA%'")
        conn.commit()
    print("Files: 4 (1 parsed)")

    print("\n=== RICH SEED COMPLETE ===")
    print("  4 clients, 4 partners, 6 contacts")
    print("  5 intel, 5 TBDs, 5 deals (1 closed)")
    print("  3 meetings, 4 reminders, 4 files")


if __name__ == "__main__":
    seed()
