"""Settings page — customize page headers + stage probability."""

import streamlit as st

from components.sidebar import render_sidebar
from constants import STATUS_CODES
from services import settings as settings_svc
from services import stage_probability as prob_svc

render_sidebar()

st.header("設定")

# --- Header settings ---
st.subheader("頁面標題設定")

headers = settings_svc.get_all_headers()

HEADER_KEYS = [
    ("header_work_log", "工作日誌"),
    ("header_presale", "案件管理"),
    ("header_postsale", "專案管理"),
    ("header_annual_plan", "產品策略管理"),
    ("header_sales_plan", "商機預測"),
    ("header_crm", "客戶管理"),
    ("header_pipeline", "業務漏斗"),
    ("header_post_closure", "已結案客戶"),
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

# --- Stage probability settings ---
st.divider()
st.subheader("階段機率設定")
st.caption("調整各階段的預設成交機率，用於業績預測加權計算。")

prob_rows = prob_svc.get_all()
if prob_rows:
    with st.form("prob_form"):
        new_probs = {}
        for row in prob_rows:
            code = row["status_code"]
            label = f"{code} {STATUS_CODES.get(code, '')}"
            new_probs[code] = st.slider(
                label,
                min_value=0.0, max_value=1.0,
                value=float(row["probability"]),
                step=0.05,
                key=f"prob_{code}",
            )

        if st.form_submit_button("儲存機率設定"):
            for code, prob in new_probs.items():
                prob_svc.update(code, prob)
            st.success("階段機率設定已儲存！")
            st.rerun()
else:
    st.info("尚無階段機率資料。請先執行 S11 遷移。")
