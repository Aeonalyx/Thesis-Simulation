import streamlit as st

from state import on_playback_slider_change
from config import SPEED_OPTIONS
from frontend2.componentss import build_staff_college_map
from backend1.scheduler_engine1 import (DOCUMENT_COMPLEXITY)
from services.comparison_service import run_comparison
from services.export_service import build_export_csv, build_config_json

from components.comparison_ui import (
    render_comparison_controls,
    render_comparison_table,
    render_export_csv,
    render_export_json,
)
from frontend2.componentss import (
    playback_state,
    routing_events,
    parse_event_time
)
from services.playback_service import (
    build_request_lookup,
    build_staff_snapshot,
    build_waiting_rows,
    build_pending_queue,
    build_capacity_view,
    is_weighted_scheduler
)

from components.playback_ui import (
    render_capacity_chart, 
    render_current_decision, 
    render_playback_controls, 
    render_playback_metrics, 
    render_queue_tables, 
    render_staff_lists,
    handle_playback_autorun,
)

from services.request_inspection_service import (
    filter_requests,
    sort_requests,
    build_request_table,
)

from components.request_inspection_ui import (
    render_filters,
    render_request_table,
    render_selected_request,
)


#    st.plotly_chart(fig_timeline, use_container_width=True)

def show_results():

    if not st.session_state.simulation_results or not st.session_state.simulation_engine:
        st.info("Run simulation first.")
        st.stop()

    results = st.session_state.simulation_results
    engine = st.session_state.simulation_engine
    staff_college_map = build_staff_college_map(engine.staff_pool)

    st.header("Playback")

    event_log = results.get("event_log", [])
    decisions = routing_events(event_log)

    if not decisions:
        st.warning("No request-routing decisions available for playback.")
        return

    max_step = len(decisions) - 1

    # =========================
    # Playback Controls (UI only)
    # =========================
    render_playback_controls(max_step, SPEED_OPTIONS, on_playback_slider_change)

    # =========================
    # Frame state
    # =========================
    frame_data = playback_state(decisions, st.session_state.playback_frame)
    current_event = frame_data["current_event"]

    request_lookup = build_request_lookup(results)

    # =========================
    # Backend-style computed data (MOVED OUT)
    # =========================
    staff_rows, staff_meta = build_staff_snapshot(
        engine=engine,
        frame_data=frame_data,
        request_lookup=request_lookup
    )

    waiting_rows = build_waiting_rows(
        frame_data=frame_data,
        request_lookup=request_lookup,
        is_weighted_scheduler=is_weighted_scheduler(results)
    )

    if not current_event:
        return

    current_time = parse_event_time(current_event["time"])

    pending_queue_rows = build_pending_queue(
        request_lookup=request_lookup,
        frame_data=frame_data,
        current_time=current_time,
        is_weighted_scheduler=is_weighted_scheduler(results)
    )

    quota_enforced = results.get("allocator_type") != "quota_free"

    capacity_rows, assigned_maps = build_capacity_view(
        engine=engine,
        staff_rows=staff_rows,
        current_time=current_time,
        quota_enforced=quota_enforced,
        staff_college_map=staff_college_map
    )

    # =========================
    # UI RENDERING ONLY
    # =========================
    render_playback_metrics(
        current_time=current_time,
        frame_data=frame_data,
        pending_queue_rows=pending_queue_rows,
        max_step=max_step
    )

    render_current_decision(current_event, staff_college_map)

    render_capacity_chart(capacity_rows, quota_enforced)

    render_staff_lists(
        engine=engine,
        staff_rows=staff_rows,
        staff_meta=staff_meta,
        assigned_maps=assigned_maps,
        quota_enforced=quota_enforced,
        staff_college_map=staff_college_map
    )

    render_queue_tables(pending_queue_rows, waiting_rows)

    # =========================
    # autoplay loop (unchanged logic, but isolated)
    # =========================
    handle_playback_autorun(max_step, SPEED_OPTIONS)




def show_request_inspection(results, engine, is_weighted_scheduler, COLLEGES, DOCUMENT_COMPLEXITY,
                            format_staff_label, staff_college_map, format_compact_datetime):

    st.header("Request Inspection")

    completed_requests = engine.completed

    if not completed_requests:
        st.info("No completed requests to inspect.")
        return

    sort_options = [
        "Assigned Day",
        "Submission Time",
        "Queue Wait Desc",
        "Queue Wait Asc",
        "Turnaround Desc",
    ]

    if is_weighted_scheduler:
        sort_options = ["Priority Desc", "Priority Asc"] + sort_options

    filter_college, filter_doc, sort_by = render_filters(
        COLLEGES,
        list(DOCUMENT_COMPLEXITY.keys()),
        sort_options
    )

    filtered = filter_requests(completed_requests, filter_college, filter_doc)
    filtered = sort_requests(filtered, sort_by, is_weighted_scheduler)

    df = build_request_table(filtered, engine, format_staff_label, staff_college_map)

    render_request_table(df)

    selected_idx = st.number_input("Select Row", 0, max(0, len(filtered) - 1), 0)

    selected_req = filtered[int(selected_idx)]

    req_obj = render_selected_request(
        {
            "request_id": selected_req.request_id,
            "college": selected_req.college,
            "document_type": selected_req.document_type,
            "completeness": float(getattr(selected_req, "completeness_of_requirements", 0.0)),
            "requester_type": getattr(selected_req, "requester_type", "-"),
            "payment_status": getattr(selected_req, "payment_status", "-"),
            "priority_score": float(getattr(selected_req, "priority_score", 0.0)),
            "assigned_staff": selected_req.assigned_staff,
            "submission_time": selected_req.submission_time,
            "assignment_time": selected_req.assignment_time,
            "completion_time": selected_req.completion_time,
        },
        format_compact_datetime,
        format_staff_label,
        staff_college_map
    )

def show_comparison(results, engine, st_state, SCHEDULER_OPTIONS, ALLOCATOR_OPTIONS,
                    normalized_weights_from_ui):

    st.header("Comparison Tools")

    schedulers, allocators, run = render_comparison_controls(
        SCHEDULER_OPTIONS,
        ALLOCATOR_OPTIONS
    )

    if run:
        if not schedulers or not allocators:
            st.warning("Select at least one scheduler and allocator.")
        else:
            df = run_comparison(
                schedulers=schedulers,
                allocators=allocators,
                seed=int(results.get("seed_used", st_state.manual_seed)),
                staff_config={
                    "num_staff": int(st_state.num_staff),
                    "quota_limit": int(st_state.quota_limit),
                },
                priority_weights_fn=normalized_weights_from_ui,
                custom_config={
                    "scenario": "custom",
                    "total_requests": int(st_state.total_requests),
                    "urgency_base": int(st_state.urgency_base),
                    "imbalance_factor": int(st_state.imbalance_factor),
                    "num_absent_staff": int(st_state.num_absent_staff),
                },
                st_state=st_state
            )

            st.session_state.comparison_df = df

    if st.session_state.get("comparison_df") is not None:
        render_comparison_table(st.session_state.comparison_df)

    # EXPORTS
    if engine.completed:
        csv_df = build_export_csv(engine)
        render_export_csv(
            csv_df,
            f"simulation_results_{st_state.manual_seed}.csv"
        )

    if st_state.last_run_config:
        json_data = build_config_json(results, st_state)
        render_export_json(
            json_data,
            f"simulation_config_{st_state.manual_seed}.json"
        )