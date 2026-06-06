
import streamlit as st 
import json
import os
from typing import Dict, List
from config import DEFAULT_STATE, PRESET_FILE, CRITERIA_KEYS, PRIORITY_WEIGHTS
import datetime
from frontend2.componentss import weight_state_key
from backend1.scheduler_engine1 import SimulationEngine
from core.simulation_context import SimulationContext


def initialize_state():
    if "sim_context" not in st.session_state:
        st.session_state.sim_context = SimulationContext()

    if "playback_frame" not in st.session_state:
        st.session_state.playback_frame = 0

    if "comparison_df" not in st.session_state:
        st.session_state.comparison_df = None

    if "playback_playing" not in st.session_state:
        st.session_state.playback_playing = False

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


def collect_ui_config() -> Dict:
    return {
        "scheduler_type": st.session_state.scheduler_type,
        "allocator_type": st.session_state.allocator_type,
        "num_staff": int(st.session_state.num_staff),
        "quota_limit": int(st.session_state.quota_limit),
        "enable_absence": bool(st.session_state.enable_absence),
        "total_requests": int(st.session_state.total_requests),
        "urgency_base": int(st.session_state.urgency_base),
        "imbalance_factor": int(st.session_state.imbalance_factor),
        "num_absent_staff": int(st.session_state.num_absent_staff),
        "work_start": st.session_state.work_start_time.strftime("%H:%M"),
        "work_end": st.session_state.work_end_time.strftime("%H:%M"),
        "seed_mode": st.session_state.seed_mode,
        "manual_seed": int(st.session_state.manual_seed),
        "weights_raw": {
            key: int(st.session_state[weight_state_key(key)]) for key in CRITERIA_KEYS
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
    st.session_state.urgency_base = int(config.get("urgency_base", st.session_state.urgency_base))
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
        st.session_state[state_key] = int(raw.get(key, st.session_state[state_key]))


def normalized_weights_from_ui() -> Dict[str, float]:
    raw = {key: float(st.session_state[weight_state_key(key)]) for key in CRITERIA_KEYS}
    total = sum(raw.values())
    if total <= 0:
        return PRIORITY_WEIGHTS.copy()
    return {key: value / total for key, value in raw.items()}

def clear_run_state():
    ctx = st.session_state.sim_context
    ctx.engine = None
    ctx.results = None
    ctx.last_run_config = None
    st.session_state.playback_frame = 0
    st.session_state.playback_frame_ui = 0
    st.session_state.playback_playing = False

def on_playback_slider_change():
    """Sync slider position to internal request-step state and pause autoplay."""
    st.session_state.playback_playing = False
    st.session_state.playback_frame = int(st.session_state.playback_frame_ui)

def build_engine_and_run_config() -> Dict:
    weights = normalized_weights_from_ui()
    manual_seed = int(st.session_state.manual_seed) if st.session_state.seed_mode == "Manual" else None

    engine_kwargs = {
        "scheduler_type": st.session_state.scheduler_type,
        "allocator_type": st.session_state.allocator_type,
        "staff_config": {
            "num_staff": int(st.session_state.num_staff),
            "quota_limit": int(st.session_state.quota_limit),
        },
        "priority_weights": weights,
        "random_seed": manual_seed,
        "work_start": st.session_state.work_start_time.strftime("%H:%M"),
        "work_end": st.session_state.work_end_time.strftime("%H:%M"),
    }

    run_config = {
        "scenario": "custom",
        "total_requests": int(st.session_state.total_requests),
        "urgency_base": int(st.session_state.urgency_base),
        "imbalance_factor": int(st.session_state.imbalance_factor),
        "num_absent_staff": int(st.session_state.num_absent_staff) if st.session_state.enable_absence else 0,
    }

    export_bundle = {
        "engine_kwargs": engine_kwargs,
        "run_config": run_config,
        "ui_config": collect_ui_config(),
    }
    return export_bundle

# TEMP: will move to API layer later
def run_simulation_now():
    payload = build_engine_and_run_config()
    engine = SimulationEngine(**payload["engine_kwargs"])
    results = engine.run(custom_config=payload["run_config"])

    ctx = st.session_state.sim_context

    if not ctx.results or not ctx.engine:
        st.info("Run simulation first.")
        st.stop()

    results = ctx.results
    engine = ctx.engine
    st.session_state.last_run_config = payload
    st.session_state.playback_frame = 0
    st.session_state.playback_frame_ui = 0
    st.session_state.playback_playing = False


