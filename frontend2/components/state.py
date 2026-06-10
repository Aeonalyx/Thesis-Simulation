from datetime import time, datetime
from frontend2.components.config import weight_state_key
from frontend2.components.config import CRITERIA_KEYS, PRIORITY_WEIGHTS, PRESET_FILE
from backend2.config import COLLEGES
from typing import List, Dict

import os
import json
import streamlit as st

# ============================================================================
# DEFAULT STATE
# ============================================================================

WEIGHT_DEFAULT_STATE = {
    weight_state_key(key): int(PRIORITY_WEIGHTS.get(key, 0.0) * 100)
    for key in CRITERIA_KEYS
}

DEFAULT_STATE = {
    "scheduler_type": "FCFS",
    "allocator_type": "college_based",
    "num_staff": len(COLLEGES),
    "quota_limit": 20,
    "enable_absence": False,
    "total_requests": 100,
    "imbalance_factor": 0,
    "num_absent_staff": 0,
    "peak_mode": False,
    "work_start_time": time(8, 0),
    "work_end_time": time(17, 0),
    "seed_mode": "Auto",
    "manual_seed": 12345,
    **WEIGHT_DEFAULT_STATE,
    "playback_frame": 0,
    "playback_frame_ui": 1,
    "playback_speed": "1.00x",
    "playback_playing": False,
    "urgency": False,
}

# ============================================================================
# UI STATE HELPERS
# ============================================================================

def active_criteria() -> List[str]:
    """Return the list of criteria to render in the UI based on urgency toggle."""
    keys = list(CRITERIA_KEYS)
    if st.session_state.get("urgency", False) and "urgency" not in keys:
        keys = keys + ["urgency"]
    return keys

def on_playback_slider_change():
    """Sync slider position to internal request-step state and pause autoplay."""
    st.session_state.playback_playing = False
    st.session_state.playback_frame = max(0, int(st.session_state.playback_frame_ui) - 1)

# ============================================================================
# STATE MANAGEMENT
# ============================================================================

def initialize_state():
    for key, value in DEFAULT_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if "simulation_engine" not in st.session_state:
        st.session_state.simulation_engine = None
    if "simulation_results" not in st.session_state:
        st.session_state.simulation_results = None
    if "comparison_df" not in st.session_state:
        st.session_state.comparison_df = None
    if "last_run_config" not in st.session_state:
        st.session_state.last_run_config = None

def clear_run_state():
    st.session_state.simulation_engine = None
    st.session_state.simulation_results = None
    st.session_state.comparison_df = None
    st.session_state.last_run_config = None
    st.session_state.playback_frame = 0
    st.session_state.playback_frame_ui = 1
    st.session_state.playback_playing = False
    st.session_state.comparison_df = None
    st.session_state.run_snapshot = {}

# ============================================================================
# SIMULATION CONFIG BUILDERS
# ============================================================================

def collect_ui_config() -> Dict:
    return {
        "scheduler_type": st.session_state.scheduler_type,
        "allocator_type": st.session_state.allocator_type,
        "num_staff": int(st.session_state.num_staff),
        "quota_limit": int(st.session_state.quota_limit),
        "enable_absence": bool(st.session_state.enable_absence),
        "total_requests": int(st.session_state.total_requests),
        "peak_mode": bool(st.session_state.peak_mode),
        "urgency": bool(st.session_state.urgency),
        "imbalance_factor": int(st.session_state.imbalance_factor),
        "num_absent_staff": int(st.session_state.num_absent_staff),
        "work_start": st.session_state.work_start_time.strftime("%H:%M"),
        "work_end": st.session_state.work_end_time.strftime("%H:%M"),
        "seed_mode": st.session_state.seed_mode,
        "manual_seed": int(st.session_state.manual_seed),
        "weights_raw": {
            key: int(st.session_state.get(weight_state_key(key), 0)) for key in active_criteria()
        },
    }

def apply_ui_config(config: Dict):
    if not isinstance(config, dict):
        return

    st.session_state.scheduler_type = config.get("scheduler_type", st.session_state.scheduler_type)
    st.session_state.allocator_type = config.get("allocator_type", st.session_state.allocator_type)
    st.session_state.num_staff = int(config.get("num_staff", st.session_state.num_staff))
    st.session_state.quota_limit = int(config.get("quota_limit", st.session_state.quota_limit))

    enable_absence = config.get("enable_absence")
    if enable_absence is None:
        enable_absence = int(config.get("num_absent_staff", 0)) > 0
    st.session_state.enable_absence = bool(enable_absence)

    st.session_state.total_requests = int(config.get("total_requests", st.session_state.total_requests))
    st.session_state.peak_mode = bool(config.get("peak_mode", st.session_state.peak_mode))
    st.session_state.urgency = bool(config.get("urgency", st.session_state.urgency))
    st.session_state.imbalance_factor = int(config.get("imbalance_factor", st.session_state.imbalance_factor))

    max_absent = max(0, st.session_state.num_staff - 1)
    if st.session_state.enable_absence and max_absent > 0:
        st.session_state.num_absent_staff = min(
            max(1, int(config.get("num_absent_staff", st.session_state.num_absent_staff))),
            max_absent,
        )
    else:
        st.session_state.num_absent_staff = 0

    try:
        work_start = datetime.strptime(config.get("work_start", "08:00"), "%H:%M").time()
        work_end = datetime.strptime(config.get("work_end", "17:00"), "%H:%M").time()
        st.session_state.work_start_time = work_start
        st.session_state.work_end_time = work_end
    except Exception:
        pass

    st.session_state.seed_mode = config.get("seed_mode", st.session_state.seed_mode)
    st.session_state.manual_seed = int(config.get("manual_seed", st.session_state.manual_seed))

    raw = config.get("weights_raw", {})
    for key in CRITERIA_KEYS:
        state_key = weight_state_key(key)
        st.session_state[state_key] = int(raw.get(key, st.session_state.get(state_key, 50)))
    # If incoming config included urgency, apply it too
    if "urgency" in raw:
        st.session_state[weight_state_key("urgency")] = int(raw.get("urgency", st.session_state.get(weight_state_key("urgency"), 50)))

# ============================================================================
# PRESET MANAGEMENT
# ============================================================================

def load_presets() -> Dict[str, Dict]:
    if not os.path.exists(PRESET_FILE):
        return {}
    try:
        with open(PRESET_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_presets(presets: Dict[str, Dict]):
    with open(PRESET_FILE, "w", encoding="utf-8") as handle:
        json.dump(presets, handle, indent=2)
