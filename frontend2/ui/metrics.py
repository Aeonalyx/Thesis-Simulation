import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import sys
import math
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Optional
from datetime import datetime

from components.charts import (
apply_plot_theme, 
render_theme_table, 
build_baseline_queue_dynamics_chart, 
build_weighted_priority_distribution_chart,
)
from backend2.config import (
COLLEGES, 
DOCUMENT_COMPLEXITY,
REQUESTER_PRIORITY,
REQUESTER_PRIORITY_MAX, 
)
from backend2.engine import calculate_priority
from backend2.models import DocumentRequest
from backend2.rules import _duration_to_schedule, _soft_cap, COLLEGE_PRIORITY

from components.config import (
CHART_COLORWAY, 
format_variant_label,
humanize_option_label,
)

from components.simulation import (
format_compact_datetime, 
format_staff_label,
)

# ============================================================================
# KPI METRICS
# ============================================================================
def render_metrics(ctx):
    st.header("Key Metrics")

    engine = ctx.engine
    results = ctx.results
    staff_college_map = ctx.staff_map
    is_weighted_scheduler = ctx.is_weighted

    k1, k2, k3, k4, k5 = st.columns([.8, .8, .7, .7, 1.2])
    with k1:
        processed = int(results.get("total_processed", 0))
        expected = int(st.session_state.total_requests)
        pct = (processed / expected * 100.0) if expected > 0 else 0.0
        st.metric("Total Processed", f"{processed}/{expected}", f"{pct:.0f}%")
    with k2:
        avg_wait_hours = float(results.get("avg_waiting_time_hours", 0.0))
        st.metric(
            "Avg Queue Wait",
            f"{avg_wait_hours:.2f} h",
            f"{(avg_wait_hours / 24.0):.2f} d equiv",
        )
    with k3:
        avg_turn_days = float(results.get("avg_turnaround_days", 0.0))
        st.metric(
            "Avg Turnaround",
            f"{avg_turn_days:.2f} d",
            f"{(avg_turn_days * 24.0):.2f} h equiv",
        )
    with k4:
        elapsed_days = float(results.get("total_days_elapsed", 0.0))
        elapsed_day_index = max(1, int(math.floor(elapsed_days)) + 1)
        st.metric(
            "Days Elapsed",
            f"Day {elapsed_day_index}",
            f"{elapsed_days:.2f} d span",
        )
    with k5:
        st.metric("Throughput", f"{results.get('throughput_req_per_day', 0):.2f} req/day")

    if results.get("absent_staff"):
        st.warning("Absent staff: " + ", ".join(results.get("absent_staff", [])))

    variant_label = format_variant_label(
        results.get('scheduler_type', ''), results.get('allocator_type', '')
    )

    st.header("Visualizations")

    st.markdown(
        f"**Scheduler:** {humanize_option_label(results.get('scheduler_type'))}<br>"
        f"**Allocator:** {humanize_option_label(results.get('allocator_type'))}"
        , unsafe_allow_html=True,
    )

    # Toggle to place legend/labels outside the plot area for easier filtering
    labels_outside_default = st.session_state.get("labels_outside", True)
    st.checkbox(
        "Show labels outside charts (useful for filtering)",
        value=labels_outside_default,
        key="labels_outside",
    )

    fig_41 = build_baseline_queue_dynamics_chart(results.get("event_log", []), variant_label)
    if fig_41.data:
        st.plotly_chart(fig_41, use_container_width=True)
    else:
        st.info("Queue dynamics are not available for the selected simulation.")

    if results.get("scheduler_type") == "WEIGHTED":
        generated_requests = results.get("generated_requests", [])
        request_types = sorted(
            {
                (req.get("document_type") if isinstance(req, dict) else getattr(req, "document_type", None))
                for req in generated_requests
                if req is not None
            }
        )
        request_types = [rt for rt in request_types if rt]
        selected_request_types = st.multiselect(
            "Request types to include in the priority distribution",
            options=request_types,
            default=request_types,
            key="priority_distribution_doc_types",
        )

        if not selected_request_types:
            st.info("Select one or more request types to display the priority score distribution.")
        else:
            fig_43 = build_weighted_priority_distribution_chart(
                generated_requests,
                selected_request_types,
                variant_label,
            )
            if fig_43.data:
                st.plotly_chart(fig_43, use_container_width=True)
            else:
                st.info("Priority score distribution is not available for the selected simulation.")
    else:
        st.info("Priority score distribution is only shown for the WEIGHTED scheduler.")

