"""
models.py
Defines DocumentRequest and StaffMember data models.
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from .config import (
    REQUESTER_PRIORITY,
    REQUESTER_PRIORITY_MAX,
    PRIORITY_SCORE_HALF_LIFE,
    DOCUMENT_COMPLEXITY,
    COLLEGE_PRIORITY,
    COMPLETENESS_LEVELS,
    _soft_cap,
    _duration_to_schedule,
)

@dataclass
class DocumentRequest:
    request_id: str
    college: str
    document_type: str
    urgency: int
    requester_type: str
    submission_time: datetime
    completeness_of_requirements: float = 1.0
    payment_status: str = "Paid"
    requirements_stage: str = "complete"
    requirements_partial_time: Optional[datetime] = None
    requirements_complete_time: Optional[datetime] = None
    payment_time: Optional[datetime] = None
    ready_time: Optional[datetime] = None

    priority_score: float = 0.0
    assignment_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    assigned_staff: Optional[str] = None
    is_custom: bool = False

    def calculate_priority(
        self,
        current_time: datetime,
        weights: Dict[str, float],
        workday_minutes: int,
        urgency: bool = False,
    ) -> float:
        """Compute weighted priority score for this request at current_time."""
        self.update_status(current_time)
        completeness_norm = max(0.0, min(float(self.completeness_of_requirements), 1.0))

        requester_raw = REQUESTER_PRIORITY.get(self.requester_type, 3)
        requester_norm = requester_raw / max(float(REQUESTER_PRIORITY_MAX), 1.0)

        waiting_minutes = max(
            0.0,
            (current_time - self.submission_time).total_seconds() / 60.0,
        )
        submission_norm = _soft_cap(waiting_minutes, max(float(workday_minutes * 2), 1.0))

        base_duration, _ = _duration_to_schedule(
            DOCUMENT_COMPLEXITY.get(self.document_type, 1)
        )
        complexity_days = max(base_duration.total_seconds() / 86400.0, 1e-6)
        doc_norm = 1.0 / (1.0 + complexity_days)

        college_norm = float(COLLEGE_PRIORITY.get(self.college, 0.5))

        payment_norm = 0.0
        if isinstance(self.payment_status, str):
            status_text = self.payment_status.strip().lower()
            if status_text in {"paid", "settled", "complete", "cleared", "yes", "y", "true", "1"}:
                payment_norm = 1.0
        else:
            payment_norm = 1.0 if bool(self.payment_status) else 0.0

        urgency_norm = float(self.urgency) / 10.0 if urgency else 0.0

        scores = {
            "completeness_of_requirements": completeness_norm,
            "submission_time": submission_norm,
            "document_type": doc_norm,
            "requester_status": requester_norm,
            "college_affiliation": college_norm,
            "payment_status": payment_norm,
            "urgency": urgency_norm
        }

        total_score = 0.0
        for key, weight in weights.items():
            if key == "urgency" and not urgency:
                continue
            total_score += float(weight) * scores.get(key, 0.0)

        self.priority_score = _soft_cap(total_score, PRIORITY_SCORE_HALF_LIFE)
        return self.priority_score

    def _requirements_stage_at(self, current_time: datetime) -> str:
        if self.requirements_partial_time and current_time < self.requirements_partial_time:
            return "incomplete"
        if self.requirements_complete_time and current_time < self.requirements_complete_time:
            return "partial"
        return "complete"

    def _payment_status_at(self, current_time: datetime) -> str:
        if self.payment_time is None:
            return self.payment_status
        return "Paid" if current_time >= self.payment_time else "Unpaid"

    def update_status(self, current_time: datetime):
        stage = self._requirements_stage_at(current_time)
        self.requirements_stage = stage
        self.completeness_of_requirements = float(COMPLETENESS_LEVELS.get(stage, 1.0))
        self.payment_status = self._payment_status_at(current_time)

    def get_waiting_time_minutes(self) -> Optional[float]:
        if self.assignment_time is None:
            return None
        return (self.assignment_time - self.submission_time).total_seconds() / 60.0

    def get_turnaround_time_minutes(self) -> float:
        if self.completion_time is None:
            return 0.0
        return (self.completion_time - self.submission_time).total_seconds() / 60.0

    def to_dict(self) -> Dict:
        return {
            "request_id": self.request_id,
            "college": self.college,
            "document_type": self.document_type,
            "urgency": self.urgency,
            "requester_type": self.requester_type,
            "completeness_of_requirements": round(float(self.completeness_of_requirements), 4),
            "requirements_stage": self.requirements_stage,
            "payment_status": self.payment_status,
            "requirements_partial_time": self.requirements_partial_time.isoformat()
            if self.requirements_partial_time
            else None,
            "requirements_complete_time": self.requirements_complete_time.isoformat()
            if self.requirements_complete_time
            else None,
            "payment_time": self.payment_time.isoformat() if self.payment_time else None,
            "ready_time": self.ready_time.isoformat() if self.ready_time else None,
            "submission_time": self.submission_time.isoformat(),
            "priority_score": round(self.priority_score, 4),
            "assignment_time": self.assignment_time.isoformat() if self.assignment_time else None,
            "completion_time": self.completion_time.isoformat() if self.completion_time else None,
            "assigned_staff": self.assigned_staff,
            "is_custom": self.is_custom,
        }


@dataclass
class StaffMember:
    staff_id: str
    name: str
    college_affiliation: str
    quota_limit: int = 20

    is_available: bool = True
    total_assigned: int = 0
    next_available_time: Optional[datetime] = None
    daily_assigned: Dict[str, int] = field(default_factory=dict)

    def reset_for_run(self, day_start: datetime):
        self.total_assigned = 0
        self.next_available_time = day_start
        self.daily_assigned = {}

    def assignments_on_day(self, day: date) -> int:
        return self.daily_assigned.get(day.isoformat(), 0)

    def increment_day_quota(self, day: date):
        key = day.isoformat()
        self.daily_assigned[key] = self.daily_assigned.get(key, 0) + 1
