import pandas as pd

def filter_requests(completed_requests, filter_college, filter_doc):
    filtered = completed_requests

    if filter_college != "All":
        filtered = [r for r in filtered if r.college == filter_college]

    if filter_doc != "All":
        filtered = [r for r in filtered if r.document_type == filter_doc]

    return filtered


def sort_requests(filtered, sort_by, is_weighted_scheduler):
    if sort_by == "Priority Desc":
        return sorted(filtered, key=lambda r: (-float(getattr(r, "priority_score", 0.0)), r.submission_time))

    if sort_by == "Priority Asc":
        return sorted(filtered, key=lambda r: (float(getattr(r, "priority_score", 0.0)), r.submission_time))

    if sort_by == "Assigned Day":
        return sorted(filtered, key=lambda r: (r.assignment_time.date(), r.submission_time))

    if sort_by == "Submission Time":
        return sorted(filtered, key=lambda r: r.submission_time)

    if sort_by == "Queue Wait Desc":
        return sorted(filtered, key=lambda r: r.get_waiting_time_minutes(), reverse=True)

    if sort_by == "Queue Wait Asc":
        return sorted(filtered, key=lambda r: r.get_waiting_time_minutes())

    return sorted(filtered, key=lambda r: r.get_turnaround_time_minutes(), reverse=True)


def build_request_table(filtered, engine, format_staff_label, staff_college_map):
    rows = []

    for idx, req in enumerate(filtered):
        assigned_day = (req.assignment_time.date() - engine.start_time.date()).days + 1

        rows.append({
            "Row": idx,
            "Request": req.request_id,
            "College": req.college,
            "Document": req.document_type,
            "Completeness": round(float(getattr(req, "completeness_of_requirements", 0.0)), 2),
            "Requester Status": getattr(req, "requester_type", "-"),
            "Payment Status": getattr(req, "payment_status", "-"),
            "Priority Score": round(float(getattr(req, "priority_score", 0.0)), 4),
            "Queue Wait (h)": round(req.get_waiting_time_minutes() / 60.0, 2),
            "Turnaround (d)": round(req.get_turnaround_time_minutes() / 1440.0, 2),
            "Assigned Day": assigned_day,
            "Staff": format_staff_label(req.assigned_staff, staff_college_map),
        })

    return pd.DataFrame(rows)


def build_selected_request_details(req):
    return {
        "request_id": req.request_id,
        "college": req.college,
        "document_type": req.document_type,
        "completeness": float(getattr(req, "completeness_of_requirements", 0.0)),
        "requester_type": getattr(req, "requester_type", "-"),
        "payment_status": getattr(req, "payment_status", "-"),
        "priority_score": float(getattr(req, "priority_score", 0.0)),
        "assigned_staff": req.assigned_staff,
        "submission_time": req.submission_time,
        "assignment_time": req.assignment_time,
        "completion_time": req.completion_time,
        "req": req,
    }