"""Work Log page — daily work record entry + log history viewer.
Supports project-level and client-level activities (S14)."""

import os
from datetime import date

import pandas as pd
import streamlit as st

from components.sidebar import render_sidebar
from constants import ACTION_TYPES, INACTIVE_STATUSES, STATUS_CODES
from services import crm as crm_svc
from services import intelligent_log as il_svc
from services import project as project_svc
from services import project_task as task_svc
from services import settings as settings_svc
from services import work_log as work_log_svc

render_sidebar()

headers = settings_svc.get_all_headers()
st.header(headers.get("header_work_log", "工作日誌"))

# S17: Quick Add popover for usability
all_projects = project_svc.get_all()
all_clients = crm_svc.get_all()

with st.popover("⚡️ 快速記錄"):
    with st.form("quick_add_form", clear_on_submit=True):
        quick_scope = st.radio("範圍", ["專案", "客戶"], horizontal=True, key="quick_scope")
        if quick_scope == "專案":
            active_projects = [p for p in all_projects if p["status_code"] not in INACTIVE_STATUSES]
            project_options = {p["project_id"]: f'[{p["status_code"]}] {p["project_name"]}' for p in active_projects}
            target_id = st.selectbox("選擇專案", options=list(project_options.keys()), format_func=lambda x: project_options[x], key="quick_project")
        else:
            client_options = {c["client_id"]: f'{c["client_id"]} — {c["company_name"]}' for c in all_clients}
            target_id = st.selectbox("選擇客戶", options=list(client_options.keys()), format_func=lambda x: client_options[x], key="quick_client")

        content = st.text_area("內容描述", key="quick_content")
        submitted = st.form_submit_button("送出")

        if submitted:
            if content and target_id:
                kwargs = {
                    "action_type": ACTION_TYPES[0],
                    "log_date": date.today(),
                    "content": content,
                    "duration_hours": 1.0,
                }
                if quick_scope == "專案":
                    kwargs["project_id"] = target_id
                else:
                    kwargs["client_id"] = target_id

                work_log_svc.create(**kwargs)
                st.success("快速記錄已新增！")
                st.rerun()
            else:
                st.warning("請選擇目標並填寫內容。")

# --- Today's tasks reminder ---
try:
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
except Exception:
    # Fail silently if DB is not ready (e.g., during first run)
    pass


tab_ai, tab_entry, tab_history = st.tabs(["🤖 AI 智慧記錄", "傳統模式", "日誌紀錄"])

# === Tab 1: AI Smart Log Entry (S18) ===
with tab_ai:
    if not os.getenv("GOOGLE_API_KEY"):
        st.error("⚠️ 未偵測到 GOOGLE_API_KEY！請在您的 `.env` 檔案中設定此環境變數以啟用 AI 功能。")
    else:
        st.info("輸入您的工作日誌，AI 會自動為您解析客戶、建立紀錄。")
        with st.form("ai_log_form"):
            text_input = st.text_area(
                "請輸入您的工作日誌文字...",
                height=150,
                placeholder="例如：今天拜訪桃園大眾捷運股份有限公司，討論關於車上冰水主機、轉轍器等議題..."
            )
            submitted = st.form_submit_button("🪄 執行 AI 記錄")

            if submitted and text_input:
                with st.spinner("AI 正在解析與記錄中..."):
                    try:
                        parsed_data = il_svc.parse_log_entry(text_input)
                        if not parsed_data or not parsed_data.get("company_name"):
                            st.error("AI 無法解析出有效的客戶名稱，請確認您的輸入內容。")
                        else:
                            company_name = parsed_data["company_name"]
                            client_id = crm_svc.find_or_create_client(company_name)

                            if not client_id:
                                st.error(f"無法為客戶 '{company_name}' 建立或找到對應的 ID。")
                            else:
                                work_log_svc.create(
                                    client_id=client_id,
                                    action_type=parsed_data.get("action_type", ACTION_TYPES[0]),
                                    log_date=date.today(),
                                    content=parsed_data.get("log_content", text_input),
                                    duration_hours=1.0, # Default duration
                                    source="ai"
                                )
                                st.success(f"AI 記錄成功！\n- 客戶：`{company_name}` (ID: `{client_id}`)\n- 活動已寫入工作日誌。")
                                st.balloons()
                                # Do not rerun, so user can see the success message
                    except Exception as e:
                        st.error(f"執行 AI 記錄時發生錯誤：{e}")


