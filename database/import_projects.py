"""Import 48 presale projects into SPMS.

Creates: 4 products, 46 new clients, 48 projects, work_log entries for projects with notes.
Safe to re-run: uses ON CONFLICT / checks for existing data.

Usage:
    python database/import_projects.py
"""

from datetime import date

from database.connection import get_connection, init_db

# ---------------------------------------------------------------------------
# 1. Products (annual_plan)
# ---------------------------------------------------------------------------
PRODUCTS = [
    ("TUKEY-PLATFORM", "Tukey Platform"),
    ("TUKEY-AGENT", "Tukey AI Agent"),
    ("TUKEY-SPARK", "Tukey / Spark : 影像辨識"),
    ("TUKEY-GPT", "Tukey GPT"),
]

# ---------------------------------------------------------------------------
# 2. New clients (crm) — CLI-035 onwards
# ---------------------------------------------------------------------------
NEW_CLIENTS = [
    ("CLI-035", "新應材"),
    ("CLI-036", "永進機械"),
    ("CLI-037", "合機電纜"),
    ("CLI-038", "工研院食研所"),
    ("CLI-039", "中科院光電所"),
    ("CLI-040", "邁達特"),
    ("CLI-041", "廣源造紙"),
    ("CLI-042", "中纖"),
    ("CLI-043", "Garmin"),
    ("CLI-044", "台電"),
    ("CLI-045", "順達科技"),
    ("CLI-046", "元太科技"),
    ("CLI-047", "展華"),
    ("CLI-048", "鵬鼎"),
    ("CLI-049", "漢翔"),
    ("CLI-050", "歐普仕"),
    ("CLI-051", "大陸生技客戶"),
    ("CLI-052", "明基材料"),
    ("CLI-053", "連展投控"),
    ("CLI-054", "遠東新"),
    ("CLI-055", "咖米"),
    ("CLI-056", "大毅科技"),
    ("CLI-057", "勝高"),
    ("CLI-058", "中糧科工"),
    ("CLI-059", "璨揚"),
    ("CLI-060", "中台興"),
    ("CLI-061", "加百裕"),
    ("CLI-062", "旺矽"),
    ("CLI-063", "南寶樹脂"),
    ("CLI-064", "空軍"),
    ("CLI-065", "和潤"),
    ("CLI-066", "慧國"),
    ("CLI-067", "致茂"),
    ("CLI-068", "聯電"),
    ("CLI-069", "聖暉"),
    ("CLI-070", "新普科技"),
    ("CLI-071", "佳世達"),
    ("CLI-072", "資勇"),
    ("CLI-073", "SDP"),
    ("CLI-074", "101大樓"),
    ("CLI-075", "群光電"),
    ("CLI-076", "中華電"),
    ("CLI-077", "東聯"),
    ("CLI-078", "喬山工程"),
    ("CLI-079", "東聯化學"),
    ("CLI-080", "立積電子"),
]

