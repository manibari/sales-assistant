"""Post-closure page — view closed projects (P2, LOST, HOLD) grouped by client."""

import json

import pandas as pd
import streamlit as st

from components.selectors import get_product_map, map_id_columns
from components.sidebar import render_sidebar
from constants import STATUS_CODES
from services import project as project_svc
from services import settings as settings_svc

render_sidebar()

headers = settings_svc.get_all_headers()
st.header(headers.get("header_post_closure", "已結案客戶"))

# --- Load data ---
all_closed = project_svc.get_closed()

# --- Metrics ---
counts = {"P2": 0, "LOST": 0, "HOLD": 0}
for p in all_closed:
    if p["status_code"] in counts:
        counts[p["status_code"]] += 1

col1, col2, col3 = st.columns(3)
col1.metric("P2 驗收完成", counts["P2"])
col2.metric("LOST 遺失", counts["LOST"])
col3.metric("HOLD 擱置", counts["HOLD"])

st.divider()

# --- Filter ---
status_filter = st.multiselect(
    "狀態篩選",
    options=["P2", "LOST", "HOLD"],
    default=["P2", "LOST", "HOLD"],
    format_func=lambda x: f"{x} — {STATUS_CODES.get(x, '')}",
)

filtered = [p for p in all_closed if p["status_code"] in status_filter]

if not filtered:
    st.info("沒有符合篩選條件的結案專案。")
else:
    # Group by client
    clients = {}
    for p in filtered:
        client_name = p.get("company_name") or "（未指定客戶）"
        clients.setdefault(client_name, {"info": p, "projects": []})
        clients[client_name]["projects"].append(p)

    product_map = get_product_map()

    for client_name, data in clients.items():
        info = data["info"]
        projects = data["projects"]
        with st.expander(f"{client_name}（{len(projects)} 筆）", expanded=True):
            # Client info
            detail_cols = st.columns(4)
            detail_cols[0].markdown(f"**產業**：{info.get('industry') or '—'}")
            detail_cols[1].markdown(f"**部門**：{info.get('department') or '—'}")

            dm = info.get("decision_maker")
            if isinstance(dm, str):
                dm = json.loads(dm)
            dm_name = dm.get("name", "—") if isinstance(dm, dict) else "—"
            detail_cols[2].markdown(f"**決策者**：{dm_name}")

            champs = info.get("champions") or []
            if isinstance(champs, str):
                champs = json.loads(champs)
            if isinstance(champs, dict):
                champs = [champs]
            champ_name = champs[0].get("name", "—") if champs else "—"
            detail_cols[3].markdown(f"**Champion**：{champ_name}")

            # Project list
            df = pd.DataFrame(projects)
            map_id_columns(df, product_map=product_map)
            display_cols = ["project_id", "project_name", "product_id",
                            "status_code", "sales_owner", "presale_owner", "postsale_owner",
                            "priority", "status_updated_at"]
            st.dataframe(
                df[[c for c in display_cols if c in df.columns]],
                width="stretch",
            )