# === Tab 2: Entry form ===
with tab_entry:
    # Radio toggle: project vs client activity
    scope = st.radio(
        "活動類型",
        options=["專案活動", "客戶活動"],
        horizontal=True,
        key="entry_scope",
    )

    if scope == "專案活動":
        # --- Project activity (original flow) ---
        active_projects = [p for p in all_projects if p["status_code"] not in INACTIVE_STATUSES]

        if not active_projects:
            st.info("目前沒有活躍的專案。")
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
                    st.rerun()

    else:
        # --- Client activity (S14) ---
        if not all_clients:
            st.info("目前沒有客戶資料。")
        else:
            client_options = {
                c["client_id"]: f'{c["client_id"]} — {c["company_name"]}'
                for c in all_clients
            }

            with st.form("work_log_client_form", clear_on_submit=True):
                selected_client = st.selectbox(
                    "選擇客戶",
                    options=list(client_options.keys()),
                    format_func=lambda x: client_options[x],
                )
                col1, col2 = st.columns(2)
                with col1:
                    log_date = st.date_input("日期", value=date.today(), key="client_log_date")
                with col2:
                    duration = st.number_input("工時（小時）", min_value=0.5, value=1.0, step=0.5,
                                               key="client_duration")
                action_type = st.selectbox("工作類型", options=ACTION_TYPES, key="client_action")
                content = st.text_area("內容描述", height=120, key="client_content")

                submitted = st.form_submit_button("送出")
                if submitted:
                    work_log_svc.create(
                        client_id=selected_client,
                        action_type=action_type,
                        log_date=log_date,
                        content=content,
                        duration_hours=duration,
                    )
                    st.success("客戶活動日誌已送出！")
                    st.rerun()

    # Recent 5 logs
    st.subheader("最近 5 筆紀錄")
    recent = work_log_svc.get_recent(5)
    if recent:
        df = pd.DataFrame(recent)
        display_cols = ["log_id", "project_id", "client_id", "log_date", "action_type",
                        "content", "duration_hours"]
        st.dataframe(df[[c for c in display_cols if c in df.columns]], width="stretch")
    else:
        st.info("尚無工作日誌紀錄。")

# === Tab 3: Log history (all projects) ===
with tab_history:
    st.subheader("歷史紀錄查詢")
    history_scope = st.radio("查詢範圍", ["依專案", "依客戶"], horizontal=True, key="history_scope")
    logs = []

    if history_scope == "依專案":
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
    else: # By client
        if not all_clients:
            st.info("目前沒有任何客戶。")
        else:
            client_options = {c["client_id"]: f'{c["client_id"]} — {c["company_name"]}' for c in all_clients}
            history_id = st.selectbox(
                "選擇客戶",
                options=list(client_options.keys()),
                format_func=lambda x: client_options[x],
                key="history_client_select",
            )
            logs = work_log_svc.get_by_client(history_id)


    if logs:
        df = pd.DataFrame(logs)
        display_cols = ["log_id", "log_date", "action_type", "content", "duration_hours", "source"]
        st.dataframe(df[[c for c in display_cols if c in df.columns]], width="stretch")

        total_hours = sum(l["duration_hours"] for l in logs)
        st.markdown(f"**日誌筆數：** {len(logs)}　｜　**總工時：** {total_hours:.1f} 小時")
    else:
        st.info("尚無工作日誌紀錄。")
