"""CRM page — customer relationship management with 4-tab layout."""

import json
from datetime import date

import pandas as pd
import streamlit as st

from components.sidebar import render_sidebar
from services import crm as crm_svc
from services import settings as settings_svc

render_sidebar()

headers = settings_svc.get_all_headers()
st.header(headers.get("header_crm", "客戶管理"))

clients = crm_svc.get_all()

tab_overview, tab_detail, tab_add, tab_edit = st.tabs(
    ["客戶總覽", "客戶詳情", "新增客戶", "編輯客戶"]
)

# ---------------------------------------------------------------------------
# Helper: parse champions (handles str / list / None)
# ---------------------------------------------------------------------------

def _parse_champions(raw):
    if raw is None:
        return []
    if isinstance(raw, str):
        raw = json.loads(raw)
    if isinstance(raw, dict):
        return [raw]
    return raw


def _parse_dm(raw):
    if raw is None:
        return {}
    if isinstance(raw, str):
        return json.loads(raw)
    return raw


# ===========================================================================
# Tab 1: 客戶總覽
# ===========================================================================
with tab_overview:
    if not clients:
        st.info("尚無客戶資料。")
    else:
        display_data = []
        for c in clients:
            dm = _parse_dm(c.get("decision_maker"))
            champs = _parse_champions(c.get("champions"))
            champ_names = ", ".join(ch.get("name", "") for ch in champs if ch.get("name"))
            display_data.append({
                "客戶 ID": c["client_id"],
                "公司名稱": c["company_name"],
                "產業別": c.get("industry") or "",
                "部門": c.get("department") or "",
                "決策者": dm.get("name", ""),
                "Champion(s)": champ_names,
                "資料年份": c.get("data_year") or "",
            })
        st.dataframe(pd.DataFrame(display_data), width="stretch")


# ===========================================================================
# Tab 2: 客戶詳情
# ===========================================================================
with tab_detail:
    if not clients:
        st.info("沒有可檢視的客戶。")
    else:
        detail_options = {c["client_id"]: c["company_name"] for c in clients}
        detail_id = st.selectbox(
            "選擇客戶",
            options=list(detail_options.keys()),
            format_func=lambda x: f"{x} — {detail_options[x]}",
            key="detail_select",
        )
        current = crm_svc.get_by_id(detail_id)
        if current:
            # Basic info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**公司名稱**: {current['company_name']}")
                st.markdown(f"**產業別**: {current.get('industry') or '—'}")
            with col2:
                st.markdown(f"**部門**: {current.get('department') or '—'}")
            with col3:
                st.markdown(f"**資料年份**: {current.get('data_year') or '—'}")

            st.divider()

            # Decision Maker card
            dm = _parse_dm(current.get("decision_maker"))
            st.markdown("**決策者 (Decision Maker)**")
            if dm.get("name"):
                dc1, dc2, dc3, dc4, dc5 = st.columns(5)
                dc1.markdown(f"姓名：{dm.get('name', '—')}")
                dc2.markdown(f"職稱：{dm.get('title', '—')}")
                dc3.markdown(f"Email：{dm.get('email', '—')}")
                dc4.markdown(f"電話：{dm.get('phone', '—')}")
                dc5.markdown(f"備註：{dm.get('notes', '—')}")
            else:
                st.markdown("—")

            st.divider()

            # Champions list
            champs = _parse_champions(current.get("champions"))
            st.markdown(f"**內部擁護者 (Champions)** — 共 {len(champs)} 位")
            if champs:
                for i, ch in enumerate(champs):
                    cc1, cc2, cc3, cc4, cc5 = st.columns(5)
                    cc1.markdown(f"姓名：{ch.get('name', '—')}")
                    cc2.markdown(f"職稱：{ch.get('title', '—')}")
                    cc3.markdown(f"Email：{ch.get('email', '—')}")
                    cc4.markdown(f"電話：{ch.get('phone', '—')}")
                    cc5.markdown(f"備註：{ch.get('notes', '—')}")
                    if i < len(champs) - 1:
                        st.markdown("---")
            else:
                st.markdown("—")

            if current.get("notes"):
                st.divider()
                st.markdown(f"**備註**: {current['notes']}")