# ============================================================================
# STAFF LOAD + TIMELINE CHARTS
# ============================================================================

    st.header("Staff and Timeline")

    staff_load = results.get("staff_load", {})
    if staff_load:
        staff_ids = list(staff_load.keys())
        staff_labels = [format_staff_label(staff_id, staff_college_map) for staff_id in staff_ids]
        staff_values = [staff_load[staff_id] for staff_id in staff_ids]
        fig_staff = go.Figure(
            data=[
                go.Bar(
                    x=staff_labels,
                    y=staff_values,
                    marker=dict(
                        color=staff_values,
                        colorscale=[
                            [0.0, "#5b21b6"],
                            [0.55, "#9333ea"],
                            [1.0, "#22d3ee"],
                        ],
                    ),
                    text=staff_values,
                    textposition="outside",
                )
            ]
        )
        fig_staff.update_layout(
            title=f"Requests Processed per Staff — {variant_label}",
            xaxis_title="Staff",
            yaxis_title="Processed Requests",
            height=450,
        )
        apply_plot_theme(fig_staff)
        st.plotly_chart(fig_staff, use_container_width=True)

    if engine.completed:
        timeline_rows = []
        for req in engine.completed:
            assigned_day = (req.assignment_time.date() - engine.start_time.date()).days + 1
            timeline_rows.append(
                {
                    "Assigned Day": assigned_day,
                    "College": req.college,
                    "Count": 1,
                }
            )
        timeline_df = pd.DataFrame(timeline_rows)
        grouped = timeline_df.groupby(["Assigned Day", "College"]).size().reset_index(name="Count")
        fig_timeline = px.bar(
            grouped,
            x="Assigned Day",
            y="Count",
            color="College",
            color_discrete_sequence=CHART_COLORWAY,
            title=f"Assignments per Day by College — {variant_label}",
            height=450,
            text="Count" if st.session_state.labels_outside else None,
        )
        apply_plot_theme(fig_timeline)
        st.plotly_chart(fig_timeline, use_container_width=True)

    if engine.completed:
        selected_college = st.selectbox(
            "Filter Document Mix by College",
            ["All"] + COLLEGES,
            key="doc_mix_college",
        )
        if selected_college == "All":
            filtered_docs = list(engine.completed)
        else:
            filtered_docs = [
                req for req in engine.completed if req.college == selected_college
            ]

        if filtered_docs:
            doc_df = pd.DataFrame(
                [{"document_type": req.document_type} for req in filtered_docs]
            )
            doc_counts = doc_df["document_type"].value_counts().reset_index()
            doc_counts.columns = ["Document", "Count"]
            total_docs = int(doc_counts["Count"].sum())

            short_doc_names = {
                "Certification, Authentication and Verification (CAV)": "CAV",
                "Official Transcript of Records (TOR) and Transfer Credentials (TC)": "TOR/TC",
                "Evaluation of Grades; Report of Grades (ROG); Certificate of Registration (COR)": "ROG/COR",
                "Permit to Cross-Enrol": "Cross-Enrol Permit",
                "Academic Load Revision (ALRP)": "ALRP",
                "Shifter’s Form, Returnee’s Form or Leave of Absence": "Shifter/Returnee/LOA",
                "Registration of Old and Returnee Students": "Old/Returnee Reg",
            }

            doc_left, doc_right = st.columns([2, 1])
            with doc_left:
                fig_docs = go.Figure(
                    data=[
                        go.Pie(
                            labels=doc_counts["Document"],
                            values=doc_counts["Count"],
                            hole=0.55,
                            textinfo="percent",
                        )
                    ]
                )
                fig_docs.update_layout(
                    title=f"Requested Document Mix (Completed) — {variant_label}",
                    height=420,
                    showlegend=False,
                )
                apply_plot_theme(fig_docs)
                st.plotly_chart(fig_docs, use_container_width=True)

            with doc_right:
                st.markdown(
                    f"<div style='font-size:0.9rem; color:#b6b0d4; margin-bottom:0.4rem;'>"
                    f"Total processed: <span style='color:#f5f3ff; font-weight:700;'>{total_docs}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                legend_rows = []
                for row in doc_counts.itertuples(index=False):
                    pct = (float(row.Count) / max(total_docs, 1)) * 100.0
                    label = short_doc_names.get(row.Document, row.Document)
                    legend_rows.append(
                        {
                            "label": label,
                            "count": int(row.Count),
                            "pct": pct,
                        }
                    )
                mid_point = (len(legend_rows) + 1) // 2
                legend_col1, legend_col2 = st.columns(2)
                for col, rows in zip(
                    [legend_col1, legend_col2],
                    [legend_rows[:mid_point], legend_rows[mid_point:]],
                ):
                    with col:
                        block = []
                        for item in rows:
                            block.append(
                                f"<div style='margin:0.3rem 0;'>"
                                f"<span style='font-weight:700; color:#e7e1fa;'>{item['label']}</span>"
                                f"<br />"
                                f"<span style='color:#a7a0c5;'>{item['count']}"
                                f" <span style='color:#7dd3fc;'>({item['pct']:.1f}%)</span></span>"
                                f"</div>"
                            )
                        st.markdown("".join(block), unsafe_allow_html=True)
        else:
            st.caption("No completed requests for the selected college.")

# ============================================================================
# REQUEST INSPECTION
# ============================================================================

    st.header("Request Inspection")

    completed_requests = engine.completed

    if not completed_requests:
        st.info("No completed requests to inspect.")
    else:
        f1, f2, f3 = st.columns(3)

        with f1:
            filter_college = st.selectbox("Filter by College", ["All"] + COLLEGES)
        with f2:
            filter_doc = st.selectbox("Filter by Document", ["All"] + list(DOCUMENT_COMPLEXITY.keys()))
        with f3:
            sort_options = [
                "Assigned Day",
                "Submission Time",
                "Staff List Order",
                "Queue Wait Desc",
                "Queue Wait Asc",
                "Turnaround Desc",
            ]
            if is_weighted_scheduler:
                sort_options = ["Priority Desc", "Priority Asc"] + sort_options

            sort_by = st.selectbox(
                "Sort by",
                sort_options,
                index=0,
            )

        filtered = completed_requests
        if filter_college != "All":
            filtered = [req for req in filtered if req.college == filter_college]
        if filter_doc != "All":
            filtered = [req for req in filtered if req.document_type == filter_doc]

        staff_order = {staff.staff_id: idx for idx, staff in enumerate(engine.staff_pool)}

        if sort_by == "Priority Desc":
            filtered = sorted(
                filtered,
                key=lambda req: (-float(getattr(req, "priority_score", 0.0)), req.submission_time),
            )
        elif sort_by == "Priority Asc":
            filtered = sorted(
                filtered,
                key=lambda req: (float(getattr(req, "priority_score", 0.0)), req.submission_time),
            )
        elif sort_by == "Assigned Day":
            filtered = sorted(
                filtered,
                key=lambda req: (
                    req.assignment_time.date(),
                    req.completion_time,
                    req.submission_time,
                ),
            )
        elif sort_by == "Submission Time":
            filtered = sorted(filtered, key=lambda req: req.submission_time)
        elif sort_by == "Staff List Order":
            filtered = sorted(
                filtered,
                key=lambda req: (
                    req.assignment_time,
                    staff_order.get(req.assigned_staff, 9999),
                    req.submission_time,
                ),
            )
        elif sort_by == "Queue Wait Desc":
            filtered = sorted(filtered, key=lambda req: req.get_waiting_time_minutes(), reverse=True)
        elif sort_by == "Queue Wait Asc":
            filtered = sorted(filtered, key=lambda req: req.get_waiting_time_minutes())
        else:
            filtered = sorted(filtered, key=lambda req: req.get_turnaround_time_minutes(), reverse=True)

        table_rows = []
        for idx, req in enumerate(filtered):
            assigned_day = (req.assignment_time.date() - engine.start_time.date()).days + 1
            table_rows.append(
                {
                    "Row": idx + 1,
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
                }
            )

        table_df = pd.DataFrame(table_rows)
        render_theme_table(table_df, height_px=430)

        st.subheader("Detailed Request Panel")
        pick_index = st.number_input(
            "Select Row",
            min_value=1,
            max_value=max(1, len(filtered)),
            value=1,
            step=1,
        )

        selected_req = filtered[int(pick_index) - 1]
        d1, d2 = st.columns(2)

        with d1:
            st.write(f"**Request ID:** {selected_req.request_id}")
            st.write(f"**College:** {selected_req.college}")
            st.write(f"**Document Type:** {selected_req.document_type}")
            st.write(
                f"**Completeness:** {float(getattr(selected_req, 'completeness_of_requirements', 0.0)):.2f}"
            )
            st.write(f"**Requester Status:** {getattr(selected_req, 'requester_type', '-')}")
            st.write(f"**Urgency (generated):** {getattr(selected_req, 'urgency', '-')}")
            st.write(f"**Payment Status:** {getattr(selected_req, 'payment_status', '-')}")
            st.write(f"**Priority Score:** {float(getattr(selected_req, 'priority_score', 0.0)):.4f}")
            st.write(f"**Assigned Staff:** {format_staff_label(selected_req.assigned_staff, staff_college_map)}")

        with d2:
            st.write(f"**Submission:** {format_compact_datetime(selected_req.submission_time)}")
            st.write(
                "**Requirements Partial:** "
                f"{format_compact_datetime(getattr(selected_req, 'requirements_partial_time', None))}"
            )
            st.write(
                "**Requirements Complete:** "
                f"{format_compact_datetime(getattr(selected_req, 'requirements_complete_time', None))}"
            )
            st.write(
                "**Payment Time:** "
                f"{format_compact_datetime(getattr(selected_req, 'payment_time', None))}"
            )
            st.write(
                "**Ready Time:** "
                f"{format_compact_datetime(getattr(selected_req, 'ready_time', None))}"
            )
            st.write(f"**Assignment:** {format_compact_datetime(selected_req.assignment_time)}")
            st.write(f"**Completion:** {format_compact_datetime(selected_req.completion_time)}")
            st.write(f"**Queue Wait:** {selected_req.get_waiting_time_minutes() / 60.0:.2f} h")
            st.write(f"**Turnaround:** {selected_req.get_turnaround_time_minutes() / 1440.0:.2f} d")

        if is_weighted_scheduler:
            st.subheader("Priority Score Progression")

            def _score_at(
                    request_obj: DocumentRequest,
                    at_time: Optional[datetime]
                ) -> Optional[float]:

                    if at_time is None:
                        return None

                    original_state = (
                        request_obj.completeness_of_requirements,
                        request_obj.payment_status,
                        request_obj.requirements_stage,
                        request_obj.priority_score,
                    )

                    try:
                        return calculate_priority(
                            request_obj,
                            at_time,
                            engine.priority_weights,
                            engine.workday_minutes,
                            urgency=engine.urgency,
                        )

                    finally:
                        (
                            request_obj.completeness_of_requirements,
                            request_obj.payment_status,
                            request_obj.requirements_stage,
                            request_obj.priority_score,
                        ) = original_state

            stage_points = [
                ("Submitted", selected_req.submission_time),
                ("Requirements Partial", getattr(selected_req, "requirements_partial_time", None)),
                ("Requirements Complete", getattr(selected_req, "requirements_complete_time", None)),
                ("Payment", getattr(selected_req, "payment_time", None)),
                ("Ready", getattr(selected_req, "ready_time", None)),
                ("Assigned", selected_req.assignment_time),
            ]
            stage_rows = []
            for label, ts in stage_points:
                if ts is None:
                    continue
                score_value = _score_at(selected_req, ts)
                stage_rows.append(
                    {
                        "Stage": label,
                        "Time": format_compact_datetime(ts),
                        "Priority Score": round(float(score_value or 0.0), 4),
                    }
                )
            if stage_rows:
                stage_df = pd.DataFrame(stage_rows)
                render_theme_table(stage_df, height_px=220)
                # Debug breakdown: show engine weights and per-criterion contributions
                with st.expander("Debug: weight & contribution breakdown", expanded=False):
                    st.write("Engine priority_weights:")
                    st.write(engine.priority_weights)

                    contrib_rows = []
                    # Recompute per-stage contributions using same logic as calculate_priority
                    for label, ts in stage_points:
                        if ts is None:
                            continue
                        # compute feature scores
                        selected_req.update_status(ts)
                        completeness_norm = max(0.0, min(float(selected_req.completeness_of_requirements), 1.0))
                        requester_raw = REQUESTER_PRIORITY.get(selected_req.requester_type, 3)
                        requester_norm = requester_raw / max(float(REQUESTER_PRIORITY_MAX), 1.0)
                        waiting_minutes = max(0.0, (ts - selected_req.submission_time).total_seconds() / 60.0)
                        submission_norm = _soft_cap(waiting_minutes, max(float(engine.workday_minutes * 2), 1.0))
                        base_duration, _ = _duration_to_schedule(DOCUMENT_COMPLEXITY.get(selected_req.document_type, 1))
                        complexity_days = max(base_duration.total_seconds() / 86400.0, 1e-6)
                        doc_norm = 1.0 / (1.0 + complexity_days)
                        college_norm = float(COLLEGE_PRIORITY.get(selected_req.college, 0.5))
                        payment_norm = 0.0
                        if isinstance(selected_req.payment_status, str):
                            status_text = selected_req.payment_status.strip().lower()
                            if status_text in {"paid", "settled", "complete", "cleared", "yes", "y", "true", "1"}:
                                payment_norm = 1.0
                        else:
                            payment_norm = 1.0 if bool(selected_req.payment_status) else 0.0
                        urgency_norm = float(selected_req.urgency) / 10.0 if engine.urgency else 0.0

                        scores_map = {
                            "completeness_of_requirements": completeness_norm,
                            "submission_time": submission_norm,
                            "document_type": doc_norm,
                            "requester_status": requester_norm,
                            "college_affiliation": college_norm,
                            "payment_status": payment_norm,
                            "urgency": urgency_norm,
                        }

                        total_raw = 0.0
                        for k, w in engine.priority_weights.items():
                            if k == "urgency" and not engine.urgency:
                                continue
                            val = scores_map.get(k, 0.0)
                            contrib = float(w) * float(val)
                            total_raw += contrib
                            contrib_rows.append(
                                {
                                    "Stage": label,
                                    "Criterion": k,
                                    "Weight": round(float(w), 6),
                                    "Feature": round(float(val), 6),
                                    "Contribution": round(float(contrib), 6),
                                }
                            )

                        contrib_rows.append(
                            {"Stage": label, "Criterion": "TOTAL", "Weight": "-", "Feature": "-", "Contribution": round(total_raw, 6)}
                        )

                    if contrib_rows:
                        contrib_df = pd.DataFrame(contrib_rows)
                        render_theme_table(contrib_df)
            else:
                st.write("No stage timestamps available.")

        st.subheader("Request Lifecycle Timeline")

        lifecycle_times = [
            selected_req.submission_time,
            selected_req.assignment_time,
            selected_req.completion_time,
        ]
        lifecycle_labels = [
            "Submitted",
            f"Assigned ({format_staff_label(selected_req.assigned_staff, staff_college_map)})",
            "Completed",
        ]
        lifecycle_colors = ["#22d3ee", "#a855f7", "#f472b6"]
        lifecycle_y = [2.0, 1.0, 0.0]

        # Stair path so labels do not get mushed in a single horizontal line.
        step_x = [
            lifecycle_times[0],
            lifecycle_times[1],
            lifecycle_times[1],
            lifecycle_times[2],
            lifecycle_times[2],
        ]
        step_y = [
            lifecycle_y[0],
            lifecycle_y[0],
            lifecycle_y[1],
            lifecycle_y[1],
            lifecycle_y[2],
        ]

        fig_request_timeline = go.Figure()
        fig_request_timeline.add_trace(
            go.Scatter(
                x=step_x,
                y=step_y,
                mode="lines",
                line=dict(color="#8b79bb", width=3),
                hoverinfo="skip",
                showlegend=False,
            )
        )
        fig_request_timeline.add_trace(
            go.Scatter(
                x=lifecycle_times,
                y=lifecycle_y,
                mode="markers+text",
                text=lifecycle_labels,
                textposition=["top left", "middle right", "bottom right"],
                marker=dict(size=14, color=lifecycle_colors),
                showlegend=False,
                customdata=lifecycle_labels,
                hovertemplate="%{customdata}<br>%{x}<extra></extra>",
            )
        )
        fig_request_timeline.update_layout(
            height=320,
            xaxis_title="Time",
            yaxis=dict(
                showticklabels=False,
                showgrid=False,
                zeroline=False,
                range=[-0.5, 2.5],
            ),
            margin=dict(l=20, r=20, t=20, b=20),
        )
        apply_plot_theme(fig_request_timeline)
        fig_request_timeline.update_yaxes(showgrid=False)
        st.plotly_chart(fig_request_timeline, use_container_width=True)

# ============================================================================
# EXPORT TOOLS
# ============================================================================

def export_tools(ctx):
    st.header("Export and Reproducibility")
    engine = ctx.engine
    results = ctx.results
    session = ctx.session

    if engine.completed:
        export_df = pd.DataFrame(
            [
                {
                    "request_id": req.request_id,
                    "college": req.college,
                    "document_type": req.document_type,
                    "requester_status": getattr(req, "requester_type", "-"),
                    "completeness_of_requirements": round(
                        float(getattr(req, "completeness_of_requirements", 0.0)),
                        4,
                    ),
                    "payment_status": getattr(req, "payment_status", "-"),
                    "submission_time": req.submission_time.isoformat(),
                    "assignment_time": req.assignment_time.isoformat() if req.assignment_time else None,
                    "completion_time": req.completion_time.isoformat() if req.completion_time else None,
                    "queue_wait_hours": round(req.get_waiting_time_minutes() / 60.0, 4),
                    "turnaround_days": round(req.get_turnaround_time_minutes() / 1440.0, 4),
                    "assigned_staff": req.assigned_staff,
                }
                for req in engine.completed
            ]
        )

        csv_data = export_df.to_csv(index=False)
        st.download_button(
            "Download Results CSV",
            data=csv_data,
            file_name=f"simulation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    if st.session_state.last_run_config:
        config_json = {
            "generated_at": datetime.now().isoformat(),
            "seed_used": results.get("seed_used"),
            "scheduler_type": results.get("scheduler_type"),
            "allocator_type": results.get("allocator_type"),
            "mode": "custom_sliders",
            "work_hours": results.get("work_hours"),
            "priority_weights": results.get("priority_weights"),
            "run_config": st.session_state.last_run_config.get("run_config", {}),
            "ui_config": st.session_state.last_run_config.get("ui_config", {}),
        }
        st.download_button(
            "Download Run Config JSON",
            data=json.dumps(config_json, indent=2),
            file_name=f"simulation_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
        )