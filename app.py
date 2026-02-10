"""SPMS — Streamlit entry point."""

import streamlit as st

from database.connection import init_db

init_db()

pages = st.navigation([
    st.Page("pages/work_log.py", title="工作日誌", default=True),
    st.Page("pages/project.py", title="專案管理"),
    st.Page("pages/annual_plan.py", title="年度戰略"),
    st.Page("pages/sales_plan.py", title="商機預測"),
    st.Page("pages/crm.py", title="客戶管理"),
])

pages.run()
