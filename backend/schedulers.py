"""
schedulers.py
Defines FCFSScheduler and WeightedPriorityScheduler.
"""

from datetime import datetime
from typing import Dict, List
from .models import DocumentRequest

class FCFSScheduler:
    def __init__(self):
        self.queue: List[DocumentRequest] = []

    def add_request(self, request: DocumentRequest):
        self.queue.append(request)

    def get_all_sorted(self) -> List[DocumentRequest]:
        sorted_queue = sorted(self.queue, key=lambda r: (r.submission_time, r.request_id))
        self.queue.clear()
        return sorted_queue


class WeightedPriorityScheduler:
    def __init__(self):
        self.pending: List[DocumentRequest] = []

    def add_request(self, request: DocumentRequest):
        self.pending.append(request)

    def remove_request(self, request: DocumentRequest):
        self.pending.remove(request)

    def rank(
        self,
        current_time: datetime,
        weights: Dict[str, float],
        workday_minutes: int,
        urgency: bool = False,
    ) -> List[DocumentRequest]:
        for req in self.pending:
            req.calculate_priority(current_time, weights, workday_minutes, urgency)
        return sorted(self.pending, key=lambda r: (-r.priority_score, r.submission_time, r.request_id))
