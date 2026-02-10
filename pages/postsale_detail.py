"""Postsale Project Detail page — task CRUD, Gantt chart, burndown chart."""

from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.sidebar import render_sidebar
from constants import STATUS_CODES, TASK_STATUSES
from services import annual_plan as ap_svc
from services import crm as crm_svc
from services import project as project_svc
from services import project_task as task_svc

render_sidebar()

# --- Read project_id from query params ---
project_id_str = st.query_params.get("project_id")
if not project_id_str:
    st.warning("未指定專案。請從售後管理頁面進入。")
    if st.button("← 返回專案列表"):
        st.switch_page("pages/postsale.py")
    st.stop()

project_id = int(project_id_str)
project = project_svc.get_by_id(project_id)
if not project:
    st.error(f"找不到專案 ID：{project_id}")
    if st.button("← 返回專案列表"):
        st.switch_page("pages/postsale.py")
    st.stop()

# === Header + metrics ===
st.header(project["project_name"])

client_map = {c["client_id"]: c["company_name"] for c in crm_svc.get_all()}
product_map = {p["product_id"]: p["product_name"] for p in ap_svc.get_all()}

col_status, col_client, col_product, col_owner, col_priority = st.columns(5)
col_status.metric("狀態", f'{project["status_code"]} {STATUS_CODES.get(project["status_code"], "")}')
col_client.metric("客戶", client_map.get(project.get("client_id"), project.get("client_id") or "—"))
col_product.metric("產品", product_map.get(project.get("product_id"), project.get("product_id") or "—"))
col_owner.metric("負責人", project.get("postsale_owner") or "—")
col_priority.metric("優先級", project.get("priority") or "—")

summary = task_svc.get_summary(project_id)
mcol1, mcol2, mcol3, mcol4 = st.columns(4)
mcol1.metric("總任務數", summary["total_tasks"])
mcol2.metric("已完成", summary["completed_tasks"])
mcol3.metric("預估工時", f'{summary["total_hours"]:.0f}h')
mcol4.metric("已完成工時", f'{summary["completed_hours"]:.0f}h')

st.divider()

# === Task CRUD ===
st.subheader("工作分解")

tasks = task_svc.get_by_project(project_id)
status_keys = list(TASK_STATUSES.keys())
status_labels = list(TASK_STATUSES.values())

tab_list, tab_add = st.tabs(["任務列表", "新增任務"])

with tab_list:
    if not tasks:
        st.info("尚無工作分項，請至「新增任務」頁籤建立。")
    else:
        # Display task table
        df = pd.DataFrame(tasks)
        display_cols = ["task_id", "task_name", "owner", "status",
                        "start_date", "end_date", "estimated_hours", "actual_hours"]
        df_display = df[[c for c in display_cols if c in df.columns]].copy()
        df_display["status"] = df_display["status"].map(TASK_STATUSES)
        st.dataframe(df_display, width="stretch")

        # Edit / Delete
        st.markdown("---")
        edit_options = {t["task_id"]: t["task_name"] for t in tasks}
        edit_task_id = st.selectbox(
            "選擇要編輯的任務",
            options=list(edit_options.keys()),
            format_func=lambda x: edit_options[x],
            key="detail_edit_select",
        )

        current_task = task_svc.get_by_id(edit_task_id)
        if current_task:
            with st.form("edit_task_form"):
                task_name = st.text_input("任務名稱", value=current_task["task_name"])
                c1, c2 = st.columns(2)
                with c1:
                    owner = st.text_input("負責人", value=current_task.get("owner") or "")
                with c2:
                    cur_idx = status_keys.index(current_task["status"]) if current_task["status"] in status_keys else 0
                    status = st.selectbox("狀態", options=status_keys,
                                          format_func=lambda x: TASK_STATUSES[x],
                                          index=cur_idx, key="edit_task_status")
                c3, c4 = st.columns(2)
                with c3:
                    due_date = st.date_input("到期日", value=current_task.get("due_date"),
                                              key="edit_due_date")
                with c4:
                    is_next_action = st.checkbox("標記為下一步行動",
                                                  value=bool(current_task.get("is_next_action")),
                                                  key="edit_next_action")
                c3b, c4b = st.columns(2)
                with c3b:
                    start_date = st.date_input("開始日期", value=current_task.get("start_date"),
                                               key="edit_start_date")
                with c4b:
                    end_date = st.date_input("結束日期", value=current_task.get("end_date"),
                                             key="edit_end_date")
                c5, c6, c7 = st.columns(3)
                with c5:
                    est_hours = st.number_input("預估工時", min_value=0.0, value=float(current_task["estimated_hours"]),
                                                step=1.0, key="edit_est_hours")
                with c6:
                    act_hours = st.number_input("實際工時", min_value=0.0, value=float(current_task["actual_hours"]),
                                                step=1.0, key="edit_act_hours")
                with c7:
                    sort_order = st.number_input("排序", min_value=0, value=current_task["sort_order"],
                                                 step=1, key="edit_sort_order")

                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.form_submit_button("儲存"):
                        task_svc.update(
                            task_id=edit_task_id,
                            task_name=task_name.strip(),
                            owner=owner or None,
                            status=status,
                            start_date=start_date,
                            end_date=end_date,
                            estimated_hours=est_hours,
                            actual_hours=act_hours,
                            sort_order=sort_order,
                            due_date=due_date,
                            is_next_action=is_next_action,
                        )
                        st.success("任務已更新。")
                        st.rerun()

            if st.button("刪除此任務", key="delete_task_btn", type="secondary"):
                task_svc.delete(edit_task_id)
                st.success("任務已刪除。")
                st.rerun()

