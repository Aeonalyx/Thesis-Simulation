import streamlit as st
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend1.scheduler_engine1 import (
COLLEGES, 
PRIORITY_ROC_WEIGHTS_FULL,
)

from components.config import (
SCHEDULER_OPTIONS,
SCHEDULER_LABELS,
ALLOCATOR_OPTIONS,
ALLOCATOR_LABELS,
PRIORITY_WEIGHTS,
format_criterion_label,
weight_state_key,
)

from components.simulation import ( 
run_simulation_now, 
normalized_weights_from_ui,
)

from components.state import (
clear_run_state, 
load_presets, 
save_presets,
apply_ui_config,
collect_ui_config,
active_criteria,
)

# ============================================================================
# SIDEBAR CONTROLS
# ============================================================================
def render_sidebar():
    st.sidebar.header("🎛️ Simulation Controls")

    run_col, reset_col = st.sidebar.columns(2)
    run_clicked = run_col.button("🚀 Run", use_container_width=True)
    reset_clicked = reset_col.button("🧹 Reset", use_container_width=True)

    if reset_clicked:
        clear_run_state()
        st.rerun()

    st.sidebar.selectbox(
        "Scheduler",
        SCHEDULER_OPTIONS,
        key="scheduler_type",
        format_func=lambda value: SCHEDULER_LABELS.get(value, value),
    )
    st.sidebar.selectbox(
        "Allocator",
        ALLOCATOR_OPTIONS,
        key="allocator_type",
        format_func=lambda value: ALLOCATOR_LABELS.get(value, value.replace("_", " ").title()),
    )

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
    st.sidebar.checkbox("Enable Urgency", value=False, key="urgency")
    def on_peak_mode_change():
        if st.session_state.peak_mode:
            # store original ONLY once
            if "base_total_requests" not in st.session_state:
                st.session_state.base_total_requests = st.session_state.total_requests

            st.session_state.total_requests = 300
        else:
            # restore safely
            if "base_total_requests" in st.session_state:
                st.session_state.total_requests = st.session_state.base_total_requests

    st.sidebar.checkbox("Peak Period", value=False, key="peak_mode", on_change=on_peak_mode_change)
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
        for key in active_criteria():
            state_key = weight_state_key(key)
            if state_key not in st.session_state:
                # Use PRIORITY_ROC_WEIGHTS_FULL for urgency to get the correct ROC default
                if key == "urgency":
                    default_raw = PRIORITY_ROC_WEIGHTS_FULL.get(key, 0.02)
                else:
                    default_raw = PRIORITY_WEIGHTS.get(key, 0.0)
                default_val = int(default_raw * 100) if isinstance(default_raw, (int, float)) else 50
                st.session_state[state_key] = default_val

        for key in active_criteria():
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
    # 🔍 DEBUG: Urgency Toggle Verification
    if st.session_state.simulation_engine is not None:
        with st.sidebar.expander("🐛 Debug: Urgency Status", expanded=False):
            st.markdown(f"**Checkbox State:** `{st.session_state.urgency}`")
            st.markdown(f"**ROC Weight for Urgency:** `{PRIORITY_WEIGHTS.get('urgency', 'N/A')}`")
                
            if st.session_state.simulation_results and st.session_state.simulation_results.get('completed_requests'):
                sample = st.session_state.simulation_results['completed_requests'][0]
                st.markdown(f"**Sample Request `{sample['request_id']}` Priority:** `{sample['priority_score']}`")
                st.caption("Run twice (checkbox OFF/ON) to compare this number.")

    if run_clicked:
        with st.spinner("Running simulation..."):
            run_simulation_now()