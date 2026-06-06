import pandas as pd
import json
from datetime import datetime


def build_export_csv(engine):
    return pd.DataFrame([
        {
            "request_id": r.request_id,
            "college": r.college,
            "document_type": r.document_type,
            "requester_status": getattr(r, "requester_type", "-"),
            "completeness_of_requirements": round(float(getattr(r, "completeness_of_requirements", 0.0)), 4),
            "payment_status": getattr(r, "payment_status", "-"),
            "submission_time": r.submission_time.isoformat(),
            "assignment_time": r.assignment_time.isoformat() if r.assignment_time else None,
            "completion_time": r.completion_time.isoformat() if r.completion_time else None,
            "queue_wait_hours": round(r.get_waiting_time_minutes() / 60.0, 4),
            "turnaround_days": round(r.get_turnaround_time_minutes() / 1440.0, 4),
            "assigned_staff": r.assigned_staff,
        }
        for r in engine.completed
    ])


def build_config_json(results, st_state):
    return {
        "generated_at": datetime.now().isoformat(),
        "seed_used": results.get("seed_used"),
        "scheduler_type": results.get("scheduler_type"),
        "allocator_type": results.get("allocator_type"),
        "mode": "custom_sliders",
        "work_hours": results.get("work_hours"),
        "priority_weights": results.get("priority_weights"),
        "run_config": st_state.last_run_config.get("run_config", {}),
        "ui_config": st_state.last_run_config.get("ui_config", {}),
    }