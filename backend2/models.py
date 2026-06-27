from datetime import datetime, date
from dataclasses import dataclass, field
from typing import Dict, Optional
from backend2.config import COMPLETENESS_LEVELS

# ============================================================================
# DATA CLASSES
# ============================================================================

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

    def get_waiting_time_minutes(self) -> float:
        if self.assignment_time is None:
            return 0.0
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
            "requester_status": self.requester_type,
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