# ---------------------------------------------------------------------------
# 3. Projects (project_list) — 48 records
#    (project_name, client_id, product_id, status_code,
#     sales_owner, presale_owner, channel, notes)
# ---------------------------------------------------------------------------
PROJECTS = [
    # --- L0 (7) ---
    ("202512_新應材_廠務節能", "CLI-035", None, "L0",
     "Darren Lee", "Peter Chang", "朋昶", None),
    ("202511_永進機械/ML平台導入", "CLI-036", "TUKEY-PLATFORM", "L0",
     "Darren Lee", "Peter Chang", "朋昶", None),
    ("202510_合機電纜", "CLI-037", "TUKEY-PLATFORM", "L0",
     "Darren Lee", "Peter Chang", "中華電", None),
    ("202507_眾志_中日合成化學/介面活性劑", "CLI-005", "TUKEY-PLATFORM", "L0",
     "Darren Lee", None, "眾志", None),
    ("202507_眾志_大立高分子/製程找台化製程成果", "CLI-002", None, "L0",
     "Darren Lee", None, "眾志", None),
    ("202507_眾志_工研院食研所/微生物發酵製程", "CLI-038", "TUKEY-PLATFORM", "L0",
     "Darren Lee", None, "眾志", None),
    ("202506_眾志_中科院光電所/", "CLI-039", "TUKEY-PLATFORM", "L0",
     "Darren Lee", None, "眾志", None),

    # --- L1 (15) ---
    ("202602_邁達特_缺藥預警系統", "CLI-040", None, "L1",
     "Darren Lee", "Peter Chang", None, "確認需求中"),
    ("202602_朋昶_廣源造紙_ML&AiAgent", "CLI-041", None, "L1",
     "Darren Lee", None, "朋昶", "確認需求"),
    ("202602_朋昶_中纖", "CLI-042", None, "L1",
     "Darren Lee", None, "朋昶", "確認之前拜訪內容"),
    ("202601_朋昶_Garmin_ML廠務議題", "CLI-043", None, "L1",
     "Darren Lee", "Peter Chang", "朋昶", "約訪中"),
    ("202602_台電_標案知識檢索Agent", "CLI-044", None, "L1",
     "Darren Lee", "Peter Chang", None, "確認時辰及Partner"),
    ("202602_朋昶_順達科技_ML&AiAgent", "CLI-045", None, "L1",
     "Darren Lee", "Wei", "朋昶", "約廠務介紹"),
    ("202601_朋昶_元太科技_廠務議題", "CLI-046", None, "L1",
     "Darren Lee", "Wei", "朋昶", "冰機先"),
    ("202601_朋昶_展華(Q3)", "CLI-047", None, "L1",
     "Darren Lee", None, "朋昶", "Q3 討論"),
    ("202601_朋昶_鵬鼎泰國廠(Q3)", "CLI-048", None, "L1",
     "Darren Lee", None, "朋昶", "Q3 討論"),
    ("202601_朋昶_漢翔_ML", "CLI-049", None, "L1",
     "Darren Lee", None, "朋昶", "約台中金組長"),
    ("202601_朋昶_歐普仕", "CLI-050", None, "L1",
     "Darren Lee", "Wei", "朋昶", "約流量計廠商介紹"),
    ("202601_朋昶_大陸生技客戶ML", "CLI-051", None, "L1",
     "Darren Lee", "Wei", "朋昶", "確認窗口後續會議時間"),
    ("202601_朋昶_明基材料_設備操作手冊 AI Agent", "CLI-052", None, "L1",
     "Darren Lee", "Wei", "朋昶", "提供資訊，年後約會議"),
    ("202601_連展投控_Edge AI_大陸廠", "CLI-053", None, "L1",
     "Darren Lee", "Peter Chang", "朋昶", "2/11約詹博拜訪"),
    ("202505_朋昶_遠東新/Tukey Platform 導入案 (Q2)", "CLI-054", "TUKEY-PLATFORM", "L1",
     "Darren Lee", "Peter Chang", "朋昶", "260401 - 合約更新日期"),

    # --- L2 (14) ---
    ("202602_咖米_客戶流失預測ML", "CLI-055", None, "L2",
     "Darren Lee", "Wei", None, "確認議題跟意願"),
    ("202602_朋昶_大毅科技_AiAgent", "CLI-056", None, "L2",
     "Darren Lee", "Peter Chang", "朋昶", "週四拜訪確認意願"),
    ("202601_勝高_AI Agent 維護合約", "CLI-057", None, "L2",
     "Darren Lee", "Peter Chang", "Direct Sales", None),
    ("202602_朋昶_中糧科工/設備＆廠務 Agent", "CLI-058", "TUKEY-PLATFORM", "L2",
     "Darren Lee", "Peter Chang", "朋昶", "2/2 First call 介紹"),
    ("202601_朋昶_璨揚", "CLI-059", None, "L2",
     "Darren Lee", None, "朋昶", "Q2 ML 半年約"),
    ("202601_Miki_中台興AIAgent(Q2)", "CLI-060", None, "L2",
     "Darren Lee", "Wei", "Miki", "提供簡報，確認內部立案時間"),
    ("202601_朋昶_加百裕", "CLI-061", "TUKEY-AGENT", "L2",
     "Darren Lee", "Peter Chang", "朋昶", "260126 介紹 AI Agent & 綠色競賽\n確認 Azure API Token"),
    ("202601_朋昶_旺矽", "CLI-062", None, "L2",
     "Darren Lee", None, "朋昶", "跟東亮確認下一步"),
    ("202601_南寶樹脂_量產製程時程優化", "CLI-063", "TUKEY-PLATFORM", "L2",
     "Darren Lee", "Wei", "Direct Sales", "確認POC資料"),
    ("202601_空軍_AI Agent + ML導入", "CLI-064", "TUKEY-AGENT", "L2",
     "Darren Lee", "Peter Chang", "Direct Sales", "260120 - ML 提案簡報撰寫"),
    ("202601_和潤_ML solution 導入(Q3)", "CLI-065", "TUKEY-PLATFORM", "L2",
     "Darren Lee", "Peter Chang", "Direct Sales", "2606 以後提供 ML solution"),
    ("202511_朋昶_慧國/煙霧偵測影像辨識", "CLI-066", "TUKEY-SPARK", "L2",
     "Darren Lee", "Peter Chang", "朋昶", "260124 - 確認是否要 POC"),
    ("202511_朋昶_致茂/PDF擷取&馬達PHM", "CLI-067", "TUKEY-PLATFORM", "L2",
     "Darren Lee", "Alberte-Chimes AI", "朋昶", "260124 - 確認是否立案"),
    ("202504_朋昶_聯電/Tukey Platform 導入案 (Q3)", "CLI-068", "TUKEY-PLATFORM", "L2",
     "Darren Lee", "cslin", "朋昶", "260601 - 合約更新日期"),

    # --- L3 (7) ---
    ("202602_朋昶_聖暉/廠務 AI Agent", "CLI-069", None, "L3",
     "Darren Lee", "Peter Chang", "朋昶", "260206 - Second call"),
    ("202601_朋昶_新普科技_ML & AIAgent", "CLI-070", None, "L3",
     "Darren Lee", "Wei", "朋昶", "1/27拜訪CIO"),
    ("202601_科勝_佳世達/桃園總部能源最佳化系統", "CLI-071", None, "L3",
     "Darren Lee", "Wei", "科勝", "確認目前數據及需求"),
    ("202601_朋昶_資勇/出貨單Agent辨識", "CLI-072", None, "L3",
     "Darren Lee", "Peter Chang", "朋昶", "260120 現場場勘\n260121 提案簡報"),
    ("202601_SDP_PHM 導入 & ML續約", "CLI-073", "TUKEY-PLATFORM", "L3",
     "Darren Lee", "Peter Chang", "朋昶", "260120 - SDP 廣州廠會議"),
    ("202601_朋昶_101大樓/ 智慧商場", "CLI-074", "TUKEY-PLATFORM", "L3",
     "Darren Lee", "Peter Chang", "朋昶", "260115 - First Call"),
    ("202511_朋昶(喬山)_群光電 FMCS& ML & AI Agent", "CLI-075", "TUKEY-PLATFORM", "L3",
     "Darren Lee", "Peter Chang", "朋昶", "2603 AutoML"),

    # --- L4 (2) ---
    ("202601_AI工具上架_Tukey GPT", "CLI-076", None, "L4",
     "Darren Lee", "Wei", "中華電", None),
    ("202511_亞灣_東聯電子級CO2配方優化", "CLI-077", None, "L4",
     "Darren Lee", "Wei", "Direct Sales", None),

    # --- L6 (3) ---
    ("202511_朋昶_喬山工程/ AI Agent 平台開發案", "CLI-078", "TUKEY-AGENT", "L6",
     "Darren Lee", "GP Hung", "朋昶", "1/28 內部啟動會議"),
    ("202511_中華電_東聯化學_美國關稅第一期", "CLI-079", "TUKEY-SPARK", "L6",
     "Darren Lee", "Wei", "中華電", None),
    ("202509_中華電_立積電子/AI 應用躍升", "CLI-080", "TUKEY-PLATFORM", "L6",
     "Darren Lee", "Peter Chang", "中華電",
     "等待通過審查中…不過要開始了\n260120 - 委員審查簡報\n260128 - 開始資料分析"),
]


