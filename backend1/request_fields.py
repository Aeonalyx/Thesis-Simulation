"""
Custom request-field configuration.

Institutions can define additional category fields used by generated requests.
Each category option carries its own normalized influence score from 0.0 to 1.0.
Request composition controls how often options are generated; criteria weighting
only decides whether that field participates in priority scoring.
"""

import json
import os
import re
from typing import Any, Dict, List, Optional


CUSTOM_REQUEST_FIELDS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "custom_request_fields.json",
)

RESERVED_FIELD_KEYS = {
    "request_id",
    "source",
    "college",
    "document_type",
    "requester_type",
    "requester_status",
    "urgency",
    "submission_time",
    "requirements_stage",
    "completeness_of_requirements",
    "requirements_partial_time",
    "requirements_complete_time",
    "payment_status",
    "payment_time",
    "ready_time",
    "assignment_time",
    "completion_time",
    "assigned_staff",
    "priority_score",
    "is_custom",
    "extra_fields",
}


def slugify_key(label: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "_", str(label or "").strip().lower())
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "custom_field"


def clamp01(value: Any) -> float:
    try:
        return max(0.0, min(float(value), 1.0))
    except Exception:
        return 0.0


def normalize_field(field: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not isinstance(field, dict):
        return None

    label = str(field.get("label") or "").strip()
    key = slugify_key(field.get("key") or label)
    if not label or not key or key in RESERVED_FIELD_KEYS:
        return None

    field_type = str(field.get("type") or "category").strip().lower()
    if field_type != "category":
        return None

    options: List[Dict[str, Any]] = []
    seen = set()
    for option in field.get("options") or []:
        if isinstance(option, dict):
            option_label = str(option.get("label") or "").strip()
            score = option.get("score", 0.0)
        else:
            option_label = str(option or "").strip()
            score = 0.0
        if not option_label or option_label in seen:
            continue
        seen.add(option_label)
        options.append({"label": option_label, "score": clamp01(score)})

    if not options:
        return None

    return {
        "key": key,
        "label": label,
        "type": "category",
        "options": options,
    }


def load_custom_request_fields() -> List[Dict[str, Any]]:
    if not os.path.exists(CUSTOM_REQUEST_FIELDS_FILE):
        return []
    try:
        with open(CUSTOM_REQUEST_FIELDS_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception:
        return []

    fields: List[Dict[str, Any]] = []
    seen = set()
    for raw in data if isinstance(data, list) else []:
        normalized = normalize_field(raw)
        if not normalized or normalized["key"] in seen:
            continue
        seen.add(normalized["key"])
        fields.append(normalized)
    return fields


def save_custom_request_fields(fields: List[Dict[str, Any]]):
    normalized_fields: List[Dict[str, Any]] = []
    seen = set()
    for raw in fields or []:
        normalized = normalize_field(raw)
        if not normalized or normalized["key"] in seen:
            continue
        seen.add(normalized["key"])
        normalized_fields.append(normalized)

    with open(CUSTOM_REQUEST_FIELDS_FILE, "w", encoding="utf-8") as handle:
        json.dump(normalized_fields, handle, indent=2)


def get_custom_request_field(field_key: str) -> Optional[Dict[str, Any]]:
    for field in load_custom_request_fields():
        if field.get("key") == field_key:
            return field
    return None


def custom_request_field_labels() -> Dict[str, str]:
    return {
        field["key"]: field["label"]
        for field in load_custom_request_fields()
    }


def custom_request_field_options() -> Dict[str, List[str]]:
    return {
        field["key"]: [option["label"] for option in field.get("options", [])]
        for field in load_custom_request_fields()
    }


def custom_request_field_scores() -> Dict[str, Dict[str, float]]:
    return {
        field["key"]: {
            str(option["label"]): clamp01(option.get("score", 0.0))
            for option in field.get("options", [])
        }
        for field in load_custom_request_fields()
    }


def score_custom_field_value(field_key: str, value: Any) -> float:
    scores = custom_request_field_scores().get(field_key, {})
    return clamp01(scores.get(str(value), 0.0))