# ===========================================================================
# Tab 3: 新增客戶
# ===========================================================================
with tab_add:
    # Dynamic champion count (buttons outside form)
    add_key = "add_champion_count"
    if add_key not in st.session_state:
        st.session_state[add_key] = 1

    st.markdown("**內部擁護者 (Champions)**")
    col_a, col_b, _ = st.columns([2, 2, 5])
    with col_a:
        if st.button("＋ 新增擁護者", key="add_champ_btn"):
            st.session_state[add_key] += 1
            st.rerun()
    with col_b:
        if st.button("－ 移除最後一位", key="rm_champ_btn") and st.session_state[add_key] > 1:
            st.session_state[add_key] -= 1
            st.rerun()

    with st.form("add_crm_form", clear_on_submit=True):
        client_id = st.text_input("客戶 ID")
        company_name = st.text_input("公司名稱")
        col1, col2 = st.columns(2)
        with col1:
            industry = st.text_input("產業別")
        with col2:
            department = st.text_input("部門")

        contact_info = st.text_input("聯絡資訊", key="add_contact")
        data_year = st.number_input("資料年份", min_value=2000, max_value=2100,
                                    value=date.today().year, key="add_data_year")
        notes = st.text_area("備註", key="add_notes")

        # Decision Maker
        st.markdown("**決策者 (Decision Maker)**")
        dm_c1, dm_c2, dm_c3, dm_c4, dm_c5 = st.columns(5)
        dm = {
            "name": dm_c1.text_input("姓名", key="add_dm_name"),
            "title": dm_c2.text_input("職稱", key="add_dm_title"),
            "email": dm_c3.text_input("Email", key="add_dm_email"),
            "phone": dm_c4.text_input("電話", key="add_dm_phone"),
            "notes": dm_c5.text_input("備註", key="add_dm_notes"),
        }

        # Champions
        st.markdown("**內部擁護者 (Champions)**")
        champions = []
        for i in range(st.session_state[add_key]):
            st.markdown(f"**擁護者 {i + 1}**")
            c1, c2, c3, c4, c5 = st.columns(5)
            champ = {
                "name": c1.text_input("姓名", key=f"add_ch_{i}_name"),
                "title": c2.text_input("職稱", key=f"add_ch_{i}_title"),
                "email": c3.text_input("Email", key=f"add_ch_{i}_email"),
                "phone": c4.text_input("電話", key=f"add_ch_{i}_phone"),
                "notes": c5.text_input("備註", key=f"add_ch_{i}_notes"),
            }
            champions.append(champ)

        if st.form_submit_button("新增"):
            if client_id.strip() and company_name.strip():
                filtered_champs = [c for c in champions if any(c.values())]
                crm_svc.create(
                    client_id=client_id.strip(),
                    company_name=company_name.strip(),
                    industry=industry or None,
                    department=department or None,
                    decision_maker=dm if any(dm.values()) else None,
                    champions=filtered_champs or None,
                    contact_info=contact_info or None,
                    notes=notes or None,
                    data_year=data_year,
                )
                st.success(f"已新增客戶：{company_name}")
                st.session_state[add_key] = 1
                st.rerun()
            else:
                st.warning("請輸入客戶 ID 與公司名稱。")


