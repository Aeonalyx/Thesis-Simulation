import os
from datetime import time

from backend1.scheduler_engine1 import (  # noqa: E402
    COLLEGES,
    DOCUMENT_COMPLEXITY,
    PRIORITY_WEIGHTS,
    COLLEGE_PRIORITY,
    COMPLETENESS_LEVELS,
    REQUESTER_PRIORITY,
    REQUESTER_PRIORITY_MAX,
    DocumentRequest,
    SimulationEngine,
    _duration_to_schedule,
)

from frontend2.componentss import weight_state_key


CRITERIA_KEYS = list(PRIORITY_WEIGHTS.keys())
CRITERIA_LABELS = {
    "completeness_of_requirements": "Completeness of requirements",
    "submission_time": "Submission time",
    "document_type": "Document type",
    "requester_status": "Requester status",
    "college_affiliation": "College affiliation",
    "payment_status": "Payment status",
}


PRESET_FILE = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    "presets.json",
)

SCHEDULER_OPTIONS = [
    "FCFS",
    "WEIGHTED",
]

ALLOCATOR_OPTIONS = [
    "college_based",
    "workload_based",
    "pooled",
    "quota_free",
]

SPEED_OPTIONS = {
    "0.25x": 1.20,
    "0.50x": 0.80,
    "1.00x": 0.45,
    "2.00x": 0.20,
    "4.00x": 0.08,
    "8.00x": 0.05,
    "16.00x": 0.03,
    "Smooth": 0.025,
}

WEIGHT_DEFAULT_STATE = {
    weight_state_key(key):
    int(PRIORITY_WEIGHTS.get(key, 0.0) * 100)
    for key in CRITERIA_KEYS
}

DEFAULT_STATE = {
    "scheduler_type": "FCFS",
    "allocator_type": "college_based",
    "num_staff": len(COLLEGES),
    "quota_limit": 20,
    "enable_absence": False,
    "total_requests": 200,
    "urgency_base": 5,
    "imbalance_factor": 0,
    "num_absent_staff": 0,
    "work_start_time": time(8, 0),
    "work_end_time": time(17, 0),
    "seed_mode": "Auto",
    "manual_seed": 12345,
    **WEIGHT_DEFAULT_STATE,
    "playback_frame": 0,
    "playback_frame_ui": 0,
    "playback_speed": "1.00x",
    "playback_playing": False,
}

CHART_COLORWAY = [
    "#a855f7",
    "#7c3aed",
    "#22d3ee",
    "#c084fc",
    "#38bdf8",
    "#f472b6",
]