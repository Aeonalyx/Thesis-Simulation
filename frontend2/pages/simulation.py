import streamlit as st

from backend1.scheduler_engine1 import COLLEGES
from state import (
    clear_run_state,
    run_simulation_now,
    load_presets,
    save_presets,
    apply_ui_config,
    collect_ui_config,
    normalized_weights_from_ui,
)

from config import (
    SCHEDULER_OPTIONS,
    ALLOCATOR_OPTIONS,
    CRITERIA_KEYS,
)

from frontend2.componentss import (
    format_criterion_label,
    weight_state_key,
)

# ============================================================================
# SIDEBAR CONTROLS
# ============================================================================
def show_simulation():

    st.sidebar.header("🎛️ Simulation Controls")

    run_col, reset_col = st.sidebar.columns(2)
    run_clicked = run_col.button("🚀 Run", use_container_width=True)
    reset_clicked = reset_col.button("🧹 Reset", use_container_width=True)

    if reset_clicked:
        clear_run_state()
        st.rerun()

    st.sidebar.selectbox("Scheduler", SCHEDULER_OPTIONS, key="scheduler_type")
    st.sidebar.selectbox("Allocator", ALLOCATOR_OPTIONS, key="allocator_type")

    st.sidebar.subheader("Capacity and Policy")
    st.sidebar.slider(
        "Number of Staff",
        min_value=len(COLLEGES),
        max_value=len(COLLEGES) * 2,
        step=1,
        key="num_staff",
    )
    st.sidebar.slider("Daily Quota per Staff", min_value=1, max_value=60, step=1, key="quota_limit")

    max_absent_staff = max(0, int(st.session_state.num_staff) - 1)
    st.sidebar.checkbox(
        "Enable Staff Absence",
        key="enable_absence",
        disabled=(max_absent_staff == 0),
        help="Turn on to model staff being absent during the run.",
    )

    if max_absent_staff == 0:
        st.session_state.enable_absence = False
        st.session_state.num_absent_staff = 0
    elif st.session_state.enable_absence:
        if st.session_state.num_absent_staff < 1:
            st.session_state.num_absent_staff = 1
        if st.session_state.num_absent_staff > max_absent_staff:
            st.session_state.num_absent_staff = max_absent_staff

        st.sidebar.slider(
            "Number of Absent Staff",
            min_value=1,
            max_value=max_absent_staff,
            step=1,
            key="num_absent_staff",
        )
    else:
        st.session_state.num_absent_staff = 0

    st.sidebar.time_input("Workday Start", key="work_start_time")
    st.sidebar.time_input("Workday End", key="work_end_time")

    st.sidebar.subheader("Demand")
    st.sidebar.slider("Total Daily Requests", min_value=50, max_value=500, step=10, key="total_requests")
    st.sidebar.slider("Average Urgency (1-10)", min_value=1, max_value=10, step=1, key="urgency_base")
    st.sidebar.slider("College Imbalance (%)", min_value=0, max_value=100, step=5, key="imbalance_factor")

    st.sidebar.subheader("Seed")
    st.sidebar.radio("Seed Mode", ["Auto", "Manual"], key="seed_mode", horizontal=True)
    if st.session_state.seed_mode == "Manual":
        st.sidebar.number_input(
            "Manual Seed",
            min_value=1,
            max_value=2_147_483_647,
            step=1,
            key="manual_seed",
        )
    else:
        st.sidebar.caption("Auto mode will generate a seed and show it in the results.")

    if st.session_state.scheduler_type == "WEIGHTED":
        st.sidebar.subheader("Weighted Priority")
        for key in CRITERIA_KEYS:
            st.sidebar.slider(
                f"Weight: {format_criterion_label(key)}",
                min_value=0,
                max_value=100,
                step=1,
                key=weight_state_key(key),
            )

        current_weights = normalized_weights_from_ui()
        st.sidebar.caption(
            "Normalized: "
            + ", ".join(f"{format_criterion_label(k)}={v:.2f}" for k, v in current_weights.items())
        )
        st.sidebar.info("Tie-break rule: earlier submission_time wins when scores are equal.")

    st.sidebar.subheader("Presets")


    presets = load_presets()
    preset_names = ["(select)"] + sorted(list(presets.keys()))
    selected_preset = st.sidebar.selectbox("Saved Presets", preset_names)

    load_col, save_col = st.sidebar.columns(2)
    load_clicked = load_col.button("Load", use_container_width=True)
    save_clicked = save_col.button("Save", use_container_width=True)

    preset_name_input = st.sidebar.text_input("Preset Name", value="")

    if load_clicked and selected_preset in presets:
        apply_ui_config(presets[selected_preset])
        st.rerun()

    if save_clicked:
        name = preset_name_input.strip()
        if name:
            presets[name] = collect_ui_config()
            save_presets(presets)
            st.sidebar.success(f"Saved preset: {name}")
        else:
            st.sidebar.warning("Enter a preset name before saving.")

    if run_clicked:
        with st.spinner("Running simulation..."):
            # TEMP: will move to API layer later
            run_simulation_now()