# ===========================================================================
# Tab 4: 編輯客戶
# ===========================================================================
with tab_edit:
    if not clients:
        st.info("沒有可編輯的客戶。")
    else:
        edit_options = {c["client_id"]: c["company_name"] for c in clients}
        edit_id = st.selectbox(
            "選擇要編輯的客戶",
            options=list(edit_options.keys()),
            format_func=lambda x: f"{x} — {edit_options[x]}",
            key="edit_select",
        )
        current = crm_svc.get_by_id(edit_id)
        if current:
            existing_champs = _parse_champions(current.get("champions"))
            existing_dm = _parse_dm(current.get("decision_maker"))

            # Dynamic champion count for edit (buttons outside form)
            edit_count_key = f"edit_champion_count_{edit_id}"
            if edit_count_key not in st.session_state:
                st.session_state[edit_count_key] = max(len(existing_champs), 1)

            st.markdown("**內部擁護者 (Champions)**")
            ecol_a, ecol_b, _ = st.columns([2, 2, 5])
            with ecol_a:
                if st.button("＋ 新增擁護者", key=f"edit_add_champ_{edit_id}"):
                    st.session_state[edit_count_key] += 1
                    st.rerun()
            with ecol_b:
                if st.button("－ 移除最後一位", key=f"edit_rm_champ_{edit_id}") and st.session_state[edit_count_key] > 1:
                    st.session_state[edit_count_key] -= 1
                    st.rerun()

            with st.form(f"edit_crm_form_{edit_id}"):
                company_name = st.text_input("公司名稱", value=current["company_name"],
                                             key=f"edit_company_{edit_id}")
                col1, col2 = st.columns(2)
                with col1:
                    industry = st.text_input("產業別", value=current.get("industry") or "",
                                             key=f"edit_industry_{edit_id}")
                with col2:
                    department = st.text_input("部門", value=current.get("department") or "",
                                               key=f"edit_department_{edit_id}")

                contact_info = st.text_input("聯絡資訊", value=current.get("contact_info") or "",
                                             key=f"edit_contact_{edit_id}")
                data_year = st.number_input("資料年份", min_value=2000, max_value=2100,
                                            value=current.get("data_year") or date.today().year,
                                            key=f"edit_data_year_{edit_id}")
                notes = st.text_area("備註", value=current.get("notes") or "",
                                     key=f"edit_notes_{edit_id}")

                # Decision Maker
                st.markdown("**決策者 (Decision Maker)**")
                dm_c1, dm_c2, dm_c3, dm_c4, dm_c5 = st.columns(5)
                dm = {
                    "name": dm_c1.text_input("姓名", value=existing_dm.get("name", ""),
                                             key=f"edit_dm_name_{edit_id}"),
                    "title": dm_c2.text_input("職稱", value=existing_dm.get("title", ""),
                                              key=f"edit_dm_title_{edit_id}"),
                    "email": dm_c3.text_input("Email", value=existing_dm.get("email", ""),
                                              key=f"edit_dm_email_{edit_id}"),
                    "phone": dm_c4.text_input("電話", value=existing_dm.get("phone", ""),
                                              key=f"edit_dm_phone_{edit_id}"),
                    "notes": dm_c5.text_input("備註", value=existing_dm.get("notes", ""),
                                              key=f"edit_dm_notes_{edit_id}"),
                }

                # Champions
                st.markdown("**內部擁護者 (Champions)**")
                champions = []
                for i in range(st.session_state[edit_count_key]):
                    defaults = existing_champs[i] if i < len(existing_champs) else {}
                    st.markdown(f"**擁護者 {i + 1}**")
                    c1, c2, c3, c4, c5 = st.columns(5)
                    champ = {
                        "name": c1.text_input("姓名", value=defaults.get("name", ""),
                                              key=f"edit_ch_{i}_name_{edit_id}"),
                        "title": c2.text_input("職稱", value=defaults.get("title", ""),
                                               key=f"edit_ch_{i}_title_{edit_id}"),
                        "email": c3.text_input("Email", value=defaults.get("email", ""),
                                               key=f"edit_ch_{i}_email_{edit_id}"),
                        "phone": c4.text_input("電話", value=defaults.get("phone", ""),
                                               key=f"edit_ch_{i}_phone_{edit_id}"),
                        "notes": c5.text_input("備註", value=defaults.get("notes", ""),
                                               key=f"edit_ch_{i}_notes_{edit_id}"),
                    }
                    champions.append(champ)

                if st.form_submit_button("儲存"):
                    filtered_champs = [c for c in champions if any(c.values())]
                    crm_svc.update(
                        client_id=edit_id,
                        company_name=company_name.strip(),
                        industry=industry or None,
                        department=department or None,
                        decision_maker=dm if any(dm.values()) else None,
                        champions=filtered_champs or None,
                        contact_info=contact_info or None,
                        notes=notes or None,
                        data_year=data_year,
                    )
                    st.success("客戶資料已更新。")
                    st.rerun()
