"""Work Log page — daily work record entry + log history viewer.
Supports project-level and client-level activities (S14).
S29: Refactored for asynchronous AI task processing.
"""

from datetime import date

import pandas as pd
import streamlit as st

from components.sidebar import render_sidebar
from constants import ACTION_TYPES, INACTIVE_STATUSES, STATUS_CODES
from services import crm as crm_svc
from services import project as project_svc
from services import project_task as task_svc
from services import settings as settings_svc
from services import work_log as work_log_svc
from services import task_queue as task_queue_svc
from services.ai_provider import check_ai_available

render_sidebar()

headers = settings_svc.get_all_headers()
st.header(headers.get("header_work_log", "工作日誌"))

# --- Data loading ---
# These are cached in the service layer (S26)
all_projects = project_svc.get_all()
all_clients = crm_svc.get_all()

# --- Quick Add Popover ---
with st.popover("⚡️ 快速手動記錄"):
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
                kwargs = {"action_type": ACTION_TYPES[0], "log_date": date.today(), "content": content, "duration_hours": 1.0}
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
            st.warning(f"{icon} **{t['task_name']}** — {t.get('project_name', '')} （{t.get('owner') or '未指派'}，到期：{t['due_date']}）")
        st.divider()
except Exception as e:
    st.error(f"載入今日待辦時發生錯誤：{e}")

# --- Main Tabs ---
tab_ai, tab_queue, tab_entry, tab_history = st.tabs(["🤖 AI 智慧記錄", "AI 任務佇列", "傳統手動模式", "歷史日誌紀錄"])

# === AI Smart Log Entry (S18/S29) ===
with tab_ai:
    ai_ok, ai_msg = check_ai_available()
    if not ai_ok:
        st.error(f"⚠️ {ai_msg}　AI 功能已停用。")
        with st.expander("🔑 如何設定 AI Provider？"):
            st.markdown("""
**在 `.env` 中設定 `AI_PROVIDER` 及對應的金鑰，然後重新啟動應用程式。**

| Provider | `AI_PROVIDER` | 必要環境變數 |
|---|---|---|
| Google Gemini（預設） | `gemini` | `GOOGLE_API_KEY` |
| Azure OpenAI | `azure_openai` | `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_KEY`, `AZURE_OPENAI_DEPLOYMENT` |
| Anthropic Claude | `anthropic` | `ANTHROPIC_API_KEY` |
            """)
    else:
        st.info("輸入您的工作日誌，AI 將在背景為您解析客戶、建立紀錄與專案。")
        with st.form("ai_log_form"):
            text_input = st.text_area("請貼上您的工作日誌文字...", height=200, placeholder="例如：今天拜訪桃園大眾捷運股份有限公司...")
            submitted = st.form_submit_button("✅ 提交至 AI 佇列")
            if submitted and text_input:
                task_id = task_queue_svc.create_task(text_input)
                st.success(f"AI 任務 #{task_id} 已成功提交！您可至「AI 任務佇列」分頁查看進度。")
                st.rerun()

# === AI Task Queue (S29) ===
with tab_queue:
    st.subheader("AI 任務佇列")
    if st.button("手動刷新"):
        st.rerun()
    
    tasks = task_queue_svc.get_recent_tasks()
    if not tasks:
        st.info("目前沒有正在執行的 AI 任務。")
    else:
        status_map = {"pending": "處理中", "completed": "✅ 已完成", "failed": "❌ 失敗"}
        for t in tasks:
            t["status_display"] = status_map.get(t["status"], t["status"])
        
        df = pd.DataFrame(tasks)
        df_display = df[["task_id", "status_display", "created_at", "processed_at", "raw_text", "error_message"]]
        df_display = df_display.rename(columns={"task_id": "任務ID", "status_display": "狀態", "created_at": "提交時間", "processed_at": "處理時間", "raw_text": "原始內容", "error_message": "錯誤訊息"})
        st.dataframe(df_display, width="stretch")

