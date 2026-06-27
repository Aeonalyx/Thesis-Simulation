"""
config.py
Configuration constants and core mathematical/scheduling helper utilities.
"""

from datetime import timedelta
import re
from typing import Dict, Tuple
from .roc_utils import PRIORITY_ROC_WEIGHTS

# Weight parameters
PRIORITY_WEIGHTS = PRIORITY_ROC_WEIGHTS

REQUESTER_PRIORITY = {
    "Graduating Student": 1,
    "Faculty": 1,
    "Alumni": 1,
    "Regular Student": 1,
}

REQUESTER_GENERATION_WEIGHTS = {
    "Regular Student": 0.65,
    "Graduating Student": 0.18,
    "Alumni": 0.10,
    "Faculty": 0.07,
}

REQUESTER_PRIORITY_MAX = max(REQUESTER_PRIORITY.values()) if REQUESTER_PRIORITY else 1

# Controls the final priority score soft-cap (lower raises scores faster).
PRIORITY_SCORE_HALF_LIFE = 0.15

# Durations can be workdays (number) or strings like "2 day" / "18 hour".
DOCUMENT_COMPLEXITY = {
    "Certification, Authentication and Verification (CAV)": "3 days",
    "Official Transcript of Records (TOR) and Transfer Credentials (TC)": "3 days",
    "Certification": "1 day",
    "Diploma": "4 hours",
    "Evaluation of Grades; Report of Grades (ROG); Certificate of Registration (COR)": "4 hours",
    "Permit to Cross-Enrol": "1 hour",
    "Authentication": "4 hours",
    "Academic Load Revision (ALRP)": "1 hour",
    "Grading Sheets": "1 day",
    "Shifter’s Form, Returnee’s Form or Leave of Absence": "1 day",
    "Completion Forms": "1 day",
    "Advance Credit": "1 day",
    "Registration of Old and Returnee Students": "1 hour",
}

DOCUMENT_REQUESTER_RESTRICTIONS = {
    "Certification, Authentication and Verification (CAV)": ["Graduating Student", "Alumni"],
    "Official Transcript of Records (TOR) and Transfer Credentials (TC)": ["Alumni"],
    "Certification": ["Alumni"],
    "Diploma": ["Alumni"],
    "Evaluation of Grades; Report of Grades (ROG); Certificate of Registration (COR)": [
        "Graduating Student",
        "Alumni",
        "Regular Student",
    ],
    "Permit to Cross-Enrol": ["Graduating Student", "Alumni", "Regular Student"],
    "Authentication": ["Graduating Student", "Alumni", "Regular Student"],
    "Academic Load Revision (ALRP)": ["Regular Student"],
    "Grading Sheets": ["Faculty"],
    "Shifter’s Form, Returnee’s Form or Leave of Absence": ["Regular Student"],
    "Completion Forms": ["Faculty"],
    "Registration of Old and Returnee Students": ["Regular Student"],
}

DOCUMENT_PAYMENT_REQUIRED = {
    "Grading Sheets": False,
}

COLLEGES = ["COE", "CED", "CASS", "CSM", "CEBA", "CCS", "CHS"]

COLLEGE_POPULATION = {
    "COE": 0.2454,
    "CED": 0.1921,
    "CASS": 0.1908,
    "CSM": 0.1553,
    "CEBA": 0.0983,
    "CCS": 0.0787,
    "CHS": 0.0394,
}

COMPLETENESS_LEVELS = {
    "incomplete": 0.3,
    "partial": 0.7,
    "complete": 1.0,
}

REQUIREMENTS_PARTIAL_DELAY_HOURS_RANGE = (0.0, 0.2) # up to 12 minutes for partial requirements
REQUIREMENTS_COMPLETE_EXTRA_DELAY_HOURS_RANGE = (0.0, 1.0) # up to 1 hour after partial for complete requirements
PAYMENT_DELAY_HOURS_RANGE = (0.0, 24.0) # up to 2 days for payment after submission (if required)


def _build_college_priority() -> Dict[str, float]:
    raw: Dict[str, float] = {}
    for college in COLLEGES:
        population = float(COLLEGE_POPULATION.get(college, 0.0))
        population = max(population, 0.01)
        raw[college] = 1.0 / population
    max_score = max(raw.values()) if raw else 1.0
    return {college: score / max_score for college, score in raw.items()}


COLLEGE_PRIORITY = _build_college_priority()

_DURATION_PATTERN = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(day|days|hour|hours)\s*$", re.IGNORECASE)


def _soft_cap(value: float, half_life: float) -> float:
    """Smoothly compress toward 1.0 as value grows; equals 0.5 at half_life."""
    safe_half_life = max(float(half_life), 1e-6)
    return float(value) / (float(value) + safe_half_life)


def _duration_to_schedule(value: object) -> Tuple[timedelta, bool]:
    """Return (duration, use_work_hours). Days use calendar time; hours use work hours."""
    if isinstance(value, (int, float)):
        return timedelta(days=float(value)), False
    if not isinstance(value, str):
        return timedelta(days=1.0), False
    match = _DURATION_PATTERN.match(value)
    if not match:
        return timedelta(days=1.0), False
    amount = float(match.group(1))
    unit = match.group(2).lower()
    if unit.startswith("day"):
        return timedelta(days=amount), False
    return timedelta(hours=amount), True
