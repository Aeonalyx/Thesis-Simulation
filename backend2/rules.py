from datetime import timedelta
from typing import Dict, Tuple
import re

from backend2.config import COLLEGE_POPULATION, COLLEGES

_DURATION_PATTERN = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(day|days|hour|hours)\s*$", re.IGNORECASE)

def _build_college_priority() -> Dict[str, float]:
    raw: Dict[str, float] = {}
    for college in COLLEGES:
        population = float(COLLEGE_POPULATION.get(college, 0.0))
        population = max(population, 0.01)
        raw[college] = 1.0 / population
    max_score = max(raw.values()) if raw else 1.0
    return {college: score / max_score for college, score in raw.items()}

COLLEGE_PRIORITY = _build_college_priority()

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