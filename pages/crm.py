"""CRM page — customer relationship management with JSONB fields."""

import pandas as pd
import streamlit as st

from components.sidebar import render_sidebar
from services import crm as crm_svc
from services import settings as settings_svc

render_sidebar()

headers = settings_svc.get_all_headers()
st.header(headers.get("header_crm", "客戶管理"))

# --- Client list ---
clients = crm_svc.get_all()
if clients:
    df = pd.DataFrame(clients)
    st.dataframe(df, use_container_width=True)
else:
    st.info("尚無客戶資料。")

st.divider()

# --- Add / Edit ---
tab_add, tab_edit = st.tabs(["新增客戶", "編輯客戶"])


def _jsonb_inputs(prefix, dm_or_champ, defaults=None):
    """Render text_inputs for a JSONB sub-object. Returns dict."""
    defaults = defaults or {}
    if dm_or_champ == "decision_maker":
        labels = [("name", "姓名"), ("title", "職稱"), ("style", "溝通風格")]
    else:
        labels = [("name", "姓名"), ("title", "職稱"), ("notes", "備註")]
    result = {}
    cols = st.columns(len(labels))
    for col, (key, label) in zip(cols, labels):
        with col:
            result[key] = st.text_input(f"{label}", value=defaults.get(key, ""), key=f"{prefix}_{key}")
    return result


with tab_add:
    with st.form("add_crm_form", clear_on_submit=True):
        client_id = st.text_input("客戶 ID")
        company_name = st.text_input("公司名稱")
        col1, col2 = st.columns(2)
        with col1:
            industry = st.text_input("產業別")
        with col2:
            email = st.text_input("Email")

        st.markdown("**決策者 (Decision Maker)**")
        dm = _jsonb_inputs("add_dm", "decision_maker")
        st.markdown("**內部擁護者 (Champion)**")
        champ = _jsonb_inputs("add_ch", "champion")

        contact_info = st.text_input("聯絡資訊")
        notes = st.text_area("備註")

        if st.form_submit_button("新增"):
            if client_id.strip() and company_name.strip():
                crm_svc.create(
                    client_id=client_id.strip(),
                    company_name=company_name.strip(),
                    industry=industry or None,
                    email=email or None,
                    decision_maker=dm if any(dm.values()) else None,
                    champion=champ if any(champ.values()) else None,
                    contact_info=contact_info or None,
                    notes=notes or None,
                )
                st.success(f"已新增客戶：{company_name}")
                st.rerun()
            else:
                st.warning("請輸入客戶 ID 與公司名稱。")

with tab_edit:
    if not clients:
        st.info("沒有可編輯的客戶。")
    else:
        edit_options = {c["client_id"]: c["company_name"] for c in clients}
        edit_id = st.selectbox(
            "選擇要編輯的客戶",
            options=list(edit_options.keys()),
            format_func=lambda x: f"{x} — {edit_options[x]}",
        )
        current = crm_svc.get_by_id(edit_id)
        if current:
            with st.form("edit_crm_form"):
                company_name = st.text_input("公司名稱", value=current["company_name"])
                col1, col2 = st.columns(2)
                with col1:
                    industry = st.text_input("產業別", value=current["industry"] or "")
                with col2:
                    email = st.text_input("Email", value=current["email"] or "")

                st.markdown("**決策者 (Decision Maker)**")
                dm = _jsonb_inputs("edit_dm", "decision_maker", defaults=current["decision_maker"] or {})
                st.markdown("**內部擁護者 (Champion)**")
                champ = _jsonb_inputs("edit_ch", "champion", defaults=current["champion"] or {})

                contact_info = st.text_input("聯絡資訊", value=current["contact_info"] or "")
                notes = st.text_area("備註", value=current["notes"] or "")

                if st.form_submit_button("儲存"):
                    crm_svc.update(
                        client_id=edit_id,
                        company_name=company_name.strip(),
                        industry=industry or None,
                        email=email or None,
                        decision_maker=dm if any(dm.values()) else None,
                        champion=champ if any(champ.values()) else None,
                        contact_info=contact_info or None,
                        notes=notes or None,
                    )
                    st.success("客戶資料已更新。")
                    st.rerun()
