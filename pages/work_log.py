"""Work Log page — daily work record entry."""

from datetime import date

import pandas as pd
import streamlit as st

from components.sidebar import render_sidebar
from constants import ACTION_TYPES, INACTIVE_STATUSES
from services import project as project_svc
from services import settings as settings_svc
from services import work_log as work_log_svc

render_sidebar()

headers = settings_svc.get_all_headers()
st.header(headers.get("header_work_log", "工作日誌"))

# --- Project selector (filter inactive) ---
all_projects = project_svc.get_all()
active_projects = [p for p in all_projects if p["status_code"] not in INACTIVE_STATUSES]

if not active_projects:
    st.info("目前沒有活躍的專案。請先至專案管理頁面新增專案。")
else:
    project_options = {
        p["project_id"]: f'[{p["status_code"]}] {p["project_name"]}'
        for p in active_projects
    }

    # --- Work log form ---
    with st.form("work_log_form", clear_on_submit=True):
        selected_id = st.selectbox(
            "選擇專案",
            options=list(project_options.keys()),
            format_func=lambda x: project_options[x],
        )
        col1, col2 = st.columns(2)
        with col1:
            log_date = st.date_input("日期", value=date.today())
        with col2:
            duration = st.number_input("工時（小時）", min_value=0.5, value=1.0, step=0.5)
        action_type = st.selectbox("工作類型", options=ACTION_TYPES)
        content = st.text_area("內容描述", height=120)

        submitted = st.form_submit_button("送出")
        if submitted:
            work_log_svc.create(
                project_id=selected_id,
                action_type=action_type,
                log_date=log_date,
                content=content,
                duration_hours=duration,
            )
            st.success("工作日誌已送出！")

# --- Recent 5 logs ---
st.subheader("最近 5 筆紀錄")
recent = work_log_svc.get_recent(5)
if recent:
    df = pd.DataFrame(recent)
    display_cols = ["log_id", "project_id", "log_date", "action_type", "content", "duration_hours"]
    st.dataframe(df[[c for c in display_cols if c in df.columns]], use_container_width=True)
else:
    st.info("尚無工作日誌紀錄。")
