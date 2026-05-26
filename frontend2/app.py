import streamlit as st

from frontend2.componentss import apply_theme
from state import initialize_state

from pages.dashboard import show_dashboard
from pages.results import show_results
from pages.results import show_playback, show_results, show_comparison, show_request_inspection

from core.context import get_context

st.set_page_config(
    page_title="Thesis Simulation Dashboard",
    page_icon="📊",
    layout="wide",
)

apply_theme()
initialize_state()

ctx = get_context()

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Playback", "Request Inspection", "Comparison"]
)

if page == "Dashboard":
    show_dashboard(ctx)

elif page == "Playback":
    show_results(ctx)

elif page == "Request Inspection":
    show_request_inspection(ctx)

elif page == "Comparison":
    show_comparison(ctx)