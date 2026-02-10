"""Pipeline Dashboard — funnel chart, stagnation alerts, overdue tasks, revenue forecast."""

from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from components.sidebar import render_sidebar
from constants import DEFAULT_STAGE_PROBABILITIES, INACTIVE_STATUSES, STATUS_CODES
from services import project as project_svc
from services import project_task as task_svc
from services import sales_plan as sp_svc
from services import settings as settings_svc
from services import stage_probability as prob_svc

render_sidebar()

headers = settings_svc.get_all_headers()
st.header(headers.get("header_pipeline", "業務漏斗"))

projects = project_svc.get_all()

if not projects:
    st.info("尚無專案資料。請先至售前管理或售後管理頁面新增專案。")
else:
    # --- Funnel bar chart ---
    st.subheader("各階段案件數量")

    df = pd.DataFrame(projects)

    # Group by stage: presale (L), postsale (P), LOST, HOLD
    def stage_group(code):
        if code in ("LOST", "HOLD"):
            return code
        if code.startswith("L"):
            return "售前"
        if code.startswith("P"):
            return "售後"
        return "?"

    # Count per individual status code
    status_counts = df["status_code"].value_counts().reset_index()
    status_counts.columns = ["status_code", "count"]
    status_counts["label"] = status_counts["status_code"].map(
        lambda c: f"{c} {STATUS_CODES.get(c, '')}"
    )
    status_counts["stage"] = status_counts["status_code"].apply(stage_group)

    # Sort: L0-L7, P0-P2, LOST, HOLD
    sort_order = ["L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7",
                  "P0", "P1", "P2", "LOST", "HOLD"]
    status_counts["sort_key"] = status_counts["status_code"].map(
        lambda c: sort_order.index(c) if c in sort_order else 99
    )
    status_counts = status_counts.sort_values("sort_key")

    # Color mapping: L series blue gradient, P series green gradient
    color_map = {
        "L0": "#a8d8ea", "L1": "#7ec8e3", "L2": "#5ab3d6",
        "L3": "#3498db", "L4": "#2980b9", "L5": "#2471a3",
        "L6": "#1f618d", "L7": "#1a5276",
        "P0": "#82e0aa", "P1": "#2ecc71", "P2": "#1e8449",
        "LOST": "#e74c3c", "HOLD": "#95a5a6",
    }

    fig = px.bar(
        status_counts,
        x="label",
        y="count",
        color="status_code",
        color_discrete_map=color_map,
        labels={"label": "狀態", "count": "案件數", "status_code": "狀態碼"},
    )
    fig.update_layout(showlegend=True, xaxis_tickangle=-45)
    st.plotly_chart(fig, width="stretch")

    # --- Stagnation alerts ---
    st.subheader("停滯警示")

    threshold = datetime.now().astimezone() - timedelta(days=14)
    stagnant = [
        p for p in projects
        if p["status_updated_at"] and p["status_updated_at"] < threshold
        and p["status_code"] not in INACTIVE_STATUSES
    ]

    if stagnant:
        for p in stagnant:
            days = (datetime.now().astimezone() - p["status_updated_at"]).days
            st.error(
                f"**[{p['status_code']} {STATUS_CODES.get(p['status_code'], '')}] {p['project_name']}** — "
                f"停滯 {days} 天（上次更新：{p['status_updated_at'].strftime('%Y-%m-%d')}）"
            )
    else:
        st.success("目前沒有停滯超過 14 天的案件。")

    # --- Overdue tasks ---
    st.subheader("逾期待辦")

    overdue_tasks = [t for t in task_svc.get_upcoming(days=0) if t["due_date"] < datetime.now().date()]
    if overdue_tasks:
        for t in overdue_tasks:
            days_overdue = (datetime.now().date() - t["due_date"]).days
            st.error(
                f"**{t['task_name']}** — {t.get('project_name', '')} "
                f"（{t.get('owner') or '未指派'}）逾期 {days_overdue} 天"
            )
    else:
        st.success("目前沒有逾期的待辦任務。")

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
            forecast_df["加權金額（手動）"] = forecast_df["amount"].astype(float) * forecast_df["confidence_level"].astype(float)

            # Stage probability weighting
            prob_rows = prob_svc.get_all()
            prob_map = {r["status_code"]: float(r["probability"]) for r in prob_rows}
            project_map = {p["project_id"]: p for p in projects}

            def _get_stage_prob(pid):
                proj = project_map.get(pid)
                if not proj:
                    return 0.5
                code = proj["status_code"]
                return prob_map.get(code, DEFAULT_STAGE_PROBABILITIES.get(code, 0.5))

            forecast_df["階段機率"] = forecast_df["project_id"].map(_get_stage_prob)
            forecast_df["加權金額（階段）"] = forecast_df["amount"].astype(float) * forecast_df["階段機率"]

            # Add project name for display
            forecast_df["專案名稱"] = forecast_df["project_id"].map(
                lambda pid: project_map.get(pid, {}).get("project_name", "?")
            )

            display_cols = [
                "plan_id", "專案名稱", "expected_invoice_date", "amount",
                "confidence_level", "加權金額（手動）", "階段機率", "加權金額（階段）",
            ]
            st.dataframe(
                forecast_df[[c for c in display_cols if c in forecast_df.columns]],
                width="stretch",
            )

            mc1, mc2 = st.columns(2)
            mc1.metric("手動信心加權總額", f"${forecast_df['加權金額（手動）'].sum():,.0f}")
            mc2.metric("階段機率加權總額", f"${forecast_df['加權金額（階段）'].sum():,.0f}")
        else:
            st.info("本月與下月無預計開票的商機。")
