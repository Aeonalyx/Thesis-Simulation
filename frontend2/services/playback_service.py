from typing import Dict, Any
import pandas as pd
from datetime import datetime

from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

def is_weighted_scheduler(results: dict) -> bool:
    return results.get("scheduler_type") == "WEIGHTED"

# ============================================================
# CORE PLAYBACK LOGIC
# ============================================================

def routing_events(event_log: List[Dict]) -> List[Dict]:
    """
    Extract only routing-related decisions from event log.
    Keeps playback deterministic.
    """
    return [
        e for e in event_log
        if e.get("event_type") in {"ASSIGN", "ROUTE", "ASSIGNMENT"}
    ]


def playback_state(decisions: List[Dict], frame: int) -> Dict:
    """
    Reconstruct system state at a given playback frame.
    Assumes decisions are ordered chronologically.
    """

    frame = max(0, min(frame, len(decisions) - 1))

    assignments = []
    waiting = []

    processed_count = 0
    assigned_count = 0
    current_event = None

    for i in range(frame + 1):
        event = decisions[i]
        current_event = event
        processed_count += 1

        if event.get("event_type") in {"ASSIGN", "ASSIGNMENT"}:
            assigned_count += 1
            assignments.append(event.get("data", {}))

        elif event.get("event_type") in {"WAIT", "QUEUE"}:
            waiting.append(event.get("data", {}))

    return {
        "current_event": current_event,
        "assignments": assignments,
        "waiting": waiting,
        "processed_count": processed_count,
        "assigned_count": assigned_count,
        "waiting_count": len(waiting),
    }


# ============================================================
# LOOKUPS
# ============================================================

def build_request_lookup(results: Dict) -> Dict[str, Dict]:
    """
    Maps request_id -> request metadata
    """
    lookup = {}

    for r in results.get("generated_requests", []):
        if isinstance(r, dict) and r.get("request_id"):
            lookup[r["request_id"]] = r

    return lookup


# ============================================================
# STAFF SNAPSHOT
# ============================================================

def build_staff_snapshot(
    engine,
    frame_data: Dict,
    request_lookup: Dict[str, Dict]
) -> Tuple[Dict[str, List[Dict]], Dict[str, Dict]]:
    """
    Builds:
    - staff_rows: assignment history per staff
    - staff_meta: staff metadata (college, quota)
    """

    staff_rows: Dict[str, List[Dict]] = {}
    staff_meta: Dict[str, Dict] = {}

    for staff in engine.staff_pool:
        staff_rows[staff.staff_id] = []
        staff_meta[staff.staff_id] = {
            "college": staff.college_affiliation,
            "quota": staff.quota_limit,
        }

    for assignment in frame_data.get("assignments", []):
        staff_id = assignment.get("Staff") or "UNASSIGNED"
        request_id = assignment.get("Request")

        meta = request_lookup.get(request_id, {})

        if staff_id not in staff_rows:
            staff_rows[staff_id] = []
            staff_meta[staff_id] = {"college": "-", "quota": None}

        staff_rows[staff_id].append({
            "Request": request_id,
            "College": meta.get("college", assignment.get("College")),
            "Document": meta.get("document_type", "-"),
            "Priority Score": float(meta.get("priority_score", assignment.get("Priority Score", 0.0)) or 0.0),
            "Queue Wait (h)": assignment.get("Queue Wait (h)"),
            "Assigned At": assignment.get("Time"),
        })

    return staff_rows, staff_meta


# ============================================================
# WAITING ROWS
# ============================================================

def build_waiting_rows(
    frame_data: Dict,
    request_lookup: Dict[str, Dict],
    is_weighted_scheduler: bool
) -> List[Dict]:

    waiting_rows = []

    assigned_ids = {
        a.get("Request")
        for a in frame_data.get("assignments", [])
        if a.get("Request")
    }

    for w in frame_data.get("waiting", []):
        request_id = w.get("Request")

        if request_id in assigned_ids:
            continue

        meta = request_lookup.get(request_id, {})

        waiting_rows.append({
            "Request": request_id,
            "College": meta.get("college", w.get("College")),
            "Document": meta.get("document_type", "-"),
            "Priority Score": float(meta.get("priority_score", w.get("Priority Score", 0.0)) or 0.0),
            "Submitted": meta.get("submission_time", "-"),
            "Reason": w.get("Reason", ""),
            "Event Time": w.get("Time"),
        })

    if is_weighted_scheduler:
        waiting_rows.sort(
            key=lambda r: (
                -float(r.get("Priority Score", 0.0)),
                r.get("Event Time") or ""
            )
        )

    return waiting_rows


# ============================================================
# PENDING QUEUE
# ============================================================

def build_pending_queue(
    request_lookup: Dict[str, Dict],
    frame_data: Dict,
    current_time: datetime,
    is_weighted_scheduler: bool
) -> List[Dict]:

    pending = []

    routed_ids = {
        a.get("Request")
        for a in frame_data.get("assignments", [])
        if a.get("Request")
    } | {
        w.get("Request")
        for w in frame_data.get("waiting", [])
        if w.get("Request")
    }

    for request_id, meta in request_lookup.items():
        submission_raw = meta.get("submission_time")
        if not submission_raw:
            continue

        try:
            submission_time = datetime.fromisoformat(submission_raw)
        except Exception:
            continue

        if submission_time <= current_time and request_id not in routed_ids:
            pending.append({
                "Request": request_id,
                "College": meta.get("college", "-"),
                "Document": meta.get("document_type", "-"),
                "Priority Score": float(meta.get("priority_score", 0.0) or 0.0),
                "Submitted": submission_raw,
                "Pending Wait (h)": round(
                    (current_time - submission_time).total_seconds() / 3600.0, 2
                ),
            })

    if is_weighted_scheduler:
        pending.sort(key=lambda r: (-r["Priority Score"], r["Submitted"]))
    else:
        pending.sort(key=lambda r: r["Submitted"])

    return pending


# ============================================================
# CAPACITY VIEW
# ============================================================

def build_capacity_view(
    engine,
    staff_rows: Dict[str, List[Dict]],
    current_time: datetime,
    quota_enforced: bool,
    staff_college_map: Dict[str, str] = None
):

    capacity_rows = []
    assigned_today_map = {}
    total_assigned_map = {}

    current_day = current_time.date()

    for staff in engine.staff_pool:

        rows = staff_rows.get(staff.staff_id, [])
        total_assigned = len(rows)

        assigned_today = 0
        for r in rows:
            assigned_at = r.get("Assigned At")
            if assigned_at:
                try:
                    dt = datetime.fromisoformat(str(assigned_at))
                    if dt.date() == current_day:
                        assigned_today += 1
                except Exception:
                    pass

        quota = staff.quota_limit if quota_enforced else None

        row = {
            "Staff ID": staff.staff_id,
            "Staff": staff.staff_id,
            "College": staff.college_affiliation,
            "Assigned Today": assigned_today,
            "Total Assigned": total_assigned,
        }

        if quota_enforced:
            row["Quota/Day"] = quota
            row["Today Fill %"] = round((assigned_today / max(quota, 1)) * 100, 1)

        capacity_rows.append(row)

        assigned_today_map[staff.staff_id] = assigned_today
        total_assigned_map[staff.staff_id] = total_assigned

    return capacity_rows, {
        "assigned_today": assigned_today_map,
        "total_assigned": total_assigned_map,
    }