"""Annual Plan page — product strategy management."""

import pandas as pd
import streamlit as st

from components.sidebar import render_sidebar
from services import annual_plan as ap_svc
from services import settings as settings_svc

render_sidebar()

headers = settings_svc.get_all_headers()
st.header(headers.get("header_annual_plan", "產品策略管理"))

# --- Product list ---
products = ap_svc.get_all()
if products:
    df = pd.DataFrame(products)
    st.dataframe(df, width="stretch")
else:
    st.info("尚無年度戰略資料。")

st.divider()

# --- Add / Edit ---
tab_add, tab_edit = st.tabs(["新增產品", "編輯產品"])

with tab_add:
    with st.form("add_ap_form", clear_on_submit=True):
        product_id = st.text_input("產品 ID")
        product_name = st.text_input("產品名稱")
        quota_fy26 = st.number_input("年度目標 (FY26)", min_value=0.0, value=0.0, step=100000.0)
        strategy = st.text_area("攻案策略")
        target_industry = st.text_input("鎖定產業")

        if st.form_submit_button("新增"):
            if product_id.strip() and product_name.strip():
                ap_svc.create(
                    product_id=product_id.strip(),
                    product_name=product_name.strip(),
                    quota_fy26=quota_fy26,
                    strategy=strategy or None,
                    target_industry=target_industry or None,
                )
                st.success(f"已新增產品：{product_name}")
                st.rerun()
            else:
                st.warning("請輸入產品 ID 與名稱。")

with tab_edit:
    if not products:
        st.info("沒有可編輯的產品。")
    else:
        edit_options = {p["product_id"]: p["product_name"] for p in products}
        edit_id = st.selectbox(
            "選擇要編輯的產品",
            options=list(edit_options.keys()),
            format_func=lambda x: f"{x} — {edit_options[x]}",
        )
        current = ap_svc.get_by_id(edit_id)
        if current:
            with st.form("edit_ap_form"):
                product_name = st.text_input("產品名稱", value=current["product_name"])
                quota_fy26 = st.number_input(
                    "年度目標 (FY26)", min_value=0.0,
                    value=float(current["quota_fy26"]), step=100000.0,
                )
                strategy = st.text_area("攻案策略", value=current["strategy"] or "")
                target_industry = st.text_input("鎖定產業", value=current["target_industry"] or "")

                if st.form_submit_button("儲存"):
                    ap_svc.update(
                        product_id=edit_id,
                        product_name=product_name.strip(),
                        quota_fy26=quota_fy26,
                        strategy=strategy or None,
                        target_industry=target_industry or None,
                    )
                    st.success("產品資料已更新。")
                    st.rerun()
