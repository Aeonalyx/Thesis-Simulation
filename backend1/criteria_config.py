"""
Criteria catalog and scoring helpers.

Built-in criteria stay in code for the study model. Institution-added criteria
are saved as data so non-coders can extend the weighted scheduler.
"""

import json
import os
import re
from typing import Any, Dict, List

try:
    from backend1.roc_utils import priority_criteria_ranking
    from backend1.request_fields import (
        custom_request_field_labels,
        custom_request_field_options,
        score_custom_field_value,
        slugify_key as slugify_field_key,
    )
except ImportError:
    from roc_utils import priority_criteria_ranking
    from request_fields import (
        custom_request_field_labels,
        custom_request_field_options,
        score_custom_field_value,
        slugify_key as slugify_field_key,
    )


CUSTOM_CRITERIA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "custom_criteria.json")

BUILT_IN_LABELS = {
    "submission_time": "Submission time",
    "document_type": "Document type",
    "requester_status": "Requester status",
    "college_affiliation": "College affiliation",
}

BUILT_IN_CRITERIA = [
    {
        "key": key,
        "label": BUILT_IN_LABELS.get(key, key.replace("_", " ").title()),
        "source": "built_in",
        "scoring_type": "built_in",
    }
    for key in priority_criteria_ranking
] + [
    {
        "key": "urgency",
        "label": "Urgency",
        "source": "built_in",
        "scoring_type": "built_in",
        "optional": True,
    },
]

SOURCE_FIELD_LABELS = {
    "requester_type": "Requester type",
    "document_type": "Document type",
    "college": "College",
    "urgency": "Urgency",
}

SCORING_TYPE_LABELS = {
    "field_score": "Request field score",
}


def slugify_key(label: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "_", str(label or "").strip().lower())
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "custom_criterion"


def get_source_field_labels(include_built_ins: bool = True) -> Dict[str, str]:
    labels = dict(SOURCE_FIELD_LABELS) if include_built_ins else {}
    labels.update(custom_request_field_labels())
    return labels


def get_source_field_options(include_built_ins: bool = True) -> Dict[str, List[Any]]:
    options: Dict[str, List[Any]] = custom_request_field_options()
    if include_built_ins:
        options = {
            "requester_type": [],
            "document_type": [],
            "college": [],
            "urgency": list(range(1, 11)),
            **options,
        }
    return options


def load_custom_criteria() -> List[Dict[str, Any]]:
    if not os.path.exists(CUSTOM_CRITERIA_FILE):
        return []
    try:
        with open(CUSTOM_CRITERIA_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_custom_criteria(criteria: List[Dict[str, Any]]):
    with open(CUSTOM_CRITERIA_FILE, "w", encoding="utf-8") as handle:
        json.dump(criteria, handle, indent=2)


def get_criteria_catalog() -> List[Dict[str, Any]]:
    custom = load_custom_criteria()
    return BUILT_IN_CRITERIA + custom


def _request_field_value(request_obj: Any, field_name: str) -> Any:
    if field_name == "college":
        return getattr(request_obj, "college", None)
    if field_name == "document_type":
        return getattr(request_obj, "document_type", None)
    if field_name == "requester_type":
        return getattr(request_obj, "requester_type", None)
    if field_name == "urgency":
        return getattr(request_obj, "urgency", None)
    extra_fields = getattr(request_obj, "extra_fields", {}) or {}
    if isinstance(extra_fields, dict) and field_name in extra_fields:
        return extra_fields.get(field_name)
    if hasattr(request_obj, field_name):
        return getattr(request_obj, field_name)
    return None


def _clamp01(value: Any) -> float:
    try:
        return max(0.0, min(float(value), 1.0))
    except Exception:
        return 0.0


def _duration_to_days(value: Any, unit: str = "days") -> float:
    if value is None:
        raise ValueError("Missing duration")
    if isinstance(value, (int, float)):
        number = float(value)
        if unit == "hours":
            return number / 24.0
        if unit == "weeks":
            return number * 7.0
        return number

    text = str(value).strip().lower()
    match = re.match(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z]+)?\s*$", text)
    if not match:
        raise ValueError(f"Invalid duration: {value}")
    number = float(match.group(1))
    parsed_unit = match.group(2) or unit
    if parsed_unit.startswith("hour") or parsed_unit in {"hr", "hrs", "h"}:
        return number / 24.0
    if parsed_unit.startswith("week") or parsed_unit in {"wk", "wks", "w"}:
        return number * 7.0
    if parsed_unit.startswith("day") or parsed_unit in {"d"}:
        return number
    raise ValueError(f"Unsupported duration unit: {parsed_unit}")


def score_custom_criteria(request_obj: Any, criteria: List[Dict[str, Any]]) -> Dict[str, float]:
    scores: Dict[str, float] = {}
    for criterion in criteria or []:
        key = criterion.get("key")
        source_field = criterion.get("source_field")
        scoring_type = criterion.get("scoring_type") or "field_score"
        if not key or not source_field:
            continue

        field_value = _request_field_value(request_obj, source_field)
        score = float(criterion.get("default_score", 0.0) or 0.0)

        if scoring_type == "field_score":
            extra_fields = getattr(request_obj, "extra_fields", {}) or {}
            score_key = f"{source_field}_score"
            if isinstance(extra_fields, dict) and score_key in extra_fields:
                score = _clamp01(extra_fields.get(score_key))
            else:
                score = score_custom_field_value(str(source_field), field_value)

        elif scoring_type == "category_mapping":
            mapping = criterion.get("mapping") or {}
            score = _clamp01(mapping.get(str(field_value), criterion.get("default_score", 0.0)))

        elif scoring_type == "duration_mapping":
            mapping = criterion.get("mapping") or {}
            unit = criterion.get("duration_unit", "days")
            duration_values = {}
            for map_key, raw_duration in mapping.items():
                try:
                    duration_values[str(map_key)] = _duration_to_days(raw_duration, unit)
                except Exception:
                    continue
            if str(field_value) in duration_values and duration_values:
                current = duration_values[str(field_value)]
                min_days = min(duration_values.values())
                max_days = max(duration_values.values())
                if max_days == min_days:
                    score = 1.0
                elif criterion.get("direction", "shorter_is_higher") == "longer_is_higher":
                    score = (current - min_days) / (max_days - min_days)
                else:
                    score = (max_days - current) / (max_days - min_days)
                score = _clamp01(score)

        elif scoring_type == "numeric_scale":
            try:
                numeric_value = float(field_value)
                min_value = float(criterion.get("min_value", 0.0))
                max_value = float(criterion.get("max_value", 1.0))
                if max_value != min_value:
                    score = (numeric_value - min_value) / (max_value - min_value)
                    if criterion.get("direction", "higher_is_higher") == "lower_is_higher":
                        score = 1.0 - score
                    score = _clamp01(score)
            except Exception:
                score = _clamp01(criterion.get("default_score", 0.0))

        scores[str(key)] = _clamp01(score)
    return scores
