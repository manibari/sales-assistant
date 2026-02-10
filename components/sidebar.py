"""Shared sidebar component — reads page headers from app_settings."""

import streamlit as st

from services import settings


def render_sidebar():
    """Render the sidebar with dynamic headers from app_settings."""
    headers = settings.get_all_headers()

    with st.sidebar:
        st.title("SPMS")
        st.caption("B2B 業務與專案管理系統")
        st.divider()

        st.page_link("pages/work_log.py", label=headers.get("header_work_log", "工作日誌"))
        st.page_link("pages/project.py", label=headers.get("header_project", "專案管理"))
        st.page_link("pages/annual_plan.py", label=headers.get("header_annual_plan", "年度戰略"))
        st.page_link("pages/sales_plan.py", label=headers.get("header_sales_plan", "商機預測"))
        st.page_link("pages/crm.py", label=headers.get("header_crm", "客戶管理"))
        st.page_link("pages/pipeline.py", label=headers.get("header_pipeline", "業務漏斗"))
        st.page_link("pages/settings.py", label="設定")
