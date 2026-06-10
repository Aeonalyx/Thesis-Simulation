import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from plotly.subplots import make_subplots
from typing import List, Dict
from ui.theme import apply_plot_theme

from frontend2.components.config import (
format_variant_label,
)

from frontend2.components.simulation import (
parse_event_time,
format_compact_datetime, 
format_compact_day, 
)

from frontend2.components.state import (
initialize_state, 
)


# ============================================================================
# CHARTS
# ============================================================================
def render_theme_table(df: pd.DataFrame, height_px: int = 320):
    if df is None or df.empty:
        return
    safe_df = df.fillna("")
    table_html = safe_df.to_html(index=False, classes="theme-table", border=0)
    st.markdown(
        f'<div class="theme-table-wrap" style="max-height:{int(height_px)}px;">{table_html}</div>',
        unsafe_allow_html=True,
    )

def build_baseline_queue_dynamics_chart(event_log: List[Dict], variant_label: str = "") -> go.Figure:
    if not event_log:
        return go.Figure()

    sorted_log = sorted(
        event_log,
        key=lambda ev: (
            parse_event_time(str(ev.get("time", ""))),
            ev.get("sequence", 0),
        ),
    )

    active_requests = set()
    queue_sizes = []
    avg_waits = []
    time_points = []
    observed_waits = []

    for event in sorted_log:
        event_type = str(event.get("event_type", "")).upper()
        request_id = event.get("request_id")

        if event_type == "ARRIVAL" and request_id:
            active_requests.add(request_id)
        elif event_type == "ASSIGN" and request_id:
            active_requests.discard(request_id)
            wait_hours = float(event.get("queue_wait_hours", 0.0) or 0.0)
            observed_waits.append(wait_hours)

        current_time = parse_event_time(str(event.get("time", "")))
        time_points.append(current_time)
        queue_sizes.append(len(active_requests))
        avg_waits.append(round(sum(observed_waits) / len(observed_waits), 2) if observed_waits else 0.0)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=time_points,
            y=queue_sizes,
            mode="lines+markers",
            name="Queue Size",
            marker=dict(size=6),
            line=dict(width=2, color="#a855f7"),
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=time_points,
            y=avg_waits,
            mode="lines+markers",
            name="Avg Waiting Time (h)",
            marker=dict(size=6),
            line=dict(width=2, color="#22d3ee"),
        ),
        secondary_y=True,
    )

    chart_title = "Queue Dynamics and Waiting Time Trend"
    if variant_label:
        chart_title = f"{chart_title} — {variant_label}"

    fig.update_layout(
        title=chart_title,
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(title_text="Simulation Time")
    fig.update_yaxes(title_text="Queue Size", secondary_y=False)
    fig.update_yaxes(title_text="Average Queue Wait (h)", secondary_y=True)
    apply_plot_theme(fig)
    return fig


def build_weighted_priority_distribution_chart(
    requests: List[Dict], selected_doc_types: List[str], variant_label: str = ""
) -> go.Figure:
    rows = []
    for req in requests:
        if not req:
            continue

        if isinstance(req, dict):
            score = float(req.get("priority_score", 0.0) or 0.0)
            assigned = bool(req.get("assignment_time"))
            doc_type = req.get("document_type", "Unknown")
        else:
            score = float(getattr(req, "priority_score", 0.0) or 0.0)
            assigned = getattr(req, "assignment_time", None) is not None
            doc_type = getattr(req, "document_type", "Unknown")

        if selected_doc_types and doc_type not in selected_doc_types:
            continue

        rows.append(
            {
                "Priority Score": score,
                "Status": "Assigned" if assigned else "Unassigned",
                "Document Type": doc_type,
            }
        )

    if not rows:
        return go.Figure()

    df = pd.DataFrame(rows)
    chart_title = "Priority Score Distribution by Request Type"
    if variant_label:
        chart_title = f"{chart_title} — {variant_label}"

    fig = px.histogram(
        df,
        x="Priority Score",
        color="Document Type",
        barmode="overlay",
        nbins=20,
        histnorm="percent",
        title=chart_title,
        labels={
            "Priority Score": "Priority Score",
            "Document Type": "Request Type",
        },
        height=420,
    )
    fig.update_traces(opacity=0.75)
    fig.update_layout(
        legend=dict(title="Request Type", orientation="h", y=1.02, x=0.5, xanchor="center")
    )
    apply_plot_theme(fig)
    return fig


def build_workload_imbalance_chart(compare_df: pd.DataFrame, title: str = "Workload Imbalance and Utilization Variance") -> go.Figure:
    if compare_df is None or compare_df.empty:
        return go.Figure()

    df = compare_df.copy()
    df["variant"] = df.apply(
        lambda row: format_variant_label(row["scheduler"], row["allocator"]),
        axis=1,
    )

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=df["variant"],
            y=df["staff_load_std"],
            name="Staff Load Std Dev",
            marker_color="#a855f7",
            text=df["staff_load_std"],
            textposition="outside",
            customdata=df[["avg_waiting_time_hours"]],
            hovertemplate="%{x}<br>Std Dev: %{y}<br>Avg Wait: %{customdata[0]} h<extra></extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df["variant"],
            y=df["staff_load_cv"],
            name="Staff Load CV",
            mode="lines+markers",
            marker=dict(color="#22d3ee", size=8),
            line=dict(width=2),
        ),
        secondary_y=True,
    )
    fig.update_layout(
        title="Workload Imbalance by Variant",
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(title_text="Variant")
    fig.update_yaxes(title_text="Staff Load Std Dev", secondary_y=False)
    fig.update_yaxes(title_text="Staff Load CV", secondary_y=True)
    apply_plot_theme(fig)
    return fig

def build_variant_summary_chart(compare_df: pd.DataFrame, title: str = "Summary of Variant Performance") -> go.Figure:
    if compare_df is None or compare_df.empty:
        return go.Figure()

    df = compare_df.copy()

    df["variant"] = df.apply(
        lambda row: format_variant_label(row["scheduler"], row["allocator"]),
        axis=1,
    )

    summary_df = df.melt(
        id_vars=["variant"],
        value_vars=[
            "avg_waiting_time_hours",
            "throughput_req_per_day",
            "staff_load_std",
        ],
        var_name="metric",
        value_name="value",
    )

    metric_names = {
        "avg_waiting_time_hours": "Avg Waiting Time (h)",
        "throughput_req_per_day": "Throughput (req/day)",
        "staff_load_std": "Staff Load Std Dev",
    }

    summary_df["metric"] = summary_df["metric"].map(metric_names)

    summary_df["result_no"] = summary_df.groupby("metric").cumcount() + 1

    fig = px.bar(
        summary_df,
        x="variant",
        y="value",
        color="metric",
        barmode="group",
        title=title,
        height=500,
        labels={"variant": "Variant", "value": "Metric Value", "metric": "Metric"},
        text="value", 
    )

    fig.update_traces(
        textposition="outside",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Metric: %{legendgroup}<br>"
            "Value: %{y:.4f}<br>"
            "Result #: %{customdata}<extra></extra>"
        ),
        customdata=summary_df[["result_no"]],
    )

    apply_plot_theme(fig)

    return fig

