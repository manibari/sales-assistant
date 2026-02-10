"""Shared sidebar component — reads page headers from app_settings."""

import streamlit as st

from services import settings


# Grouped navigation: (section_label, [(page_path, settings_key, fallback)])
# section_label=None → standalone page (no header)
_NAV_SECTIONS = [
    (None, [("pages/work_log.py", "header_work_log", "工作日誌")]),
    ("年度戰略", [("pages/annual_plan.py", "header_annual_plan", "產品策略管理")]),
    ("售前管理", [
        ("pages/crm.py", "header_crm", "客戶管理"),
        ("pages/presale.py", "header_presale", "案件管理"),
        ("pages/sales_plan.py", "header_sales_plan", "商機預測"),
        ("pages/pipeline.py", "header_pipeline", "業務漏斗"),
        ("pages/kanban.py", None, "售前看板"),
    ]),
    ("售後管理", [("pages/postsale.py", "header_postsale", "專案管理")]),
    ("客戶關係管理", [("pages/post_closure.py", "header_post_closure", "已結案客戶")]),
    (None, [("pages/search.py", None, "全域搜尋")]),
    (None, [("pages/settings.py", None, "設定")]),
]


def render_sidebar():
    """Render the sidebar with grouped navigation from app_settings."""
    # Hide st.navigation() default nav items (duplicates our custom sidebar)
    st.markdown(
        """<style>[data-testid="stSidebarNav"] {display: none;}</style>""",
        unsafe_allow_html=True,
    )

    headers = settings.get_all_headers()

    with st.sidebar:
        st.title("SPMS")
        st.caption("B2B 業務與專案管理系統")

        first = True
        for section_label, pages in _NAV_SECTIONS:
            # Divider between sections
            if first:
                st.divider()
                first = False
            else:
                st.divider()

            if section_label is None:
                # Standalone page — render directly
                for path, key, fallback in pages:
                    label = headers.get(key, fallback) if key else fallback
                    try:
                        st.page_link(path, label=label)
                    except Exception:
                        pass
            else:
                # Section with header
                st.markdown(f"**{section_label}**")
                multi = len(pages) > 1
                for path, key, fallback in pages:
                    label = headers.get(key, fallback) if key else fallback
                    # Indent sub-pages with full-width space for multi-page sections
                    display_label = f"\u3000{label}" if multi else label
                    try:
                        st.page_link(path, label=display_label)
                    except Exception:
                        pass
