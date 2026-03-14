"""Annual Plan page — The War Room Dashboard."""

import streamlit as st
from collections import defaultdict

from components.sidebar import render_sidebar
from services import annual_plan as ap_svc
from services import settings as settings_svc
from services import analytics as analytics_svc

render_sidebar()

# --- Page Header ---
headers = settings_svc.get_all_headers()
st.header("年度戰情室 (Annual War Room)")

# --- Data & Constants ---
PILLARS = ["市場擴張", "客戶成功", "卓越營運", "生態與創新"]
COLUMN_ORDER = ["Q1 執行中", "Q2 計劃", "H2 展望", "完成 & 整合"]

# --- Fetch all data in one go ---
initiatives = ap_svc.get_all()
manpower_data = analytics_svc.get_manpower_by_initiative()
pipeline_data = analytics_svc.get_potential_pipeline_by_initiative()
app_settings = settings_svc.get_all_headers()
hourly_rate = float(app_settings.get("hourly_cost_rate", 100))

# --- Kanban Board UI ---
if not initiatives:
    st.info("尚無年度戰略舉措。請在下方新增一個。")
else:
    grouped_initiatives = defaultdict(list)
    for init in initiatives:
        status = init.get("status", "Q2 計劃")
        grouped_initiatives[status].append(init)

    columns = st.columns(len(COLUMN_ORDER))

    for i, col_name in enumerate(COLUMN_ORDER):
        with columns[i]:
            st.subheader(col_name)
            for init in grouped_initiatives[col_name]:
                with st.expander(f"**{init['product_name']}**"):
                    # --- Core Info ---
                    if init.get("battlefront"):
                        st.markdown(f"##### 戰線: {init['battlefront']}")
                    st.markdown(f"**ID:** `{init['product_id']}`")
                    st.markdown(f"**負責人:** {init.get('owner') or 'N/A'}")
                    st.markdown(f"**戰略支柱:** {init.get('pillar') or 'N/A'}")
                    st.markdown(f"**目標 (FY26):** `${init['quota_fy26']:,.0f}`")
                    
                    # --- War Room Metrics ---
                    st.markdown("---")
                    initiative_id = init['product_id']
                    manpower = manpower_data.get(initiative_id, 0)
                    burn_rate = manpower * hourly_rate
                    pipeline = pipeline_data.get(initiative_id, 0)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("投入人力 (hr)", f"{manpower:,.1f}")
                    with col2:
                        st.metric("預估成本 ($)", f"{burn_rate:,.0f}")
                    with col3:
                        st.metric("潛在商機 ($)", f"{pipeline:,.0f}")
                    st.markdown("---")

                    # --- Details ---
                    with st.container():
                        st.markdown("**KPIs:**")
                        st.info(init.get('kpis') or '尚未定義')
                        
                        st.markdown("**策略:**")
                        st.warning(init.get('strategy') or '尚未定義')


st.divider()

# --- Add / Edit Forms ---
tab_add, tab_edit = st.tabs(["新增舉措", "編輯舉措"])

with tab_add:
    with st.form("add_initiative_form", clear_on_submit=True):
        st.subheader("新增戰略舉措")
        
        col1, col2 = st.columns(2)
        with col1:
            product_id = st.text_input("舉措 ID (Initiative ID)")
            product_name = st.text_input("舉措名稱 (Title)")
        with col2:
            battlefront = st.text_input("戰線 (Battlefront)")
            owner = st.text_input("負責人 (Owner)")
        
        col1, col2 = st.columns(2)
        with col1:
            pillar = st.selectbox("戰略支柱 (Pillar)", options=PILLARS)
            status = st.selectbox("看板位置 (Status)", options=COLUMN_ORDER, index=1)
        with col2:
            quota_fy26 = st.number_input("年度目標 (FY26 Goal)", min_value=0.0, value=0.0, step=100000.0)

        kpis = st.text_area("衡量指標 (KPIs)")
        strategy = st.text_area("策略/描述 (Strategy/Description)")

        if st.form_submit_button("新增舉措"):
            if product_id.strip() and product_name.strip():
                ap_svc.create(
                    product_id=product_id.strip(),
                    product_name=product_name.strip(),
                    quota_fy26=quota_fy26,
                    strategy=strategy or None,
                    target_industry=None,
                    pillar=pillar,
                    owner=owner or None,
                    kpis=kpis or None,
                    status=status,
                    battlefront=battlefront or None,
                )
                st.success(f"已新增舉措：{product_name}")
                st.rerun()
            else:
                st.warning("請務必輸入舉措的 ID 與名稱。")

with tab_edit:
    if not initiatives:
        st.info("沒有可編輯的舉措。")
    else:
        st.subheader("編輯戰略舉措")
        edit_options = {p["product_id"]: p["product_name"] for p in initiatives}
        edit_id = st.selectbox(
            "選擇要編輯的舉措",
            options=list(edit_options.keys()),
            format_func=lambda x: f"{x} — {edit_options[x]}",
            key="edit_select"
        )
        
        current = ap_svc.get_by_id(edit_id)
        
        if current:
            with st.form("edit_initiative_form"):
                col1, col2 = st.columns(2)
                with col1:
                    product_name = st.text_input("舉措名稱 (Title)", value=current["product_name"])
                with col2:
                    battlefront = st.text_input("戰線 (Battlefront)", value=current.get("battlefront") or "")
                
                owner = st.text_input("負責人 (Owner)", value=current.get("owner") or "")

                col1, col2 = st.columns(2)
                with col1:
                    pillar = st.selectbox(
                        "戰略支柱 (Pillar)", options=PILLARS, 
                        index=PILLARS.index(current["pillar"]) if current.get("pillar") in PILLARS else 0
                    )
                    status = st.selectbox(
                        "看板位置 (Status)", options=COLUMN_ORDER,
                        index=COLUMN_ORDER.index(current["status"]) if current.get("status") in COLUMN_ORDER else 1
                    )
                with col2:
                    quota_fy26 = st.number_input(
                        "年度目標 (FY26 Goal)", min_value=0.0,
                        value=float(current["quota_fy26"]), step=100000.0
                    )

                kpis = st.text_area("衡量指標 (KPIs)", value=current.get("kpis") or "")
                strategy = st.text_area("策略/描述 (Strategy/Description)", value=current.get("strategy") or "")

                if st.form_submit_button("儲存變更"):
                    ap_svc.update(
                        product_id=edit_id,
                        product_name=product_name.strip(),
                        quota_fy26=quota_fy26,
                        strategy=strategy or None,
                        target_industry=current.get("target_industry"),
                        pillar=pillar,
                        owner=owner or None,
                        kpis=kpis or None,
                        status=status,
                        battlefront=battlefront or None,
                    )
                    st.success("舉措資料已更新。")
                    st.rerun()