# === Manual Entry Form ===
with tab_entry:
    scope = st.radio("活動類型", ["專案活動", "客戶活動"], horizontal=True, key="entry_scope")
    if scope == "專案活動":
        active_projects = [p for p in all_projects if p["status_code"] not in INACTIVE_STATUSES]
        if not active_projects:
            st.info("目前沒有活躍的專案。")
        else:
            project_options = {p["project_id"]: f'[{p["status_code"]} {STATUS_CODES.get(p["status_code"], "")}] {p["project_name"]}' for p in active_projects}
            with st.form("work_log_form", clear_on_submit=True):
                # Form fields...
                selected_id = st.selectbox("選擇專案", options=list(project_options.keys()), format_func=lambda x: project_options[x])
                col1, col2 = st.columns(2)
                with col1:
                    log_date = st.date_input("日期", value=date.today())
                with col2:
                    duration = st.number_input("工時（小時）", min_value=0.5, value=1.0, step=0.5)
                action_type = st.selectbox("工作類型", options=ACTION_TYPES)
                content = st.text_area("內容描述", height=120)
                if st.form_submit_button("送出"):
                    work_log_svc.create(project_id=selected_id, action_type=action_type, log_date=log_date, content=content, duration_hours=duration)
                    st.success("工作日誌已送出！")
                    st.rerun()
    else: # Client activity
        if not all_clients:
            st.info("目前沒有客戶資料。")
        else:
            client_options = {c["client_id"]: f'{c["client_id"]} — {c["company_name"]}' for c in all_clients}
            with st.form("work_log_client_form", clear_on_submit=True):
                # Form fields...
                selected_client = st.selectbox("選擇客戶", options=list(client_options.keys()), format_func=lambda x: client_options[x])
                col1, col2 = st.columns(2)
                with col1:
                    log_date = st.date_input("日期", value=date.today(), key="client_log_date")
                with col2:
                    duration = st.number_input("工時（小時）", min_value=0.5, value=1.0, step=0.5, key="client_duration")
                action_type = st.selectbox("工作類型", options=ACTION_TYPES, key="client_action")
                content = st.text_area("內容描述", height=120, key="client_content")
                if st.form_submit_button("送出"):
                    work_log_svc.create(client_id=selected_client, action_type=action_type, log_date=log_date, content=content, duration_hours=duration)
                    st.success("客戶活動日誌已送出！")
                    st.rerun()

# === Log History ===
with tab_history:
    st.subheader("歷史紀錄查詢")
    history_scope = st.radio("查詢範圍", ["依專案", "依客戶"], horizontal=True, key="history_scope")
    logs = []
    # Logic to fetch and display logs...
    if history_scope == "依專案":
        if all_projects:
            history_options = {p["project_id"]: f'[{p["status_code"]}] {p["project_name"]}' for p in all_projects}
            history_id = st.selectbox("選擇專案", options=list(history_options.keys()), format_func=lambda x: history_options[x], key="history_project_select")
            logs = work_log_svc.get_by_project(history_id)
    else: # By client
        if all_clients:
            client_options = {c["client_id"]: f'{c["client_id"]} — {c["company_name"]}' for c in all_clients}
            history_id = st.selectbox("選擇客戶", options=list(client_options.keys()), format_func=lambda x: client_options[x], key="history_client_select")
            logs = work_log_svc.get_by_client(history_id)
    
    if logs:
        df = pd.DataFrame(logs)
        display_cols = ["log_id", "log_date", "action_type", "content", "duration_hours", "source"]
        st.dataframe(df[[c for c in display_cols if c in df.columns]], width="stretch")
        total_hours = sum(l["duration_hours"] for l in logs)
        st.markdown(f"**日誌筆數：** {len(logs)}　｜　**總工時：** {total_hours:.1f} 小時")
    else:
        st.info("尚無工作日誌紀錄。")
