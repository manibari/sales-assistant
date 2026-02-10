"""SPMS — Streamlit entry point."""

import streamlit as st

from database.connection import init_db
from services import settings

init_db()

headers = settings.get_all_headers()

pages = st.navigation([
    st.Page("pages/work_log.py", title=headers.get("header_work_log", "工作日誌"), default=True),
    st.Page("pages/annual_plan.py", title=headers.get("header_annual_plan", "產品策略管理")),
    st.Page("pages/presale.py", title=headers.get("header_presale", "案件管理")),
    st.Page("pages/presale_detail.py", title="案件詳情"),
    st.Page("pages/sales_plan.py", title=headers.get("header_sales_plan", "商機預測")),
    st.Page("pages/pipeline.py", title=headers.get("header_pipeline", "業務漏斗")),
    st.Page("pages/kanban.py", title="售前看板"),
    st.Page("pages/crm.py", title=headers.get("header_crm", "客戶管理")),
    st.Page("pages/postsale.py", title=headers.get("header_postsale", "專案管理")),
    st.Page("pages/postsale_detail.py", title="專案詳情"),
    st.Page("pages/post_closure.py", title=headers.get("header_post_closure", "已結案客戶")),
    st.Page("pages/search.py", title="全域搜尋"),
    st.Page("pages/settings.py", title="設定"),
])

pages.run()
