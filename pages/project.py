"""Project Management page — CRUD + status transition."""

import pandas as pd
import streamlit as st

from components.sidebar import render_sidebar
from constants import STATUS_CODES, VALID_TRANSITIONS
from services import annual_plan as ap_svc
from services import crm as crm_svc
from services import project as project_svc
from services import settings as settings_svc

render_sidebar()

headers = settings_svc.get_all_headers()
st.header(headers.get("header_project", "專案管理"))

# --- Project list ---
projects = project_svc.get_all()
if projects:
    df = pd.DataFrame(projects)
    st.dataframe(df, use_container_width=True)
else:
    st.info("尚無專案資料。")

st.divider()

# --- Helper: load dropdown options ---
all_clients = crm_svc.get_all()
all_products = ap_svc.get_all()
client_options = {c["client_id"]: c["company_name"] for c in all_clients}
product_options = {p["product_id"]: p["product_name"] for p in all_products}

# --- Add / Edit project ---
tab_add, tab_edit, tab_transition = st.tabs(["新增專案", "編輯專案", "狀態流轉"])

with tab_add:
    with st.form("add_project_form", clear_on_submit=True):
        name = st.text_input("專案名稱")
        col1, col2 = st.columns(2)
        with col1:
            client_id = st.selectbox(
                "客戶",
                options=[""] + list(client_options.keys()),
                format_func=lambda x: client_options.get(x, "（不指定）"),
                key="add_client",
            )
        with col2:
            product_id = st.selectbox(
                "產品",
                options=[""] + list(product_options.keys()),
                format_func=lambda x: product_options.get(x, "（不指定）"),
                key="add_product",
            )
        col3, col4 = st.columns(2)
        with col3:
            owner = st.text_input("負責人")
        with col4:
            priority = st.selectbox("優先級", options=["High", "Medium", "Low"], index=1)

        if st.form_submit_button("新增"):
            if name.strip():
                project_svc.create(
                    project_name=name.strip(),
                    client_id=client_id or None,
                    product_id=product_id or None,
                    owner=owner or None,
                    priority=priority,
                )
                st.success(f"已新增專案：{name}")
                st.rerun()
            else:
                st.warning("請輸入專案名稱。")

with tab_edit:
    if not projects:
        st.info("沒有可編輯的專案。")
    else:
        edit_options = {p["project_id"]: p["project_name"] for p in projects}
        edit_id = st.selectbox(
            "選擇要編輯的專案",
            options=list(edit_options.keys()),
            format_func=lambda x: edit_options[x],
            key="edit_select",
        )
        current = project_svc.get_by_id(edit_id)
        if current:
            with st.form("edit_project_form"):
                name = st.text_input("專案名稱", value=current["project_name"])
                col1, col2 = st.columns(2)
                with col1:
                    client_keys = [""] + list(client_options.keys())
                    client_idx = client_keys.index(current["client_id"]) if current["client_id"] in client_keys else 0
                    client_id = st.selectbox(
                        "客戶", options=client_keys,
                        format_func=lambda x: client_options.get(x, "（不指定）"),
                        index=client_idx, key="edit_client",
                    )
                with col2:
                    product_keys = [""] + list(product_options.keys())
                    product_idx = product_keys.index(current["product_id"]) if current["product_id"] in product_keys else 0
                    product_id = st.selectbox(
                        "產品", options=product_keys,
                        format_func=lambda x: product_options.get(x, "（不指定）"),
                        index=product_idx, key="edit_product",
                    )
                col3, col4 = st.columns(2)
                with col3:
                    owner = st.text_input("負責人", value=current["owner"] or "")
                with col4:
                    priorities = ["High", "Medium", "Low"]
                    priority = st.selectbox(
                        "優先級", options=priorities,
                        index=priorities.index(current["priority"]) if current["priority"] in priorities else 1,
                    )

                if st.form_submit_button("儲存"):
                    project_svc.update(
                        project_id=edit_id,
                        project_name=name.strip(),
                        client_id=client_id or None,
                        product_id=product_id or None,
                        owner=owner or None,
                        priority=priority,
                    )
                    st.success("專案已更新。")
                    st.rerun()

with tab_transition:
    if not projects:
        st.info("沒有可操作的專案。")
    else:
        trans_options = {
            p["project_id"]: f'[{p["status_code"]}] {p["project_name"]}'
            for p in projects
        }
        trans_id = st.selectbox(
            "選擇專案",
            options=list(trans_options.keys()),
            format_func=lambda x: trans_options[x],
            key="trans_select",
        )
        current = project_svc.get_by_id(trans_id)
        if current:
            current_status = current["status_code"]
            st.info(f"目前狀態：**{current_status}** — {STATUS_CODES.get(current_status, '')}")

            allowed = VALID_TRANSITIONS.get(current_status, [])
            if not allowed:
                st.warning("此專案已達終態，無法進行狀態流轉。")
            else:
                display = [f"{s} — {STATUS_CODES.get(s, '')}" for s in allowed]
                selected_display = st.selectbox("選擇下一步狀態", options=display)
                new_status = allowed[display.index(selected_display)]

                if st.button("確認流轉"):
                    try:
                        project_svc.transition_status(trans_id, new_status)
                        st.success(f"狀態已從 {current_status} 流轉至 {new_status}")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
