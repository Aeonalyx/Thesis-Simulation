import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time as tm

from typing import List, Dict
from datetime import datetime

from components.charts import (
apply_plot_theme, 
render_theme_table, 
staff_rows_with_day_separators, 
)

from components.config import SPEED_OPTIONS

from components.simulation import (
parse_event_time,
format_compact_datetime, 
format_staff_label,
playback_state,
routing_events,
)

from components.state import on_playback_slider_change
# ============================================================================
# PLAYBACK CONTROLS
# ============================================================================

def render_playback(ctx):
    st.header("Playback")

    engine = ctx.engine
    results = ctx.results
    session = ctx.session
    staff_college_map = ctx.staff_map
    is_weighted_scheduler = ctx.is_weighted

    event_log = results.get("event_log", [])
    decisions = routing_events(event_log)
    if not decisions:
        st.warning("No request-routing decisions available for playback.")
    else:
        max_step = len(decisions) - 1
        st.session_state.playback_frame = min(st.session_state.playback_frame, max_step)
        st.session_state.playback_frame_ui = min(max(st.session_state.playback_frame_ui, 1), max_step + 1)

        force_slider_sync = False

        controls_col1, controls_col2, controls_col3, controls_col4, controls_col5, controls_col6 = st.columns(6)

        if controls_col1.button("▶ Play", use_container_width=True):
            st.session_state.playback_playing = True
        if controls_col2.button("⏸ Pause", use_container_width=True):
            st.session_state.playback_playing = False
        if controls_col3.button("◀ Step", use_container_width=True):
            st.session_state.playback_playing = False
            st.session_state.playback_frame = max(0, st.session_state.playback_frame - 1)
            force_slider_sync = True
        if controls_col4.button("Step ▶", use_container_width=True):
            st.session_state.playback_playing = False
            st.session_state.playback_frame = min(max_step, st.session_state.playback_frame + 1)
            force_slider_sync = True
        if controls_col5.button("⏭ End", use_container_width=True):
            st.session_state.playback_playing = False
            st.session_state.playback_frame = max_step
            force_slider_sync = True

        controls_col6.selectbox("Speed", list(SPEED_OPTIONS.keys()), key="playback_speed")

        # Sync slider only after programmatic changes (buttons/autoplay), not on user drags.
        if force_slider_sync or (
            st.session_state.playback_playing
            and st.session_state.playback_frame_ui != st.session_state.playback_frame
        ):
            st.session_state.playback_frame_ui = st.session_state.playback_frame + 1

        st.slider(
            "Request Step",
            min_value=1,
            max_value=max_step + 1,
            key="playback_frame_ui",
            on_change=on_playback_slider_change,
        )

        frame_data = playback_state(decisions, st.session_state.playback_frame)
        current_event = frame_data["current_event"]

        request_lookup = {}
        for request_item in results.get("generated_requests", []):
            if isinstance(request_item, dict) and request_item.get("request_id"):
                request_lookup[request_item["request_id"]] = request_item

        staff_rows: Dict[str, List[Dict]] = {}
        staff_meta: Dict[str, Dict] = {}
        for staff in engine.staff_pool:
            staff_rows[staff.staff_id] = []
            staff_meta[staff.staff_id] = {
                "college": staff.college_affiliation,
                "quota": staff.quota_limit,
            }

        for assignment in frame_data["assignments"]:
            staff_id = assignment.get("Staff") or "UNASSIGNED"
            request_id = assignment.get("Request")
            request_meta = request_lookup.get(request_id, {})
            priority_score = request_meta.get("priority_score", assignment.get("Priority Score", 0.0))

            if staff_id not in staff_rows:
                staff_rows[staff_id] = []
                staff_meta[staff_id] = {"college": "-", "quota": None}

            staff_rows[staff_id].append(
                {
                    "Request": request_id,
                    "College": request_meta.get("college", assignment.get("College")),
                    "Document": request_meta.get("document_type", "-"),
                    "Priority Score": round(float(priority_score or 0.0), 4),
                    "Queue Wait (h)": assignment.get("Queue Wait (h)"),
                    "Assigned At": assignment.get("Time"),
                }
            )

        assigned_request_ids = {
            assignment.get("Request")
            for assignment in frame_data["assignments"]
            if assignment.get("Request")
        }

        waiting_rows = []
        for waiting_item in frame_data["waiting"]:
            request_id = waiting_item.get("Request")
            if request_id in assigned_request_ids:
                continue
            request_meta = request_lookup.get(request_id, {})
            event_time_raw = waiting_item.get("Time")
            waiting_rows.append(
                {
                    "Request": request_id,
                    "College": request_meta.get("college", waiting_item.get("College")),
                    "Document": request_meta.get("document_type", "-"),
                    "Priority Score": round(float(request_meta.get("priority_score", waiting_item.get("Priority Score", 0.0)) or 0.0), 4),
                    "Submitted": format_compact_datetime(request_meta.get("submission_time", "-")),
                    "Reason": waiting_item.get("Reason", ""),
                    "Event Time": format_compact_datetime(event_time_raw),
                    "_event_time": parse_event_time(str(event_time_raw)) if event_time_raw else datetime.min,
                }
            )

        if is_weighted_scheduler:
            waiting_rows.sort(
                key=lambda row: (
                    -float(row.get("Priority Score", 0.0)),
                    row.get("_event_time", datetime.min),
                )
            )

        if current_event:
            current_time = parse_event_time(current_event.get("time", ""))

            routed_request_ids = set()
            for assign_item in frame_data["assignments"]:
                if assign_item.get("Request"):
                    routed_request_ids.add(assign_item["Request"])
            for waiting_item in frame_data["waiting"]:
                if waiting_item.get("Request"):
                    routed_request_ids.add(waiting_item["Request"])

            pending_queue_rows = []
            for request_id, request_meta in request_lookup.items():
                submission_raw = request_meta.get("submission_time")
                if not submission_raw:
                    continue
                submission_time = parse_event_time(submission_raw)
                if submission_time <= current_time and request_id not in routed_request_ids:
                    pending_queue_rows.append(
                        {
                            "Request": request_id,
                            "College": request_meta.get("college", "-"),
                            "Document": request_meta.get("document_type", "-"),
                            "Priority Score": round(float(request_meta.get("priority_score", 0.0) or 0.0), 4),
                            "Submitted": format_compact_datetime(submission_raw),
                            "Pending Wait (h)": round((current_time - submission_time).total_seconds() / 3600.0, 2),
                            "_sort_submission": submission_time,
                        }
                    )

            if is_weighted_scheduler:
                pending_queue_rows.sort(
                    key=lambda row: (-float(row.get("Priority Score", 0.0)), row["_sort_submission"])
                )
            else:
                pending_queue_rows.sort(key=lambda row: row["_sort_submission"])
            for row in pending_queue_rows:
                row.pop("_sort_submission", None)

            card1, card2, card3, card4, card5 = st.columns([1.4, .7, .6, .5, .5])
            card1.metric("Simulation Clock", current_time.strftime("%Y-%m-%d %H:%M"))
            card2.metric("Current Request Step", f"{st.session_state.playback_frame + 1}/{max_step + 1}")
            card3.metric("Processed Decisions", frame_data["processed_count"])
            card4.metric("Assigned So Far", frame_data["assigned_count"])
            card5.metric("Queue Size Now", len(pending_queue_rows) + frame_data["waiting_count"])

            routing_event_label = str(current_event.get("event_type", "")).replace("_", " ").title()
            routing_detail_label = str(current_event.get("details", "")).replace("_", " ").title()

            st.markdown(
                "**Current Routing Decision:** "
                f"{routing_event_label} | "
                f"Request = {current_event.get('request_id')} | "
                f"Staff = {format_staff_label(current_event.get('staff_id'), staff_college_map)} | "
                f"Details = {routing_detail_label}"
            )

            st.subheader("Staff Capacity View")
            quota_enforced = results.get("allocator_type") != "quota_free"
            current_day = current_time.date()
            capacity_rows = []
            for staff in engine.staff_pool:
                rows_for_staff = staff_rows.get(staff.staff_id, [])
                total_assigned = len(rows_for_staff)
                assigned_today = 0
                for row in rows_for_staff:
                    assigned_at = row.get("Assigned At")
                    if assigned_at and parse_event_time(str(assigned_at)).date() == current_day:
                        assigned_today += 1

                quota_value = staff.quota_limit if quota_enforced else None
                row = {
                    "Staff ID": staff.staff_id,
                    "Staff": format_staff_label(staff.staff_id, staff_college_map),
                    "College": staff.college_affiliation,
                    "Assigned Today": assigned_today,
                    "Total Assigned": total_assigned,
                }
                if quota_enforced:
                    row["Quota/Day"] = quota_value
                    row["Today Fill %"] = round((assigned_today / max(quota_value, 1)) * 100.0, 1)
                capacity_rows.append(row)

            capacity_df = pd.DataFrame(capacity_rows)
            assigned_today_map = {
                row["Staff ID"]: row["Assigned Today"] for row in capacity_rows
            }
            total_assigned_map = {
                row["Staff ID"]: row["Total Assigned"] for row in capacity_rows
            }

            fig_capacity = go.Figure()
            fig_capacity.add_trace(
                go.Bar(
                    name="Assigned Today",
                    x=capacity_df["Staff"],
                    y=capacity_df["Assigned Today"],
                    marker_color="#a855f7",
                )
            )
            if quota_enforced:
                fig_capacity.add_trace(
                    go.Bar(
                        name="Quota per Day",
                        x=capacity_df["Staff"],
                        y=capacity_df["Quota/Day"],
                        marker_color="#22d3ee",
                        opacity=0.55,
                    )
                )

            fig_capacity.update_layout(
                title="Daily Staff Capacity at Current Request Step",
                xaxis_title="Staff",
                yaxis_title="Requests",
                barmode="group",
                height=360,
            )
            apply_plot_theme(fig_capacity)
            st.plotly_chart(fig_capacity, use_container_width=True)

            st.subheader("Live Staff Request Lists")
            ordered_staff_ids = [staff.staff_id for staff in engine.staff_pool]
            for idx in range(0, len(ordered_staff_ids), 3):
                row_ids = ordered_staff_ids[idx: idx + 3]
                row_cols = st.columns(3)
                for col, staff_id in zip(row_cols, row_ids):
                    with col:
                        meta = staff_meta.get(staff_id, {"college": "-", "quota": None})
                        assigned_today = assigned_today_map.get(staff_id, 0)
                        total_assigned = total_assigned_map.get(staff_id, 0)
                        if quota_enforced and meta.get("quota") is not None:
                            quota_value = int(meta["quota"])
                            st.metric(
                                f"{staff_id} ({meta['college']})",
                                f"{assigned_today}/{quota_value}",
                                delta=f"Total {total_assigned}",
                            )
                            if assigned_today >= quota_value:
                                st.warning("Quota full at this step")
                        else:
                            st.metric(
                                f"{staff_id} ({meta['college']})",
                                f"{total_assigned} assigned",
                            )

                        rows = staff_rows.get(staff_id, [])
                        if rows:
                            display_rows = staff_rows_with_day_separators(rows)
                            render_theme_table(pd.DataFrame(display_rows), height_px=340)
                        else:
                            st.caption("No requests routed here yet.")

            st.subheader("Queue and Waiting Lists")
            wait_col1, wait_col2 = st.columns(2)

            with wait_col1:
                st.caption("Pending Queue: requests already arrived but still waiting for a slot.")
                if pending_queue_rows:
                    render_theme_table(pd.DataFrame(pending_queue_rows), height_px=320)
                else:
                    st.caption("No pending queue at this step.")

            with wait_col2:
                st.caption("Unassignable Waiting List: requests that cannot be routed to any staff.")
                if waiting_rows:
                    waiting_display_rows = [
                        {k: v for k, v in row.items() if not str(k).startswith("_")}
                        for row in waiting_rows
                    ]
                    render_theme_table(pd.DataFrame(waiting_display_rows), height_px=320)
                else:
                    st.caption("No unassignable waiting requests at this step.")

        if st.session_state.playback_playing:
            if st.session_state.playback_frame < max_step:
                tm.sleep(SPEED_OPTIONS.get(st.session_state.playback_speed, 0.45))
                st.session_state.playback_frame += 1
                st.rerun()
            else:
                st.session_state.playback_playing = False