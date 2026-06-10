from frontend2.components.config import PRIORITY_WEIGHTS
from frontend2.components.state import active_criteria, weight_state_key, collect_ui_config
from typing import Dict, Optional, List
from backend2.engine import SimulationEngine
from datetime import datetime
from frontend2.components.config import humanize_event_text

import streamlit as st

# ============================================================================
# SIMULATION ENGINE
# ============================================================================

def normalized_weights_from_ui() -> Dict[str, float]:
    keys = active_criteria()
    raw = {key: float(st.session_state.get(weight_state_key(key), 0.0)) for key in keys}
    total = sum(raw.values())
    if total <= 0:
        return PRIORITY_WEIGHTS.copy()
    return {key: value / total for key, value in raw.items()}

def build_engine_and_run_config() -> Dict:
    weights = normalized_weights_from_ui()
    manual_seed = int(st.session_state.manual_seed) if st.session_state.seed_mode == "Manual" else None
    scenario = "peak_period" if st.session_state.peak_mode else "baseline"

    engine_kwargs = {
        "scheduler_type": st.session_state.scheduler_type,
        "allocator_type": st.session_state.allocator_type,
        "staff_config": {
            "num_staff": int(st.session_state.num_staff),
            "quota_limit": int(st.session_state.quota_limit),
        },
        "priority_weights": None if (st.session_state.urgency and sum(weights.get(k, 0.0) for k in weights if k != "urgency") <= 1e-9) else weights,
        "random_seed": manual_seed,
        "work_start": st.session_state.work_start_time.strftime("%H:%M"),
        "work_end": st.session_state.work_end_time.strftime("%H:%M"),
        "urgency": bool(st.session_state.urgency),
    }

    run_config = {
        "scenario": scenario,
        "total_requests": int(st.session_state.total_requests),
        "urgency": bool(st.session_state.urgency),
        "imbalance_factor": int(st.session_state.imbalance_factor),
        "num_absent_staff": int(st.session_state.num_absent_staff) if st.session_state.enable_absence else 0,
    }

    export_bundle = {
        "engine_kwargs": engine_kwargs,
        "run_config": run_config,
        "ui_config": collect_ui_config(),
    }
    return export_bundle


def run_simulation_now():
    payload = build_engine_and_run_config()

    engine = SimulationEngine(**payload["engine_kwargs"])
    results = engine.run(custom_config=payload["run_config"])

    # store engine + results
    st.session_state.simulation_engine = engine
    st.session_state.simulation_results = results

    # store exact config used
    st.session_state.last_run_config = payload["run_config"]

    # ✅ FREEZE SNAPSHOT (UI uses ONLY this)
    st.session_state.run_snapshot = {
        **payload["run_config"],

        # output metadata
        "seed_used": results.get("seed_used"),
        "scheduler_type": results.get("scheduler_type"),
        "allocator_type": results.get("allocator_type"),
        
        "peak_mode": st.session_state.get("peak_mode", False),
    }

    # reset playback
    st.session_state.playback_frame = 0
    st.session_state.playback_frame_ui = 1
    st.session_state.playback_playing = False
    st.session_state.comparison_df = None

def parse_event_time(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return datetime.now()
    
def build_staff_college_map(staff_pool) -> Dict[str, Dict[str, str]]:
    mapping: Dict[str, Dict[str, str]] = {}
    for staff in staff_pool:
        mapping[str(staff.staff_id)] = {
            "college": str(staff.college_affiliation),
            "name": str(getattr(staff, "name", "")),
        }
    return mapping

# ============================================================================
# FORMAT
# ============================================================================

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

# ============================================================================
# FIGURE
# ============================================================================

def run_variant_for_figure(scheduler_type: str, allocator_type: str) -> Optional[Dict]:
    last_run = st.session_state.get("last_run_config")
    if not last_run:
        return None

    engine_kwargs = dict(last_run.get("engine_kwargs", {}))
    engine_kwargs["scheduler_type"] = scheduler_type
    engine_kwargs["allocator_type"] = allocator_type
    engine_kwargs["random_seed"] = int(
        st.session_state.simulation_results.get("seed_used", st.session_state.manual_seed)
    )

    engine = SimulationEngine(**engine_kwargs)
    return engine.run(custom_config=last_run.get("run_config", {}))


# ============================================================================
# STATE
# ============================================================================

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
                    "Mode": humanize_event_text(item.get("details", "")),
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
                    "Reason": humanize_event_text(item.get("details", "")),
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