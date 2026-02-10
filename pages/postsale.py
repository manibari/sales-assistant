"""Post-sale Management page — CRUD + status transition for P0-P2 stages."""

import pandas as pd
import streamlit as st

from components.sidebar import render_sidebar
from constants import POSTSALE_TRANSITIONS, STATUS_CODES, POSTSALE_STATUS_CODES
from services import annual_plan as ap_svc
from services import crm as crm_svc
from services import project as project_svc
from services import settings as settings_svc

render_sidebar()

headers = settings_svc.get_all_headers()
st.header(headers.get("header_postsale", "專案管理"))

# --- Project list (postsale only) ---
projects = project_svc.get_postsale()
if projects:
    df = pd.DataFrame(projects)
    # Chinese display for codes
    client_map = {c["client_id"]: c["company_name"] for c in crm_svc.get_all()}
    product_map = {p["product_id"]: p["product_name"] for p in ap_svc.get_all()}
    df["status_code"] = df["status_code"].map(lambda x: f"{x} {STATUS_CODES.get(x, '')}")
    df["client_id"] = df["client_id"].map(lambda x: client_map.get(x, x or "—"))
    df["product_id"] = df["product_id"].map(lambda x: product_map.get(x, x or "—"))
    display_cols = ["project_id", "project_name", "client_id", "product_id",
                    "status_code", "postsale_owner", "priority", "status_updated_at"]
    st.dataframe(df[[c for c in display_cols if c in df.columns]], width="stretch")

    st.subheader("專案詳情")
    for p in projects:
        col1, col2 = st.columns([4, 1])
        with col1:
            status_label = f'{p["status_code"]} {STATUS_CODES.get(p["status_code"], "")}'
            st.write(f'[{status_label}] {p["project_name"]}')
        with col2:
            if st.button("查看詳情", key=f'detail_{p["project_id"]}'):
                st.query_params["project_id"] = str(p["project_id"])
                st.switch_page("pages/postsale_detail.py")
else:
    st.info("尚無售後專案資料。")

st.divider()

# --- Helper: load dropdown options ---
all_clients = crm_svc.get_all()
all_products = ap_svc.get_all()
client_options = {c["client_id"]: c["company_name"] for c in all_clients}
product_options = {p["product_id"]: p["product_name"] for p in all_products}

# --- Add / Edit / Transition ---
tab_add, tab_edit, tab_transition = st.tabs(["新增售後案件", "編輯案件", "狀態流轉"])

with tab_add:
    st.markdown("售前案件簽約完成（L7）後，在此建立售後追蹤。")
    with st.form("add_postsale_form", clear_on_submit=True):
        name = st.text_input("專案名稱")
        col1, col2 = st.columns(2)
        with col1:
            client_id = st.selectbox(
                "客戶",
                options=[""] + list(client_options.keys()),
                format_func=lambda x: client_options.get(x, "（不指定）"),
                key="postsale_add_client",
            )
        with col2:
            product_id = st.selectbox(
                "產品",
                options=[""] + list(product_options.keys()),
                format_func=lambda x: product_options.get(x, "（不指定）"),
                key="postsale_add_product",
            )
        col3, col4 = st.columns(2)
        with col3:
            postsale_owner = st.text_input("售後負責人")
        with col4:
            priority = st.selectbox("優先級", options=["High", "Medium", "Low"], index=1)

        if st.form_submit_button("新增"):
            if name.strip():
                project_svc.create(
                    project_name=name.strip(),
                    client_id=client_id or None,
                    product_id=product_id or None,
                    status_code="P0",
                    postsale_owner=postsale_owner or None,
                    priority=priority,
                )
                st.success(f"已新增售後案件：{name}")
                st.rerun()
            else:
                st.warning("請輸入專案名稱。")

with tab_edit:
    if not projects:
        st.info("沒有可編輯的售後案件。")
    else:
        edit_options = {p["project_id"]: p["project_name"] for p in projects}
        edit_id = st.selectbox(
            "選擇要編輯的案件",
            options=list(edit_options.keys()),
            format_func=lambda x: edit_options[x],
            key="postsale_edit_select",
        )
        current = project_svc.get_by_id(edit_id)
        if current:
            with st.form("edit_postsale_form"):
                name = st.text_input("專案名稱", value=current["project_name"])
                col1, col2 = st.columns(2)
                with col1:
                    client_keys = [""] + list(client_options.keys())
                    client_idx = client_keys.index(current["client_id"]) if current["client_id"] in client_keys else 0
                    client_id = st.selectbox(
                        "客戶", options=client_keys,
                        format_func=lambda x: client_options.get(x, "（不指定）"),
                        index=client_idx, key="postsale_edit_client",
                    )
                with col2:
                    product_keys = [""] + list(product_options.keys())
                    product_idx = product_keys.index(current["product_id"]) if current["product_id"] in product_keys else 0
                    product_id = st.selectbox(
                        "產品", options=product_keys,
                        format_func=lambda x: product_options.get(x, "（不指定）"),
                        index=product_idx, key="postsale_edit_product",
                    )
                col3, col4 = st.columns(2)
                with col3:
                    postsale_owner = st.text_input("售後負責人", value=current.get("postsale_owner") or "")
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
                        presale_owner=current.get("presale_owner"),
                        postsale_owner=postsale_owner or None,
                        priority=priority,
                        sales_owner=current.get("sales_owner"),
                    )
                    st.success("案件已更新。")
                    st.rerun()

with tab_transition:
    if not projects:
        st.info("沒有可操作的售後案件。")
    else:
        trans_options = {
            p["project_id"]: f'[{p["status_code"]} {STATUS_CODES.get(p["status_code"], "")}] {p["project_name"]}'
            for p in projects
        }
        trans_id = st.selectbox(
            "選擇案件",
            options=list(trans_options.keys()),
            format_func=lambda x: trans_options[x],
            key="postsale_trans_select",
        )
        current = project_svc.get_by_id(trans_id)
        if current:
            current_status = current["status_code"]
            st.info(f"目前狀態：**{current_status}** — {STATUS_CODES.get(current_status, '')}")

            allowed = POSTSALE_TRANSITIONS.get(current_status, [])
            if not allowed:
                st.warning("此案件已達終態（驗收完成），無法進行狀態流轉。")
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
