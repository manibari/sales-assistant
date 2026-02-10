"""Settings page — customize page headers."""

import streamlit as st

from components.sidebar import render_sidebar
from services import settings as settings_svc

render_sidebar()

st.header("設定")

# --- Header settings ---
st.subheader("頁面標題設定")

headers = settings_svc.get_all_headers()

HEADER_KEYS = [
    ("header_work_log", "工作日誌"),
    ("header_project", "專案管理"),
    ("header_annual_plan", "年度戰略"),
    ("header_sales_plan", "商機預測"),
    ("header_crm", "客戶管理"),
    ("header_pipeline", "業務漏斗"),
]

with st.form("settings_form"):
    new_values = {}
    for key, default_label in HEADER_KEYS:
        new_values[key] = st.text_input(
            default_label,
            value=headers.get(key, default_label),
            key=f"setting_{key}",
        )

    if st.form_submit_button("儲存"):
        for key, value in new_values.items():
            settings_svc.update_header(key, value)
        st.success("設定已儲存！")
        st.rerun()
