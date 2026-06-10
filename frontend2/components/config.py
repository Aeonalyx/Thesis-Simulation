from backend1.scheduler_engine1 import PRIORITY_WEIGHTS
import os
from typing import Any

# ============================================================================
# CONFIG AND CONSTANTS
# ============================================================================

CHART_COLORWAY = ["#a855f7", "#7c3aed", "#22d3ee", "#c084fc", "#38bdf8", "#f472b6"]
PRESET_FILE = os.path.join(os.path.dirname(__file__), "presets.json")

CRITERIA_KEYS = list(PRIORITY_WEIGHTS.keys())
CRITERIA_LABELS = {
    "completeness_of_requirements": "Completeness of requirements",
    "submission_time": "Submission time",
    "document_type": "Document type",
    "requester_status": "Requester status",
    "college_affiliation": "College affiliation",
    "payment_status": "Payment status",
    "urgency": "Urgency",
}


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

SCHEDULER_OPTIONS = ["FCFS", "WEIGHTED"]
SCHEDULER_LABELS = {
    "FCFS": "FCFS (default)",
    "WEIGHTED": "Weighted (priority-based)",
}
ALLOCATOR_OPTIONS = ["college_based", "workload_based", "pooled", "quota_free"]
ALLOCATOR_LABELS = {
    "college_based": "College Based",
    "workload_based": "Workload Based",
    "pooled": "Pooled",
    "quota_free": "Quota Free",
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_criterion_label(key: str) -> str:
    return CRITERIA_LABELS.get(key, key.replace("_", " ").title())


def weight_state_key(key: str) -> str:
    return f"w_{key}"


def humanize_option_label(value: str) -> str:
    if not isinstance(value, str):
        return str(value)
    if value in SCHEDULER_LABELS:
        return SCHEDULER_LABELS[value]
    if value in ALLOCATOR_LABELS:
        return ALLOCATOR_LABELS[value]
    if value == "Variant":
        return "Variant"
    return value.replace("_", " ").title()


def humanize_event_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    return text.replace("_", " ").title()


def format_variant_label(scheduler: str, allocator: str) -> str:
    scheduler_label = SCHEDULER_LABELS.get(str(scheduler), str(scheduler))
    allocator_label = ALLOCATOR_LABELS.get(
        str(allocator), str(allocator).replace("_", " ").title()
    )
    return f"{scheduler_label} | {allocator_label}"