"""Presale Project Detail page — metrics, contacts, sales plan, timeline, tasks, status transition."""

from datetime import date

import pandas as pd
import streamlit as st

from components.sidebar import render_sidebar
from constants import (
    CONTACT_ROLES,
    DEFAULT_STAGE_PROBABILITIES,
    PRESALE_TRANSITIONS,
    STATUS_CODES,
    TASK_STATUSES,
)
from services import annual_plan as ap_svc
from services import contact as contact_svc
from services import crm as crm_svc
from services import meddic as meddic_svc
from services import project as project_svc
from services import project_task as task_svc
from services import sales_plan as sp_svc
from services import stage_probability as prob_svc
from services import work_log as wl_svc

render_sidebar()

# --- Read project_id from query params ---
project_id_str = st.query_params.get("project_id")
if not project_id_str:
    st.warning("未指定專案。請從案件管理頁面進入。")
    if st.button("← 返回案件列表"):
        st.switch_page("pages/presale.py")
    st.stop()

project_id = int(project_id_str)
project = project_svc.get_by_id(project_id)
if not project:
    st.error(f"找不到專案 ID：{project_id}")
    if st.button("← 返回案件列表"):
        st.switch_page("pages/presale.py")
    st.stop()

# === Header + metrics ===
st.header(project["project_name"])

client_map = {c["client_id"]: c["company_name"] for c in crm_svc.get_all()}
product_map = {p["product_id"]: p["product_name"] for p in ap_svc.get_all()}

col_status, col_client, col_product, col_owner, col_priority, col_channel = st.columns(6)

# --- Editable Status (S23/S25 Refactor) ---
with col_status:
    all_status_options = list(PRESALE_STATUS_CODES.keys()) + ["LOST", "HOLD"]
    current_status = project["status_code"]
    try:
        current_status_index = all_status_options.index(current_status)
    except ValueError:
        current_status_index = 0

    new_status = st.selectbox(
        "狀態",
        options=all_status_options,
        index=current_status_index,
        format_func=lambda x: f"{x} {STATUS_CODES.get(x, '')}",
        key="presale_detail_status_selector"
    )
    
    force_transition = st.checkbox("強制轉換 (繞過規則)", key="force_transition_cb", help="勾選此項以繞過 MEDDIC 關卡和標準流程限制，直接變更狀態。")
    
    if st.button("更新狀態", key="update_status_btn"):
        try:
            project_svc.transition_status(project_id, new_status, force=force_transition)
            st.toast(f"狀態已成功更新為: {new_status}", icon="✅")
            st.rerun()
        except ValueError as e:
            st.error(str(e))

col_client.metric("客戶", client_map.get(project.get("client_id"), project.get("client_id") or "—"))
col_product.metric("產品", product_map.get(project.get("product_id"), project.get("product_id") or "—"))
col_owner.metric("售前負責人", project.get("presale_owner") or "—")
col_priority.metric("優先級", project.get("priority") or "—")
col_channel.metric("通路", project.get("channel") or "—")

# Stage probability metric
current_prob = prob_svc.get_by_code(project["status_code"])
if current_prob is None:
    current_prob = DEFAULT_STAGE_PROBABILITIES.get(project["status_code"], 0.5)
st.metric("階段機率", f"{current_prob:.0%}")

st.divider()

# === Tabs ===
tab_meddic, tab_contacts, tab_sales, tab_timeline, tab_tasks = st.tabs(
    ["MEDDIC", "關聯聯絡人", "商機預測", "活動時間軸", "任務管理"]
)

# --- Tab 0: MEDDIC (S25) ---
with tab_meddic:
    st.subheader("MEDDIC 分析")
    
    meddic_data = meddic_svc.get_by_project(project_id) or {}

    with st.form("meddic_form"):
        metrics = st.text_area("Metrics (量化指標)", value=meddic_data.get("metrics", ""), height=100, help="客戶希望達成的量化效益，例如：提升 20% 產能、降低 15% 成本")
        economic_buyer = st.text_area("Economic Buyer (經濟決策者)", value=meddic_data.get("economic_buyer", ""), height=100, help="最終有預算簽字權的人是誰？他的主要考量是什麼？")
        decision_criteria = st.text_area("Decision Criteria (決策標準)", value=meddic_data.get("decision_criteria", ""), height=100, help="客戶用什麼具體標準來評估供應商？（技術、價格、品牌、服務...）")
        decision_process = st.text_area("Decision Process (決策流程)", value=meddic_data.get("decision_process", ""), height=100, help="客戶內部的採購流程、時程、及參與者有誰？")
        identify_pain = st.text_area("Identify Pain (痛點)", value=meddic_data.get("identify_pain", ""), height=100, help="他們現在具體遇到了什麼困難？這個困難對他們的業務造成了什麼影響？")
        champion = st.text_area("Champion (擁護者)", value=meddic_data.get("champion", ""), height=100, help="我們在客戶內部的「自己人」是誰？他能為我們帶來什麼資訊或影響力？")

        submitted = st.form_submit_button("儲存 MEDDIC 分析")
        if submitted:
            meddic_svc.save_or_update(
                project_id=project_id,
                metrics=metrics,
                economic_buyer=economic_buyer,
                decision_criteria=decision_criteria,
                decision_process=decision_process,
                identify_pain=identify_pain,
                champion=champion,
            )
            st.success("MEDDIC 分析已儲存！")
            st.rerun()

