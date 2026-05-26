from config import CRITERIA_LABELS
import streamlit as st
from typing import Dict, Optional, List
import datetime
import pandas as pd
import plotly.graph_objects as go


def format_criterion_label(key: str) -> str:
    return CRITERIA_LABELS.get(key, key.replace("_", " ").title())


def weight_state_key(key: str) -> str:
    return f"w_{key}"

st.set_page_config(
    page_title="Thesis Simulation Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_theme():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Space+Grotesk:wght@500;700&display=swap');

        :root {
            --bg-soft: #0f0d1b;
            --panel: #161626;
            --panel-2: #1d1b31;
            --ink: #f5f3ff;
            --ink-soft: #b6b0d4;
            --line: #2f2a47;
            --accent-a: #a855f7;
            --accent-b: #7c3aed;
            --accent-c: #22d3ee;
            --ok: #10b981;
        }

        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(980px 420px at 96% 0%, rgba(168, 85, 247, 0.20), transparent 60%),
                radial-gradient(860px 360px at 0% 18%, rgba(34, 211, 238, 0.13), transparent 60%),
                linear-gradient(150deg, #0b0b12 0%, #161127 45%, #22163d 100%);
        }

        .stApp, [data-testid="stSidebar"] {
            font-family: 'Plus Jakarta Sans', 'Segoe UI', sans-serif;
            color: var(--ink);
        }

        [data-testid="stAppViewContainer"] .main,
        [data-testid="stAppViewContainer"] .main * {
            color: var(--ink);
        }

        [data-testid="stHeader"] {
            background: rgba(0, 0, 0, 0);
        }

        .main .block-container {
            padding-top: 1.2rem;
            padding-bottom: 2.2rem;
        }

        h1, h2, h3 {
            font-family: 'Space Grotesk', 'Plus Jakarta Sans', sans-serif;
            letter-spacing: 0.2px;
        }

        [data-testid="stCaptionContainer"], .stCaption {
            color: var(--ink-soft) !important;
        }

        [data-testid="stAlert"] {
            background: rgba(29, 27, 49, 0.82);
            border: 1px solid var(--line);
            color: var(--ink);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #121023 0%, #191630 100%);
            border-right: 1px solid var(--line);
        }

        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] .stMarkdown {
            color: var(--ink) !important;
        }

        [data-testid="stSidebar"] .stSlider,
        [data-testid="stSidebar"] .stNumberInput,
        [data-testid="stSidebar"] .stSelectbox,
        [data-testid="stSidebar"] .stTextInput,
        [data-testid="stSidebar"] .stTimeInput {
            background: transparent;
        }

        [data-testid="stMetric"] {
            background: linear-gradient(160deg, #1a1730 0%, #141326 100%);
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 0.55rem 0.8rem;
            box-shadow: 0 10px 26px rgba(7, 6, 13, 0.45);
        }

        [data-testid="stMetricLabel"] {
            color: var(--ink-soft);
            font-weight: 600;
        }

        [data-testid="stMetricValue"] {
            color: var(--ink);
            font-weight: 800;
        }

        .stButton > button {
            border-radius: 10px;
            border: 1px solid #3c325e;
            background: linear-gradient(140deg, #1f1b33 0%, #151226 100%);
            color: #f8f7ff;
            font-weight: 700;
            box-shadow: 0 8px 18px rgba(6, 4, 12, 0.38);
        }

        .stButton > button:hover {
            border-color: #8b5cf6;
            background: linear-gradient(120deg, #6d28d9 0%, #a855f7 62%, #22d3ee 100%);
            color: #ffffff;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid var(--line);
            border-radius: 12px;
            overflow: hidden;
            background: linear-gradient(180deg, #221a39 0%, #1c1731 100%);
            box-shadow: 0 12px 28px rgba(5, 3, 10, 0.45);
        }

        div[data-testid="stDataFrame"] [role="grid"],
        div[data-testid="stDataFrame"] [data-testid="stDataFrameResizable"],
        div[data-testid="stDataFrame"] table {
            background: #241c3d !important;
            color: #e4def8 !important;
        }

        div[data-testid="stDataFrame"] [role="columnheader"],
        div[data-testid="stDataFrame"] th {
            background: #35245a !important;
            color: #f2ebff !important;
            border-bottom: 1px solid #513a7a !important;
        }

        div[data-testid="stDataFrame"] [role="gridcell"],
        div[data-testid="stDataFrame"] td {
            background: rgba(44, 34, 69, 0.55) !important;
            border-bottom: 1px solid #30254a !important;
            color: #e4def8 !important;
        }

        div[data-testid="stDataFrame"] [role="row"]:hover [role="gridcell"],
        div[data-testid="stDataFrame"] tr:hover td {
            background: rgba(88, 62, 129, 0.50) !important;
        }

        .stPlotlyChart {
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 0.35rem;
            background: linear-gradient(180deg, rgba(42, 30, 67, 0.82) 0%, rgba(27, 22, 46, 0.86) 100%);
            box-shadow: 0 14px 30px rgba(6, 4, 12, 0.45);
        }

        .theme-table-wrap {
            border: 1px solid #4a3470;
            border-radius: 12px;
            overflow: auto;
            background: linear-gradient(180deg, #1f1735 0%, #171227 100%);
            box-shadow: inset 0 0 0 1px rgba(137, 93, 205, 0.10);
        }

        .theme-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.86rem;
            color: #e7e1fa;
            min-width: 760px;
        }

        .theme-table thead th {
            position: sticky;
            top: 0;
            z-index: 2;
            background: linear-gradient(180deg, #3c2a62 0%, #2e214c 100%);
            color: #f3edff;
            font-weight: 700;
            text-align: left;
            padding: 0.52rem 0.56rem;
            border-bottom: 1px solid #5b4487;
            white-space: nowrap;
        }

        .theme-table tbody td {
            padding: 0.44rem 0.56rem;
            border-bottom: 1px solid #30264b;
            color: #ddd4f5;
            white-space: nowrap;
        }

        .theme-table tbody tr:nth-child(odd) td {
            background: rgba(36, 27, 57, 0.72);
        }

        .theme-table tbody tr:nth-child(even) td {
            background: rgba(30, 23, 48, 0.72);
        }

        .theme-table tbody tr:hover td {
            background: rgba(110, 78, 164, 0.36);
            color: #f3edff;
        }

        .theme-table tbody td:last-child,
        .theme-table thead th:last-child {
            text-align: right;
        }

        .hero-band {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            margin: 0.1rem 0 1rem;
            padding: 0.9rem 1rem;
            border-radius: 14px;
            border: 1px solid rgba(168, 85, 247, 0.5);
            background: linear-gradient(105deg, #21143a 0%, #3f1b78 48%, #5c2a9d 78%, #2a8eb3 100%);
            color: #f8fafc;
            box-shadow: 0 18px 34px rgba(14, 9, 24, 0.52);
        }

        .hero-band p {
            margin: 0;
            line-height: 1.3;
        }

        .hero-kicker {
            font-size: 0.72rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            opacity: 0.9;
            font-weight: 700;
        }

        .hero-title {
            font-size: 1.08rem;
            font-weight: 800;
            margin-top: 0.18rem;
        }

        .hero-sub {
            font-size: 0.82rem;
            opacity: 0.92;
            margin-top: 0.24rem;
        }

        .hero-pill {
            display: inline-flex;
            align-items: center;
            border: 1px solid rgba(255, 255, 255, 0.5);
            border-radius: 999px;
            padding: 0.28rem 0.7rem;
            font-weight: 700;
            font-size: 0.8rem;
            background: rgba(255, 255, 255, 0.14);
            white-space: nowrap;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def parse_event_time(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return datetime.now()


def format_compact_datetime(value) -> str:
    if value in (None, "", "-"):
        return "-"
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value))
        except Exception:
            return str(value)
    return dt.strftime("%b %d %H:%M")


def format_compact_day(day_value) -> str:
    if day_value is None:
        return "-"
    try:
        return day_value.strftime("%b %d, %Y")
    except Exception:
        return str(day_value)
    
def build_staff_college_map(staff_pool) -> Dict[str, Dict[str, str]]:
    mapping: Dict[str, Dict[str, str]] = {}
    for staff in staff_pool:
        mapping[str(staff.staff_id)] = {
            "college": str(staff.college_affiliation),
            "name": str(getattr(staff, "name", "")),
        }
    return mapping


def format_staff_label(staff_id: Optional[str], staff_map: Dict[str, Dict[str, str]]) -> str:
    if not staff_id:
        return "UNASSIGNED"
    staff_text = str(staff_id)
    if staff_text.upper() == "UNASSIGNED":
        return "UNASSIGNED"
    meta = staff_map.get(staff_text, {})
    college = str(meta.get("college", "")).strip()
    if college:
        return f"{staff_text} ({college})"
    return staff_text


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
        else:
            day_label = ""

        display_rows.append(
            {
                "Day Block": day_label,
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


CHART_COLORWAY = ["#a855f7", "#7c3aed", "#22d3ee", "#c084fc", "#38bdf8", "#f472b6"]

def apply_plot_theme(fig: go.Figure):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(28,22,46,0.92)",
        colorway=CHART_COLORWAY,
        font=dict(color="#ebe5ff", family="Plus Jakarta Sans, Segoe UI, sans-serif"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#d9d2f0")),
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(111,87,164,0.28)",
        zeroline=False,
        linecolor="rgba(130,105,190,0.45)",
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(111,87,164,0.28)",
        zeroline=False,
        linecolor="rgba(130,105,190,0.45)",
    )


def render_theme_table(df: pd.DataFrame, height_px: int = 320):
    if df is None or df.empty:
        return
    safe_df = df.fillna("")
    table_html = safe_df.to_html(index=False, classes="theme-table", border=0)
    st.markdown(
        f'<div class="theme-table-wrap" style="max-height:{int(height_px)}px;">{table_html}</div>',
        unsafe_allow_html=True,
    )

def routing_events(event_log: List[Dict]) -> List[Dict]:
    """Keep only request-routing decisions for request-by-request playback."""
    decision_types = {"ASSIGN", "WAITING"}
    return [event for event in event_log if event.get("event_type") in decision_types]


def playback_state(decisions: List[Dict], step: int) -> Dict:
    if not decisions:
        return {
            "current_event": None,
            "assignments": [],
            "waiting": [],
            "processed_count": 0,
            "assigned_count": 0,
            "waiting_count": 0,
            "staff_flow": {},
        }

    step = max(0, min(step, len(decisions) - 1))
    chunk = decisions[: step + 1]

    assignments = []
    waiting = []
    staff_flow: Dict[str, List[str]] = {}

    for item in chunk:
        kind = item.get("event_type")
        if kind == "ASSIGN":
            assignments.append(
                {
                    "Time": item.get("time"),
                    "Request": item.get("request_id"),
                    "College": item.get("college"),
                    "Staff": item.get("staff_id"),
                    "Priority Score": item.get("priority_score", 0.0),
                    "Queue Wait (h)": item.get("queue_wait_hours", "-"),
                    "Mode": item.get("details", ""),
                }
            )
            staff_key = item.get("staff_id") or "UNASSIGNED"
            staff_flow.setdefault(staff_key, []).append(item.get("request_id"))
        elif kind == "WAITING":
            waiting.append(
                {
                    "Time": item.get("time"),
                    "Request": item.get("request_id"),
                    "College": item.get("college"),
                    "Priority Score": item.get("priority_score", 0.0),
                    "Reason": item.get("details", ""),
                }
            )

    return {
        "current_event": chunk[-1],
        "assignments": assignments,
        "waiting": waiting,
        "processed_count": len(chunk),
        "assigned_count": len(assignments),
        "waiting_count": len(waiting),
        "staff_flow": staff_flow,
    }

def render_kpi_section(results, total_requests):
    st.header("Key Metrics")

    k1, k2, k3, k4, k5 = st.columns(5)

    processed = int(results.get("total_processed", 0))
    expected = int(total_requests)

    pct = (processed / expected * 100.0) if expected > 0 else 0.0

    with k1:
        st.metric("Total Processed", f"{processed}/{expected}", f"{pct:.0f}%")

    with k2:
        avg_wait_hours = float(results.get("avg_waiting_time_hours", 0.0))
        st.metric("Avg Queue Wait", f"{avg_wait_hours:.2f} h")

    with k3:
        avg_turn_days = float(results.get("avg_turnaround_days", 0.0))
        st.metric("Avg Turnaround", f"{avg_turn_days:.2f} d")

    with k4:
        elapsed_days = float(results.get("total_days_elapsed", 0.0))
        st.metric("Days Elapsed", f"{elapsed_days:.2f} d")

    with k5:
        st.metric("Throughput", f"{results.get('throughput_req_per_day', 0):.2f} req/day")

    if results.get("absent_staff"):
        st.warning("Absent staff: " + ", ".join(results.get("absent_staff", [])))

""" 
def render_kpi_section(results, total_requests):
    st.header("Key Metrics")

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        processed = int(results.get("total_processed", 0))
        expected = int(st.session_state.total_requests)
        pct = (processed / expected * 100.0) if expected > 0 else 0.0
        st.metric("Total Processed", f"{processed}/{expected}", f"{pct:.0f}%")
    with k2:
        avg_wait_hours = float(results.get("avg_waiting_time_hours", 0.0))
        st.metric(
            "Avg Queue Wait",
            f"{avg_wait_hours:.2f} h",
            f"{(avg_wait_hours / 24.0):.2f} d equiv",
        )
    with k3:
        avg_turn_days = float(results.get("avg_turnaround_days", 0.0))
        st.metric(
            "Avg Turnaround",
            f"{avg_turn_days:.2f} d",
            f"{(avg_turn_days * 24.0):.2f} h equiv",
        )
    with k4:
        elapsed_days = float(results.get("total_days_elapsed", 0.0))
        st.metric(
            "Days Elapsed",
            f"{elapsed_days:.2f} d",
            f"{(elapsed_days * 24.0):.2f} h equiv",
        )
    with k5:
        st.metric("Throughput", f"{results.get('throughput_req_per_day', 0):.2f} req/day")

    if results.get("absent_staff"):
        st.warning("Absent staff: " + ", ".join(results.get("absent_staff", []))) 
"""