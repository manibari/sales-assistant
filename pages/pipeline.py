"""Pipeline Dashboard — funnel chart, stagnation alerts, revenue forecast."""

from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from components.sidebar import render_sidebar
from constants import STATUS_CODES
from services import project as project_svc
from services import sales_plan as sp_svc
from services import settings as settings_svc

render_sidebar()

headers = settings_svc.get_all_headers()
st.header(headers.get("header_pipeline", "業務漏斗"))

projects = project_svc.get_all()

if not projects:
    st.info("尚無專案資料。請先至專案管理頁面新增專案。")
else:
    # --- Funnel bar chart ---
    st.subheader("各階段案件數量")

    df = pd.DataFrame(projects)

    # Group by stage prefix (S/T/C/D/LOST/HOLD)
    def stage_group(code):
        if code in ("LOST", "HOLD"):
            return code
        return code[0] if code else "?"

    df["stage"] = df["status_code"].apply(stage_group)

    # Count per individual status code
    status_counts = df["status_code"].value_counts().reset_index()
    status_counts.columns = ["status_code", "count"]
    status_counts["label"] = status_counts["status_code"].map(
        lambda c: f"{c} {STATUS_CODES.get(c, '')}"
    )
    status_counts["stage"] = status_counts["status_code"].apply(stage_group)
    status_counts = status_counts.sort_values("status_code")

    fig = px.bar(
        status_counts,
        x="label",
        y="count",
        color="stage",
        color_discrete_map={"S": "#3498db", "T": "#9b59b6", "C": "#e67e22", "D": "#2ecc71", "LOST": "#e74c3c", "HOLD": "#95a5a6"},
        labels={"label": "狀態", "count": "案件數", "stage": "階段"},
    )
    fig.update_layout(showlegend=True, xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    # --- Stagnation alerts ---
    st.subheader("停滯警示")

    threshold = datetime.now().astimezone() - timedelta(days=14)
    stagnant = [
        p for p in projects
        if p["status_updated_at"] and p["status_updated_at"] < threshold
        and p["status_code"] not in ("D03", "LOST", "HOLD")
    ]

    if stagnant:
        for p in stagnant:
            days = (datetime.now().astimezone() - p["status_updated_at"]).days
            st.error(
                f"**[{p['status_code']}] {p['project_name']}** — "
                f"停滯 {days} 天（上次更新：{p['status_updated_at'].strftime('%Y-%m-%d')}）"
            )
    else:
        st.success("目前沒有停滯超過 14 天的案件。")

    # --- Revenue forecast ---
    st.subheader("業績預測（本月 / 下月）")

    plans = sp_svc.get_all()
    if not plans:
        st.info("尚無商機預測資料。")
    else:
        today = datetime.now().date()
        this_month_start = today.replace(day=1)
        if today.month == 12:
            next_month_start = today.replace(year=today.year + 1, month=1, day=1)
            month_after_start = today.replace(year=today.year + 1, month=2, day=1)
        else:
            next_month_start = today.replace(month=today.month + 1, day=1)
            if today.month + 1 == 12:
                month_after_start = today.replace(year=today.year + 1, month=1, day=1)
            else:
                month_after_start = today.replace(month=today.month + 2, day=1)

        forecast_plans = [
            p for p in plans
            if p["expected_invoice_date"] and this_month_start <= p["expected_invoice_date"] < month_after_start
        ]

        if forecast_plans:
            forecast_df = pd.DataFrame(forecast_plans)
            forecast_df["加權金額"] = forecast_df["amount"].astype(float) * forecast_df["confidence_level"].astype(float)

            # Add project name for display
            project_map = {p["project_id"]: p["project_name"] for p in projects}
            forecast_df["專案名稱"] = forecast_df["project_id"].map(project_map)

            display_cols = ["plan_id", "專案名稱", "expected_invoice_date", "amount", "confidence_level", "加權金額"]
            st.dataframe(
                forecast_df[[c for c in display_cols if c in forecast_df.columns]],
                use_container_width=True,
            )
            st.metric("加權總額", f"${forecast_df['加權金額'].sum():,.0f}")
        else:
            st.info("本月與下月無預計開票的商機。")