# --- Tab 1: Linked contacts ---
with tab_contacts:
    st.subheader("此案件的聯絡人")

    linked_contacts = project_svc.get_contacts(project_id)
    if linked_contacts:
        for c in linked_contacts:
            with st.container():
                cc1, cc2, cc3, cc4 = st.columns([2, 2, 2, 1])
                cc1.write(f"**{c['name']}**（{c.get('title') or '—'}）")
                cc2.write(c.get("email") or "—")
                cc3.write(f"角色：{c['role']}")
                with cc4:
                    if st.button("移除", key=f"unlink_{c['contact_id']}"):
                        project_svc.unlink_contact(project_id, c["contact_id"])
                        st.rerun()
    else:
        st.info("尚未關聯聯絡人。")

    # Add contact: show contacts from this client
    st.markdown("---")
    st.markdown("**新增關聯聯絡人**")

    client_id = project.get("client_id")
    if client_id:
        available = contact_svc.get_by_client(client_id)
        linked_ids = {c["contact_id"] for c in linked_contacts}
        unlinked = [c for c in available if c["contact_id"] not in linked_ids]

        if unlinked:
            contact_options = {c["contact_id"]: f"{c['name']}（{c.get('title') or '—'}）" for c in unlinked}
            sel_contact = st.selectbox(
                "從客戶聯絡人中選擇",
                options=list(contact_options.keys()),
                format_func=lambda x: contact_options[x],
                key="link_contact_select",
            )
            sel_role = st.selectbox("角色", options=CONTACT_ROLES, key="link_contact_role")
            if st.button("關聯"):
                project_svc.link_contact(project_id, sel_contact, role=sel_role)
                st.success("已關聯聯絡人。")
                st.rerun()
        else:
            st.info("此客戶的所有聯絡人已全部關聯。")
    else:
        st.info("此案件尚未指定客戶，無法選擇聯絡人。")

# --- Tab 2: Sales plan ---
with tab_sales:
    st.subheader("商機預測")

    plans = sp_svc.get_all()
    project_plans = [p for p in plans if p["project_id"] == project_id]

    if project_plans:
        df = pd.DataFrame(project_plans)
        display_cols = ["plan_id", "expected_invoice_date", "amount", "confidence_level", "prime_contractor", "notes"]
        st.dataframe(df[[c for c in display_cols if c in df.columns]], width="stretch")

        # Show stage probability comparison
        for p in project_plans:
            manual_weighted = float(p["amount"]) * float(p["confidence_level"])
            stage_weighted = float(p["amount"]) * current_prob
            st.caption(
                f"商機 #{p['plan_id']}：手動加權 ${manual_weighted:,.0f} ｜ 階段機率加權 ${stage_weighted:,.0f}"
            )

        # Sync button
        st.markdown("---")
        if st.button("同步為階段機率", help="將此案件所有商機的信心指數更新為目前階段機率"):
            for p in project_plans:
                sp_svc.update(
                    plan_id=p["plan_id"],
                    project_id=p["project_id"],
                    product_id=p["product_id"],
                    expected_invoice_date=p["expected_invoice_date"],
                    amount=p["amount"],
                    confidence_level=current_prob,
                    prime_contractor=p["prime_contractor"],
                    notes=p["notes"],
                )
            st.success(f"已將 {len(project_plans)} 筆商機信心指數同步為 {current_prob:.0%}")
            st.rerun()
    else:
        st.info("此案件尚無商機預測。請至商機預測頁面新增。")

# --- Tab 3: Activity timeline ---
with tab_timeline:
    st.subheader("活動時間軸")

    logs = wl_svc.get_by_project(project_id)
    if logs:
        for log in logs:
            with st.container():
                col_date, col_content = st.columns([1, 4])
                col_date.markdown(f"**{log['log_date']}**")
                col_content.markdown(
                    f":blue[{log['action_type']}] {log.get('content') or '—'}　"
                    f"（{log['duration_hours']}h）"
                )
    else:
        st.info("此案件尚無工作紀錄。請至工作日誌頁面新增。")

