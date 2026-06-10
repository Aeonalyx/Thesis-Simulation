import streamlit as st

from frontend2.components.state import initialize_state
from frontend2.components.context import get_context

from frontend2.ui.theme import apply_dashboard_theme
from frontend2.ui.sidebar import render_sidebar
from frontend2.ui.results import render_results, render_comparison
from frontend2.ui.metrics import render_metrics, export_tools
from frontend2.ui.playback import render_playback

st.set_page_config(
    page_title="Thesis Simulation Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 Registrar Queue Simulation Dashboard")
st.caption("Real-time simulation and analysis with playback, staffing, and weighted routing insights.")

initialize_state()
apply_dashboard_theme()
render_sidebar()

ctx = get_context()
snapshot = st.session_state.get("run_snapshot", {})

render_results(ctx, snapshot)
render_playback(ctx)
render_metrics(ctx)
render_comparison(ctx)
export_tools(ctx)
