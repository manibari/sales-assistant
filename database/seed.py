"""Seed script — load demo data for SPMS. Safe to run repeatedly (clears then re-inserts)."""

import sys
import os
from datetime import date, timedelta

# Ensure project root is in path when run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import init_db, get_connection


def seed():
    """Clear existing data and insert demo records."""
    init_db()

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Clear in FK-safe order
            cur.execute("DELETE FROM work_log")
            cur.execute("DELETE FROM sales_plan")
            cur.execute("DELETE FROM project_list")
            cur.execute("DELETE FROM crm")
            cur.execute("DELETE FROM annual_plan")
            # Reset sequences
            cur.execute("ALTER SEQUENCE project_list_project_id_seq RESTART WITH 1")
            cur.execute("ALTER SEQUENCE work_log_log_id_seq RESTART WITH 1")
            cur.execute("ALTER SEQUENCE sales_plan_plan_id_seq RESTART WITH 1")

            # --- 2 Products ---
            cur.execute("""
                INSERT INTO annual_plan (product_id, product_name, quota_fy26, strategy, target_industry) VALUES
                ('PROD-AI', 'AI 智能平台', 8000000, '主攻大型企業數位轉型，搭配 POC 驗證', '科技/金融'),
                ('PROD-SEC', '資安防護方案', 5000000, '鎖定合規需求產業，強調零信任架構', '金融/政府')
            """)

            # --- 3 Clients ---
            cur.execute("""
                INSERT INTO crm (client_id, company_name, industry, email, decision_maker, champion, contact_info) VALUES
                ('CLI-TSMC', '台積電', '半導體', 'wang@tsmc.com',
                 '{"name": "王副總", "title": "IT VP", "style": "數據驅動，重視 ROI"}',
                 '{"name": "林經理", "title": "IT Manager", "notes": "內部推動者，技術背景"}',
                 '03-5636688'),
                ('CLI-FUBON', '富邦金控', '金融', 'chen@fubon.com',
                 '{"name": "陳協理", "title": "數位長", "style": "創新導向，願意嘗試新技術"}',
                 '{"name": "張主任", "title": "資訊部主任", "notes": "負責技術評估"}',
                 '02-66366636'),
                ('CLI-ASUS', '華碩電腦', '科技', 'lee@asus.com',
                 '{"name": "李處長", "title": "CTO Office", "style": "技術深度，重視架構"}',
                 '{"name": "黃工程師", "title": "Senior Engineer", "notes": "POC 技術窗口"}',
                 '02-28943447')
            """)

            # --- 5 Projects (various statuses) ---
            cur.execute("""
                INSERT INTO project_list (project_name, client_id, product_id, status_code, status_updated_at, owner, priority) VALUES
                ('台積電 AI 客服導入案', 'CLI-TSMC', 'PROD-AI', 'S03', NOW() - INTERVAL '20 days', '業務一部-陳', 'High'),
                ('富邦金控資安升級案', 'CLI-FUBON', 'PROD-SEC', 'C01', NOW() - INTERVAL '5 days', '業務二部-李', 'High'),
                ('華碩 AI 研發助手 POC', 'CLI-ASUS', 'PROD-AI', 'T01', NOW() - INTERVAL '3 days', '業務一部-陳', 'Medium'),
                ('台積電資安合規案', 'CLI-TSMC', 'PROD-SEC', 'S01', NOW() - INTERVAL '1 day', '業務二部-李', 'Medium'),
                ('富邦 AI 風控系統', 'CLI-FUBON', 'PROD-AI', 'D03', NOW() - INTERVAL '60 days', '業務一部-陳', 'Low')
            """)

            # --- 10 Work Logs ---
            today = date.today()
            cur.execute("""
                INSERT INTO work_log (project_id, log_date, action_type, content, duration_hours) VALUES
                (1, %s, '會議', '與台積電 IT 部門進行需求訪談，確認 AI 客服導入範圍', 2.0),
                (1, %s, '提案', '準備 AI 客服方案簡報，包含架構圖與報價', 3.0),
                (1, %s, '郵件', '寄送正式提案書給王副總', 0.5),
                (2, %s, '會議', '富邦金控資安需求討論，確認零信任架構需求', 1.5),
                (2, %s, '提案', '準備資安防護方案與合規對照表', 2.0),
                (2, %s, '開發', '建立 POC 測試環境', 4.0),
                (3, %s, '會議', '華碩 AI 研發助手 kickoff meeting', 1.0),
                (3, %s, '開發', 'POC 環境建置與資料準備', 3.0),
                (4, %s, '郵件', '初次聯繫台積電資安部門', 0.5),
                (5, %s, '文件', '富邦 AI 風控系統驗收文件整理', 2.0)
            """, (
                today - timedelta(days=15),
                today - timedelta(days=12),
                today - timedelta(days=10),
                today - timedelta(days=8),
                today - timedelta(days=6),
                today - timedelta(days=4),
                today - timedelta(days=3),
                today - timedelta(days=2),
                today - timedelta(days=1),
                today - timedelta(days=30),
            ))

            # --- 3 Sales Plans ---
            cur.execute("""
                INSERT INTO sales_plan (project_id, product_id, expected_invoice_date, amount, confidence_level, prime_contractor, notes) VALUES
                (1, 'PROD-AI', %s, 2500000, 0.6, TRUE, '預計提案通過後 Q2 開票'),
                (2, 'PROD-SEC', %s, 1800000, 0.8, TRUE, '議價中，預計下月簽約開票'),
                (3, 'PROD-AI', %s, 500000, 0.3, FALSE, 'POC 階段，金額待確認')
            """, (
                today + timedelta(days=45),
                today + timedelta(days=20),
                today + timedelta(days=90),
            ))

    print("Seed data loaded successfully!")
    print("  - 2 products (annual_plan)")
    print("  - 3 clients (crm)")
    print("  - 5 projects (project_list)")
    print("  - 10 work logs (work_log)")
    print("  - 3 sales plans (sales_plan)")


if __name__ == "__main__":
    seed()