def staff_rows_with_day_separators(rows: List[Dict]) -> List[Dict]:
    """Keep full staff history and visually separate each assignment day."""
    if not rows:
        return []

    ordered_rows = sorted(
        rows,
        key=lambda item: parse_event_time(str(item.get("Assigned At", ""))),
    )

    display_rows: List[Dict] = []
    last_day = None
    day_block = 0
    day_count = 0

    for row in ordered_rows:
        assigned_at_raw = row.get("Assigned At")
        assigned_at_dt = parse_event_time(str(assigned_at_raw)) if assigned_at_raw else None
        assigned_day = assigned_at_dt.date() if assigned_at_dt else None

        if assigned_day != last_day:
            if last_day is not None:
                # Insert a visible day divider row between day blocks.
                divider_text = f"--- Day {day_block + 1} Start ({format_compact_day(assigned_day)}) ---"
                display_rows.append(
                    {
                        "Day Block": divider_text,
                        "Count": "",
                        "Request": "",
                        "College": "",
                        "Document": "",
                        "Priority Score": "",
                        "Queue Wait (h)": "",
                        "Assigned At": "",
                    }
                )
            day_block += 1
            day_label = f"Day {day_block} ({format_compact_day(assigned_day)})"
            day_count = 0
        else:
            day_label = ""

        day_count += 1
        display_rows.append(
            {
                "Day Block": day_label,
                "Count": day_count,
                "Request": row.get("Request", ""),
                "College": row.get("College", ""),
                "Document": row.get("Document", ""),
                "Priority Score": row.get("Priority Score", ""),
                "Queue Wait (h)": row.get("Queue Wait (h)", ""),
                "Assigned At": format_compact_datetime(row.get("Assigned At", "")),
            }
        )
        last_day = assigned_day

    return display_rows


initialize_state()