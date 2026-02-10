"""Visual Board page — column board for presale pipeline (L0-L6)."""

from datetime import datetime

import streamlit as st

from components.sidebar import render_sidebar
from constants import PRESALE_STATUS_CODES, PRESALE_TRANSITIONS, STATUS_CODES
from services import crm as crm_svc
from services import project as project_svc

render_sidebar()

st.header("售前看板")

# Stage filter
all_stages = [k for k in PRESALE_STATUS_CODES if k != "L7"]  # L0-L6 (active presale)
selected_stages = st.multiselect(
    "顯示階段",
    options=all_stages,
    default=all_stages,
    format_func=lambda x: f"{x} {PRESALE_STATUS_CODES[x]}",
)

if not selected_stages:
    st.info("請選擇至少一個階段。")
    st.stop()

# Load data
projects = project_svc.get_presale()
client_map = {c["client_id"]: c["company_name"] for c in crm_svc.get_all()}

# Group by stage
stage_projects = {s: [] for s in selected_stages}
for p in projects:
    if p["status_code"] in stage_projects:
        stage_projects[p["status_code"]].append(p)

# Render columns
cols = st.columns(len(selected_stages))
now = datetime.now().astimezone()

for col, stage in zip(cols, selected_stages):
    with col:
        st.markdown(f"**{stage}**")
        st.caption(PRESALE_STATUS_CODES[stage])
        st.markdown(f"_{len(stage_projects[stage])} 件_")
        st.markdown("---")

        for p in stage_projects[stage]:
            # Calculate stagnation
            stagnant_days = 0
            if p.get("status_updated_at"):
                stagnant_days = (now - p["status_updated_at"]).days

            # Card style: red border for stagnation > 14 days
            if stagnant_days > 14:
                st.error(f"**{p['project_name']}**")
            else:
                st.markdown(f"**{p['project_name']}**")

            client_name = client_map.get(p.get("client_id"), "—")
            owner = p.get("presale_owner") or p.get("sales_owner") or "—"
            st.caption(f"{client_name}　|　{owner}")

            if stagnant_days > 0:
                st.caption(f"停滯 {stagnant_days} 天")

            # Advance button
            allowed = PRESALE_TRANSITIONS.get(stage, [])
            next_stage = [s for s in allowed if s.startswith("L") or s.startswith("P")]
            if next_stage:
                target = next_stage[0]
                label = f"→ {target}"
                if st.button(label, key=f"advance_{p['project_id']}"):
                    try:
                        project_svc.transition_status(p["project_id"], target)
                        if target == "L7":
                            st.success(f"{p['project_name']} 已簽約！")
                        else:
                            st.success(f"{p['project_name']} → {target}")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

            st.markdown("---")
