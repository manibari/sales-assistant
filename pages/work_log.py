"""Work Log page — daily work record entry + log history viewer."""

from datetime import date

import pandas as pd
import streamlit as st

from components.sidebar import render_sidebar
from constants import ACTION_TYPES, INACTIVE_STATUSES, STATUS_CODES
from services import project as project_svc
from services import project_task as task_svc
from services import settings as settings_svc
from services import work_log as work_log_svc

render_sidebar()

headers = settings_svc.get_all_headers()
st.header(headers.get("header_work_log", "工作日誌"))

# --- Today's tasks reminder ---
today_tasks = task_svc.get_upcoming(days=0)
if today_tasks:
    st.subheader("今日待辦提醒")
    for t in today_tasks:
        overdue = t["due_date"] < date.today()
        icon = ":red[逾期]" if overdue else ":orange[今日]"
        st.warning(
            f"{icon} **{t['task_name']}** — {t.get('project_name', '')} "
            f"（{t.get('owner') or '未指派'}，到期：{t['due_date']}）"
        )
    st.divider()

all_projects = project_svc.get_all()

tab_entry, tab_history = st.tabs(["填寫工作日誌", "日誌紀錄"])

# === Tab 1: Entry form (active projects only) ===
with tab_entry:
    active_projects = [p for p in all_projects if p["status_code"] not in INACTIVE_STATUSES]

    if not active_projects:
        st.info("目前沒有活躍的專案。請先至售前管理或售後管理頁面新增專案。")
    else:
        project_options = {
            p["project_id"]: f'[{p["status_code"]} {STATUS_CODES.get(p["status_code"], "")}] {p["project_name"]}'
            for p in active_projects
        }

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

    # Recent 5 logs
    st.subheader("最近 5 筆紀錄")
    recent = work_log_svc.get_recent(5)
    if recent:
        df = pd.DataFrame(recent)
        display_cols = ["log_id", "project_id", "log_date", "action_type", "content", "duration_hours"]
        st.dataframe(df[[c for c in display_cols if c in df.columns]], width="stretch")
    else:
        st.info("尚無工作日誌紀錄。")

# === Tab 2: Log history (all projects) ===
with tab_history:
    if not all_projects:
        st.info("目前沒有任何專案。")
    else:
        history_options = {
            p["project_id"]: f'[{p["status_code"]} {STATUS_CODES.get(p["status_code"], "")}] {p["project_name"]}'
            for p in all_projects
        }

        history_id = st.selectbox(
            "選擇專案",
            options=list(history_options.keys()),
            format_func=lambda x: history_options[x],
            key="history_project_select",
        )

        logs = work_log_svc.get_by_project(history_id)
        if logs:
            df = pd.DataFrame(logs)
            display_cols = ["log_id", "log_date", "action_type", "content", "duration_hours", "source"]
            st.dataframe(df[[c for c in display_cols if c in df.columns]], width="stretch")

            total_hours = sum(l["duration_hours"] for l in logs)
            st.markdown(f"**日誌筆數：** {len(logs)}　｜　**總工時：** {total_hours:.1f} 小時")
        else:
            st.info("該專案尚無工作日誌紀錄。")
