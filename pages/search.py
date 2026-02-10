"""Global Search page — search across contacts, clients, and projects."""

import streamlit as st

from components.sidebar import render_sidebar
from constants import STATUS_CODES
from services import search as search_svc

render_sidebar()

st.header("全域搜尋")

query = st.text_input("搜尋（公司名稱、聯絡人、電話、專案名稱⋯）", key="global_search")

if query and len(query.strip()) >= 1:
    results = search_svc.search_all(query.strip())

    total = sum(len(v) for v in results.values())
    st.caption(f"共找到 {total} 筆結果")

    # --- Contacts ---
    if results["contacts"]:
        st.subheader(f"聯絡人（{len(results['contacts'])} 筆）")
        for c in results["contacts"]:
            st.markdown(
                f"**{c['name']}**　{c.get('title') or ''}　"
                f"{c.get('email') or ''}　{c.get('phone') or ''}"
            )

    # --- Clients ---
    if results["clients"]:
        st.subheader(f"客戶（{len(results['clients'])} 筆）")
        for c in results["clients"]:
            st.markdown(
                f"**{c['company_name']}**（{c['client_id']}）　"
                f"{c.get('industry') or ''}　{c.get('department') or ''}"
            )

    # --- Projects ---
    if results["projects"]:
        st.subheader(f"專案（{len(results['projects'])} 筆）")
        for p in results["projects"]:
            status_label = f"{p['status_code']} {STATUS_CODES.get(p['status_code'], '')}"
            client_name = p.get("client_name") or "—"
            st.markdown(f"**[{status_label}] {p['project_name']}** — {client_name}")
            # Link to detail page
            col1, col2 = st.columns([4, 1])
            with col2:
                if p["status_code"].startswith("P"):
                    if st.button("查看詳情", key=f"search_detail_{p['project_id']}"):
                        st.query_params["project_id"] = str(p["project_id"])
                        st.switch_page("pages/postsale_detail.py")
                elif p["status_code"].startswith("L"):
                    if st.button("查看詳情", key=f"search_detail_{p['project_id']}"):
                        st.query_params["project_id"] = str(p["project_id"])
                        st.switch_page("pages/presale_detail.py")

    if total == 0:
        st.info("找不到符合的結果。")
elif query:
    st.info("請輸入至少 1 個字元。")