with tab_add:
    with st.form("add_task_form", clear_on_submit=True):
        task_name = st.text_input("任務名稱")
        c1, c2 = st.columns(2)
        with c1:
            owner = st.text_input("負責人", key="add_owner")
        with c2:
            status = st.selectbox("狀態", options=status_keys,
                                  format_func=lambda x: TASK_STATUSES[x],
                                  key="add_status")
        c3, c4 = st.columns(2)
        with c3:
            due_date = st.date_input("到期日", value=None, key="add_due_date")
        with c4:
            is_next_action = st.checkbox("標記為下一步行動", key="add_next_action")
        c3b, c4b = st.columns(2)
        with c3b:
            start_date = st.date_input("開始日期", value=date.today(), key="add_start_date")
        with c4b:
            end_date = st.date_input("結束日期", value=date.today(), key="add_end_date")
        c5, c6, c7 = st.columns(3)
        with c5:
            est_hours = st.number_input("預估工時", min_value=0.0, value=8.0, step=1.0, key="add_est_hours")
        with c6:
            act_hours = st.number_input("實際工時", min_value=0.0, value=0.0, step=1.0, key="add_act_hours")
        with c7:
            sort_order = st.number_input("排序", min_value=0, value=0, step=1, key="add_sort_order")

        if st.form_submit_button("新增任務"):
            if task_name.strip():
                task_svc.create(
                    project_id=project_id,
                    task_name=task_name.strip(),
                    owner=owner or None,
                    status=status,
                    start_date=start_date,
                    end_date=end_date,
                    estimated_hours=est_hours,
                    actual_hours=act_hours,
                    sort_order=sort_order,
                    due_date=due_date,
                    is_next_action=is_next_action,
                )
                st.success(f"已新增任務：{task_name}")
                st.rerun()
            else:
                st.warning("請輸入任務名稱。")

st.divider()

# === Gantt Chart ===
st.subheader("甘特圖")

tasks_with_dates = [t for t in tasks if t.get("start_date") and t.get("end_date")]
if not tasks_with_dates:
    st.info("尚無具日期的任務，無法產生甘特圖。")
else:
    gantt_data = []
    for t in tasks_with_dates:
        gantt_data.append({
            "task_name": t["task_name"],
            "start_date": t["start_date"],
            "end_date": t["end_date"],
            "status": TASK_STATUSES.get(t["status"], t["status"]),
        })
    gantt_df = pd.DataFrame(gantt_data)

    color_map = {"規劃中": "#95a5a6", "進行中": "#3498db", "已完成": "#2ecc71"}
    fig = px.timeline(
        gantt_df, x_start="start_date", x_end="end_date",
        y="task_name", color="status",
        color_discrete_map=color_map,
        labels={"task_name": "任務", "status": "狀態"},
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(height=max(300, len(tasks_with_dates) * 50))
    st.plotly_chart(fig, width="stretch")

    tasks_no_dates = [t for t in tasks if not t.get("start_date") or not t.get("end_date")]
    if tasks_no_dates:
        names = ", ".join(t["task_name"] for t in tasks_no_dates)
        st.info(f"以下任務缺少日期，未顯示在甘特圖中：{names}")

st.divider()

# === Burndown Chart ===
st.subheader("燃盡圖")

if not tasks:
    st.info("尚無任務資料，無法產生燃盡圖。")
else:
    total_hours = float(summary["total_hours"])
    if total_hours == 0:
        st.info("總預估工時為 0，無法產生燃盡圖。")
    else:
        # Determine date range
        dated_tasks = [t for t in tasks if t.get("start_date") and t.get("end_date")]
        if not dated_tasks:
            st.info("尚無具日期的任務，無法產生燃盡圖。")
        else:
            min_date = min(t["start_date"] for t in dated_tasks)
            max_date = max(t["end_date"] for t in dated_tasks)
            today = date.today()

            # Ideal line: linear decrease from total_hours to 0
            total_days = (max_date - min_date).days
            if total_days <= 0:
                total_days = 1
            ideal_dates = [min_date, max_date]
            ideal_values = [total_hours, 0]

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=ideal_dates, y=ideal_values,
                mode="lines", name="理想進度",
                line=dict(dash="dash", color="#95a5a6"),
            ))

            # Actual line: total - cumulative completed hours, up to today
            completed_data = task_svc.get_completed_by_date(project_id)
            actual_dates = [min_date]
            actual_values = [total_hours]

            if completed_data:
                for row in completed_data:
                    d = row["completion_date"]
                    if d <= today:
                        actual_dates.append(d)
                        actual_values.append(total_hours - float(row["cumulative_hours"]))

            # Extend to today if needed
            if actual_dates[-1] < today and today <= max_date:
                actual_dates.append(today)
                actual_values.append(actual_values[-1])

            fig.add_trace(go.Scatter(
                x=actual_dates, y=actual_values,
                mode="lines+markers", name="實際進度",
                line=dict(color="#3498db"),
            ))

            fig.update_layout(
                xaxis_title="日期",
                yaxis_title="剩餘工時",
                height=400,
            )
            st.plotly_chart(fig, width="stretch")

st.divider()

# === Back button ===
if st.button("← 返回專案列表"):
    st.switch_page("pages/postsale.py")