def run():
    # Ensure schema is up-to-date (adds channel column if missing)
    init_db()

    with get_connection() as conn:
        with conn.cursor() as cur:
            # --- 1. Products ---
            for product_id, product_name in PRODUCTS:
                cur.execute(
                    """INSERT INTO annual_plan (product_id, product_name)
                       VALUES (%s, %s)
                       ON CONFLICT (product_id) DO NOTHING""",
                    (product_id, product_name),
                )
            print(f"✓ Products: {len(PRODUCTS)} upserted")

            # --- 2. Clients ---
            inserted_clients = 0
            for client_id, company_name in NEW_CLIENTS:
                cur.execute(
                    """INSERT INTO crm (client_id, company_name, data_year)
                       VALUES (%s, %s, 2026)
                       ON CONFLICT (client_id) DO NOTHING""",
                    (client_id, company_name),
                )
                if cur.rowcount > 0:
                    inserted_clients += 1
            print(f"✓ Clients: {inserted_clients} new / {len(NEW_CLIENTS)} total")

            # --- 3. Projects ---
            inserted_projects = 0
            project_ids = {}  # name → project_id (for work_log)
            for (name, client_id, product_id, status_code,
                 sales_owner, presale_owner, channel, notes) in PROJECTS:
                # Check if project already exists (by name + client)
                cur.execute(
                    "SELECT project_id FROM project_list WHERE project_name = %s AND client_id = %s",
                    (name, client_id),
                )
                existing = cur.fetchone()
                if existing:
                    project_ids[name] = existing[0]
                    continue

                cur.execute(
                    """INSERT INTO project_list
                       (project_name, client_id, product_id, status_code,
                        sales_owner, presale_owner, channel, priority)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, 'Medium')
                       RETURNING project_id""",
                    (name, client_id, product_id, status_code,
                     sales_owner, presale_owner, channel),
                )
                project_ids[name] = cur.fetchone()[0]
                inserted_projects += 1
            print(f"✓ Projects: {inserted_projects} new / {len(PROJECTS)} total")

            # --- 4. Work logs (for projects with notes) ---
            inserted_logs = 0
            today = date.today()
            for (name, client_id, product_id, status_code,
                 sales_owner, presale_owner, channel, notes) in PROJECTS:
                if not notes:
                    continue
                pid = project_ids.get(name)
                if not pid:
                    continue
                # Check if we already wrote a log for this project+content
                cur.execute(
                    "SELECT 1 FROM work_log WHERE project_id = %s AND content = %s",
                    (pid, notes),
                )
                if cur.fetchone():
                    continue
                cur.execute(
                    """INSERT INTO work_log
                       (project_id, log_date, action_type, content, duration_hours, source)
                       VALUES (%s, %s, '文件', %s, 0.5, 'import')""",
                    (pid, today, notes),
                )
                inserted_logs += 1
            print(f"✓ Work logs: {inserted_logs} entries")

    print("\n=== Import complete ===")


if __name__ == "__main__":
    run()
