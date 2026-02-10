"""Sales Plan page — opportunity forecast management."""

import pandas as pd
import streamlit as st

from components.sidebar import render_sidebar
from constants import DEFAULT_STAGE_PROBABILITIES
from services import annual_plan as ap_svc
from services import project as project_svc
from services import sales_plan as sp_svc
from services import settings as settings_svc
from services import stage_probability as prob_svc

render_sidebar()

headers = settings_svc.get_all_headers()
st.header(headers.get("header_sales_plan", "商機預測"))

# --- Opportunity list ---
plans = sp_svc.get_all()
if plans:
    df = pd.DataFrame(plans)
    st.dataframe(df, width="stretch")
else:
    st.info("尚無商機預測資料。")

st.divider()

# --- Helper: dropdown options ---
all_projects = project_svc.get_all()
all_products = ap_svc.get_all()
project_options = {p["project_id"]: p["project_name"] for p in all_projects}
product_options = {p["product_id"]: p["product_name"] for p in all_products}

# --- Add / Edit ---
tab_add, tab_edit = st.tabs(["新增商機", "編輯商機"])

with tab_add:
    if not all_projects:
        st.info("請先新增專案後才能建立商機。")
    else:
        # Project selector outside form so we can compute default confidence
        add_project_id = st.selectbox(
            "關聯專案",
            options=list(project_options.keys()),
            format_func=lambda x: project_options[x],
            key="add_sp_project",
        )

        # Look up stage probability for default confidence
        sel_project = project_svc.get_by_id(add_project_id)
        if sel_project:
            default_conf = prob_svc.get_by_code(sel_project["status_code"])
            if default_conf is None:
                default_conf = DEFAULT_STAGE_PROBABILITIES.get(sel_project["status_code"], 0.5)
            st.caption(f"階段機率預填：{default_conf:.0%}（{sel_project['status_code']}）")
        else:
            default_conf = 0.5

        with st.form("add_sp_form", clear_on_submit=True):
            product_id = st.selectbox(
                "關聯產品",
                options=[""] + list(product_options.keys()),
                format_func=lambda x: product_options.get(x, "（不指定）"),
                key="add_sp_product",
            )
            expected_invoice_date = st.date_input("預計開票日", value=None)
            amount = st.number_input("金額", min_value=0.0, value=0.0, step=10000.0)
            confidence_level = st.slider(
                "信心指數", min_value=0.0, max_value=1.0,
                value=default_conf, step=0.05,
            )
            prime_contractor = st.checkbox("主標", value=True)
            notes = st.text_area("備註")

            if st.form_submit_button("新增"):
                sp_svc.create(
                    project_id=add_project_id,
                    product_id=product_id or None,
                    expected_invoice_date=expected_invoice_date,
                    amount=amount,
                    confidence_level=confidence_level,
                    prime_contractor=prime_contractor,
                    notes=notes or None,
                )
                st.success("已新增商機預測。")
                st.rerun()

with tab_edit:
    if not plans:
        st.info("沒有可編輯的商機。")
    else:
        edit_options = {
            p["plan_id"]: f'#{p["plan_id"]} — {project_options.get(p["project_id"], "?")} (${p["amount"]:,.0f})'
            for p in plans
        }
        edit_id = st.selectbox(
            "選擇要編輯的商機",
            options=list(edit_options.keys()),
            format_func=lambda x: edit_options[x],
        )
        current = sp_svc.get_by_id(edit_id)
        if current:
            with st.form("edit_sp_form"):
                project_keys = list(project_options.keys())
                project_idx = project_keys.index(current["project_id"]) if current["project_id"] in project_keys else 0
                project_id = st.selectbox(
                    "關聯專案", options=project_keys,
                    format_func=lambda x: project_options[x],
                    index=project_idx, key="edit_sp_project",
                )
                product_keys = [""] + list(product_options.keys())
                product_idx = product_keys.index(current["product_id"]) if current["product_id"] in product_keys else 0
                product_id = st.selectbox(
                    "關聯產品", options=product_keys,
                    format_func=lambda x: product_options.get(x, "（不指定）"),
                    index=product_idx, key="edit_sp_product",
                )
                expected_invoice_date = st.date_input(
                    "預計開票日", value=current["expected_invoice_date"],
                )
                amount = st.number_input(
                    "金額", min_value=0.0, value=float(current["amount"]), step=10000.0,
                )
                confidence_level = st.slider(
                    "信心指數", min_value=0.0, max_value=1.0,
                    value=float(current["confidence_level"]), step=0.05,
                )
                prime_contractor = st.checkbox("主標", value=current["prime_contractor"])
                notes = st.text_area("備註", value=current["notes"] or "")

                if st.form_submit_button("儲存"):
                    sp_svc.update(
                        plan_id=edit_id,
                        project_id=project_id,
                        product_id=product_id or None,
                        expected_invoice_date=expected_invoice_date,
                        amount=amount,
                        confidence_level=confidence_level,
                        prime_contractor=prime_contractor,
                        notes=notes or None,
                    )
                    st.success("商機資料已更新。")
                    st.rerun()