# --- Tab 4: Task management ---
with tab_tasks:
    st.subheader("任務管理")

    tasks = task_svc.get_by_project(project_id)
    status_keys = list(TASK_STATUSES.keys())

    sub_tab_list, sub_tab_add = st.tabs(["任務列表", "新增任務"])

    with sub_tab_list:
        if not tasks:
            st.info("尚無任務，請至「新增任務」頁籤建立。")
        else:
            # Highlight next actions
            next_actions = [t for t in tasks if t.get("is_next_action") and t["status"] != "completed"]
            if next_actions:
                st.markdown("**下一步行動：**")
                for t in next_actions:
                    due = f"（到期：{t['due_date']}）" if t.get("due_date") else ""
                    st.warning(f"{t['task_name']} — {t.get('owner') or '未指派'} {due}")

            df = pd.DataFrame(tasks)
            display_cols = ["task_id", "task_name", "owner", "status",
                            "due_date", "is_next_action", "start_date", "end_date",
                            "estimated_hours", "actual_hours"]
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
                key="presale_edit_task_select",
            )

            current_task = task_svc.get_by_id(edit_task_id)
            if current_task:
                with st.form("presale_edit_task_form"):
                    task_name = st.text_input("任務名稱", value=current_task["task_name"])
                    c1, c2 = st.columns(2)
                    with c1:
                        owner = st.text_input("負責人", value=current_task.get("owner") or "")
                    with c2:
                        cur_idx = status_keys.index(current_task["status"]) if current_task["status"] in status_keys else 0
                        status = st.selectbox("狀態", options=status_keys,
                                              format_func=lambda x: TASK_STATUSES[x],
                                              index=cur_idx, key="presale_edit_task_status")
                    c3, c4 = st.columns(2)
                    with c3:
                        due_date = st.date_input("到期日", value=current_task.get("due_date"),
                                                  key="presale_edit_due_date")
                    with c4:
                        is_next_action = st.checkbox("標記為下一步行動",
                                                      value=bool(current_task.get("is_next_action")),
                                                      key="presale_edit_next_action")
                    c5, c6 = st.columns(2)
                    with c5:
                        start_date = st.date_input("開始日期", value=current_task.get("start_date"),
                                                    key="presale_edit_start")
                    with c6:
                        end_date = st.date_input("結束日期", value=current_task.get("end_date"),
                                                  key="presale_edit_end")
                    c7, c8, c9 = st.columns(3)
                    with c7:
                        est_hours = st.number_input("預估工時", min_value=0.0,
                                                     value=float(current_task["estimated_hours"]),
                                                     step=1.0, key="presale_edit_est")
                    with c8:
                        act_hours = st.number_input("實際工時", min_value=0.0,
                                                     value=float(current_task["actual_hours"]),
                                                     step=1.0, key="presale_edit_act")
                    with c9:
                        sort_order = st.number_input("排序", min_value=0,
                                                      value=current_task["sort_order"],
                                                      step=1, key="presale_edit_sort")

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

                if st.button("刪除此任務", key="presale_delete_task_btn", type="secondary"):
                    task_svc.delete(edit_task_id)
                    st.success("任務已刪除。")
                    st.rerun()

    with sub_tab_add:
        with st.form("presale_add_task_form", clear_on_submit=True):
            task_name = st.text_input("任務名稱")
            c1, c2 = st.columns(2)
            with c1:
                owner = st.text_input("負責人", key="presale_add_owner")
            with c2:
                status = st.selectbox("狀態", options=status_keys,
                                      format_func=lambda x: TASK_STATUSES[x],
                                      key="presale_add_status")
            c3, c4 = st.columns(2)
            with c3:
                due_date = st.date_input("到期日", value=None, key="presale_add_due_date")
            with c4:
                is_next_action = st.checkbox("標記為下一步行動", key="presale_add_next_action")
            c5, c6 = st.columns(2)
            with c5:
                start_date = st.date_input("開始日期", value=date.today(), key="presale_add_start")
            with c6:
                end_date = st.date_input("結束日期", value=date.today(), key="presale_add_end")
            c7, c8, c9 = st.columns(3)
            with c7:
                est_hours = st.number_input("預估工時", min_value=0.0, value=8.0, step=1.0, key="presale_add_est")
            with c8:
                act_hours = st.number_input("實際工時", min_value=0.0, value=0.0, step=1.0, key="presale_add_act")
            with c9:
                sort_order = st.number_input("排序", min_value=0, value=0, step=1, key="presale_add_sort")

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

# --- Tab 5: Status transition ---
with tab_transition:
    st.subheader("狀態流轉")

    current_status = project["status_code"]
    st.info(f"目前狀態：**{current_status}** — {STATUS_CODES.get(current_status, '')}")

    allowed = PRESALE_TRANSITIONS.get(current_status, [])
    if not allowed:
        st.warning("此案件已達終態，無法進行狀態流轉。")
    else:
        display = [f"{s} — {STATUS_CODES.get(s, '')}" for s in allowed]
        selected_display = st.selectbox("選擇下一步狀態", options=display, key="detail_trans_select")
        new_status = allowed[display.index(selected_display)]

        if st.button("確認流轉", key="detail_trans_btn"):
            try:
                project_svc.transition_status(project_id, new_status)
                if new_status == "L7":
                    st.success("已簽約！專案已自動移至售後管理（P0 規劃）")
                else:
                    st.success(f"狀態已從 {current_status} 流轉至 {new_status}")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

st.divider()

# === Back button ===
if st.button("← 返回案件列表"):
    st.switch_page("pages/presale.py")
