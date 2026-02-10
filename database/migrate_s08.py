"""S08 migration — add header_post_closure setting, update default labels."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection


def migrate():
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Add new header_post_closure setting
            cur.execute("""
                INSERT INTO app_settings (key, value)
                VALUES ('header_post_closure', '已結案客戶')
                ON CONFLICT (key) DO NOTHING
            """)

            # Update defaults only if user hasn't customised them
            cur.execute("""
                UPDATE app_settings SET value = '案件管理'
                WHERE key = 'header_presale' AND value = '售前管理'
            """)
            cur.execute("""
                UPDATE app_settings SET value = '專案管理'
                WHERE key = 'header_postsale' AND value = '售後管理'
            """)
            cur.execute("""
                UPDATE app_settings SET value = '產品策略管理'
                WHERE key = 'header_annual_plan' AND value = '年度戰略'
            """)

    print("S08 migration complete.")
    print("  - Added header_post_closure setting")
    print("  - Updated default labels (presale→案件管理, postsale→專案管理, annual_plan→產品策略管理)")


if __name__ == "__main__":
    migrate()
