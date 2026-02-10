"""Shared sidebar component — reads page headers from app_settings."""

import streamlit as st

from services import settings


# Map of page file -> settings key (and fallback label)
_PAGE_LINKS = [
    ("pages/work_log.py", "header_work_log", "工作日誌"),
    ("pages/project.py", "header_project", "專案管理"),
    ("pages/annual_plan.py", "header_annual_plan", "年度戰略"),
    ("pages/sales_plan.py", "header_sales_plan", "商機預測"),
    ("pages/crm.py", "header_crm", "客戶管理"),
    ("pages/pipeline.py", "header_pipeline", "業務漏斗"),
    ("pages/settings.py", None, "設定"),
]


def render_sidebar():
    """Render the sidebar with dynamic headers from app_settings."""
    headers = settings.get_all_headers()

    with st.sidebar:
        st.title("SPMS")
        st.caption("B2B 業務與專案管理系統")
        st.divider()

        for path, key, fallback in _PAGE_LINKS:
            label = headers.get(key, fallback) if key else fallback
            try:
                st.page_link(path, label=label)
            except Exception:
                # Page not yet registered in st.navigation — skip silently
                pass
