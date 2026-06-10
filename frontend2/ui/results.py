import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import List, Dict
from datetime import datetime

from components.charts import (
apply_plot_theme, 
render_theme_table, 
build_workload_imbalance_chart,
build_variant_summary_chart,
)

from backend2.engine import (
SimulationEngine,
calculate_priority
)

from components.config import (
SCHEDULER_OPTIONS,
SCHEDULER_LABELS,
ALLOCATOR_OPTIONS,
ALLOCATOR_LABELS,
humanize_option_label,
)

from components.simulation import (
parse_event_time,
normalized_weights_from_ui,
)

# ============================================================================
# MAIN RESULTS
# ============================================================================

def render_results(ctx, snapshot):
    engine = ctx.engine
    results = ctx.results
    is_weighted_scheduler = ctx.is_weighted

    if not engine or not results:
        st.info("Use the sidebar controls, then click Run to start the simulation.")
        st.stop()

    st.success("Simulation complete.")

    seed_used = snapshot.get("seed_used")
    absence_count = snapshot.get("num_absent_staff", 0)
    absence_text = f"ON ({absence_count} Staff)" if absence_count > 0 else "OFF"

    st.markdown(
        f"""
        <div class="hero-band">
            <div>
                <p class="hero-kicker">Simulation Snapshot</p>
                <p class="hero-title">
                    Scheduler: {SCHEDULER_LABELS.get(snapshot.get('scheduler_type'), snapshot.get('scheduler_type'))} |
                    Allocator: {ALLOCATOR_LABELS.get(snapshot.get('allocator_type'), str(snapshot.get('allocator_type')).replace('_', ' ').title())}
                </p>
                <p class="hero-sub">
                    Seed: {seed_used} |
                    ⚙️ Requests: {snapshot.get('total_requests')} |
                    ⚖️ Imbalance: {snapshot.get('imbalance_factor')}%
                </p>
                <p class="hero-sub">
                    👥 Absence: {absence_text} |
                    ⚡ Urgency: {"ON" if snapshot.get("urgency") else "OFF"} |
                    🔥 Peak: {"ON" if snapshot.get("peak_mode") else "OFF"}
                </p>
            </div>
            <div class="hero-pill">Ready for playback</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ============================================================================
# COMPARISON TOOLS
# ============================================================================

def render_comparison(ctx):
    st.header("Comparison Tools")

    results = ctx.results
    session = ctx.session

    c1, c2 = st.columns(2)
    with c1:
        compare_schedulers = st.multiselect(
            "Schedulers",
            SCHEDULER_OPTIONS,
            default=SCHEDULER_OPTIONS,
            format_func=lambda v: ctx.scheduler_labels.get(v, v),
        )
    with c2:
        compare_allocators = st.multiselect(
            "Allocators",
            ALLOCATOR_OPTIONS,
            default=ALLOCATOR_OPTIONS,
            format_func=lambda v: ctx.allocator_labels.get(v, v.replace("_", " ").title()),
        )

    if st.button("Run Comparison Across Selected Variants", use_container_width=True):
        if not compare_schedulers or not compare_allocators:
            st.warning("Select at least one scheduler and one allocator.")
        else:
            compare_rows = []
            compare_details = []
            same_seed = int(results.get("seed_used", session.get("manual_seed", 42)))

            for scheduler in compare_schedulers:
                for allocator in compare_allocators:
                    compare_engine = SimulationEngine(
                        scheduler_type=scheduler,
                        allocator_type=allocator,
                        staff_config={
                            "num_staff": int(st.session_state.num_staff),
                            "quota_limit": int(st.session_state.quota_limit),
                        },
                        priority_weights=normalized_weights_from_ui(),
                        random_seed=same_seed,
                        work_start=st.session_state.work_start_time.strftime("%H:%M"),
                        work_end=st.session_state.work_end_time.strftime("%H:%M"),
                        urgency= st.session_state.urgency,
                    )
                    compare_result = compare_engine.run(
                        custom_config={
                            "scenario": "peak_period" if st.session_state.peak_mode else "baseline",
                            "total_requests": int(st.session_state.total_requests),
                            "urgency": bool(st.session_state.urgency),
                            "imbalance_factor": int(st.session_state.imbalance_factor),
                            "num_absent_staff": int(st.session_state.num_absent_staff),
                        }
                    )

                    compare_details.append(
                        {
                            "scheduler": scheduler,
                            "allocator": allocator,
                            "completed_requests": compare_result.get("completed_requests", []),
                        }
                    )

                    staff_load_values = list(compare_result.get("staff_load", {}).values())
                    staff_load_std = float(pd.Series(staff_load_values).std(ddof=0)) if staff_load_values else 0.0
                    staff_load_mean = float(pd.Series(staff_load_values).mean()) if staff_load_values else 0.0
                    staff_load_cv = round(staff_load_std / max(staff_load_mean, 1.0), 4) if staff_load_mean else 0.0

                    compare_rows.append(
                        {
                            "scheduler": scheduler,
                            "allocator": allocator,
                            "total_processed": compare_result.get("total_processed", 0),
                            "avg_waiting_time_hours": compare_result.get("avg_waiting_time_hours", 0.0),
                            "avg_turnaround_days": compare_result.get("avg_turnaround_days", 0.0),
                            "total_days_elapsed": compare_result.get("total_days_elapsed", 0.0),
                            "throughput_req_per_day": compare_result.get("throughput_req_per_day", 0.0),
                            "staff_load_std": round(staff_load_std, 2),
                            "staff_load_cv": round(staff_load_cv, 4),
                        }
                    )

            compare_df = pd.DataFrame(compare_rows)

            baseline = compare_df[
                (compare_df["scheduler"] == "FCFS")
                & (compare_df["allocator"] == "college_based")
            ]

            if baseline.empty:
                baseline_row = compare_df.iloc[0]
            else:
                baseline_row = baseline.iloc[0]

            compare_df["delta_wait_vs_baseline"] = (
                compare_df["avg_waiting_time_hours"] - baseline_row["avg_waiting_time_hours"]
            ).round(2)
            compare_df["delta_throughput_vs_baseline"] = (
                compare_df["throughput_req_per_day"] - baseline_row["throughput_req_per_day"]
            ).round(2)
            compare_df["delta_turnaround_vs_baseline"] = (
                compare_df["avg_turnaround_days"] - baseline_row["avg_turnaround_days"]
            ).round(2)

            st.session_state.comparison_df = compare_df
            st.session_state.comparison_details = compare_details

    if st.session_state.comparison_df is not None:
        # Prepare display dataframe from the stored comparison results
        compare_df = st.session_state.comparison_df.copy()

        # Formal allocator and scheduler labels
        ALLOCATOR_LABELS = {
            "college_based": "College Based",
            "workload_based": "Workload Based",
            "pooled": "Pooled",
            "quota_free": "Quota Free",
        }

        # Use existing SCHEDULER_LABELS for scheduler display where available
        scheduler_display = compare_df["scheduler"].map(lambda s: SCHEDULER_LABELS.get(s, str(s)))
        allocator_display = compare_df["allocator"].map(lambda a: ALLOCATOR_LABELS.get(a, str(a).replace("_", " ").title()))
        compare_df["Variant"] = scheduler_display + " | " + allocator_display

        st.subheader("Variant Comparison Table")
        st.caption("Use the filters below to select which variants and columns appear in the comparison table.")

        # Variant filter (multi-select)
        variant_options = list(compare_df["Variant"].unique())
        selected_variants = st.multiselect("Show variants", variant_options, default=variant_options)
        if selected_variants:
            compare_df = compare_df[compare_df["Variant"].isin(selected_variants)].copy()

        # Column selector for the comparison table — exclude scheduler/allocator because Variant summarizes them
        available_cols = [
            c
            for c in compare_df.columns
            if c not in ("Variant", "scheduler", "allocator")
        ]
        # Put Variant first in defaults
        default_cols = ["Variant"] + available_cols
        selected_cols = st.multiselect(
            "Columns to display",
            options=default_cols,
            default=default_cols,
            format_func=humanize_option_label,
        )

        if not selected_cols:
            st.info("Select at least one column to display the comparison table.")
        else:
            # Human-friendly column labels
            def human_label(col: str) -> str:
                labels = {
                    "scheduler": "Scheduler",
                    "allocator": "Allocator",
                    "Variant": "Variant",
                    "total_processed": "Total Processed",
                    "avg_waiting_time_hours": "Avg Waiting Time (h)",
                    "avg_turnaround_days": "Avg Turnaround (d)",
                    "total_days_elapsed": "Total Days Elapsed",
                    "throughput_req_per_day": "Throughput (req/day)",
                    "staff_load_std": "Staff Load Std Dev",
                    "staff_load_cv": "Staff Load CV",
                    "delta_wait_vs_baseline": "Δ Wait vs Baseline (h)",
                    "delta_throughput_vs_baseline": "Δ Throughput vs Baseline",
                    "delta_turnaround_vs_baseline": "Δ Turnaround vs Baseline (d)",
                    "order_changed_pct": "Order Changed (%)",
                }
                if col in labels:
                    return labels[col]
                # fallback: turn snake_case into Title Case
                return str(col).replace("_", " ").title()

            # Build display DataFrame and rename columns for presentation
            display_df = compare_df[selected_cols].copy()
            rename_map = {c: human_label(c) for c in display_df.columns}
            display_df.rename(columns=rename_map, inplace=True)

            render_theme_table(display_df, height_px=420)

            # Also show charts for the filtered variants
            imbalance_fig = build_workload_imbalance_chart(compare_df)
            if imbalance_fig.data:
                st.subheader("Workload Imbalance by Variant")
                st.plotly_chart(imbalance_fig, use_container_width=True)

            summary_fig = build_variant_summary_chart(compare_df)
            if summary_fig.data:
                st.subheader("Variant Performance Summary")
                st.plotly_chart(summary_fig, use_container_width=True)

    comparison_details = st.session_state.get("comparison_details")
    if st.session_state.comparison_df is not None and comparison_details:
        st.subheader("Request-Level Differences")

        def _build_request_index(completed_requests: List[Dict]) -> Dict[str, Dict[str, object]]:
            rows = []
            for item in completed_requests:
                request_id = item.get("request_id")
                if not request_id:
                    continue
                assign_raw = item.get("assignment_time")
                complete_raw = item.get("completion_time")
                rows.append(
                    {
                        "request_id": request_id,
                        "assignment_time": parse_event_time(str(assign_raw)) if assign_raw else None,
                        "completion_time": parse_event_time(str(complete_raw)) if complete_raw else None,
                        "assigned_staff": item.get("assigned_staff"),
                    }
                )

            rows = sorted(
                rows,
                key=lambda r: (r["assignment_time"] or datetime.max, r["request_id"]),
            )
            index: Dict[str, Dict[str, object]] = {}
            for rank, row in enumerate(rows, start=1):
                index[row["request_id"]] = {
                    "rank": rank,
                    "assignment_time": row["assignment_time"],
                    "completion_time": row["completion_time"],
                    "assigned_staff": row["assigned_staff"],
                }
            return index

        compare_df = st.session_state.comparison_df
        baseline_row = compare_df.iloc[0]
        baseline_match = compare_df[
            (compare_df["scheduler"] == "FCFS")
            & (compare_df["allocator"] == "college_based")
        ]
        if not baseline_match.empty:
            baseline_row = baseline_match.iloc[0]

        baseline_key = (baseline_row["scheduler"], baseline_row["allocator"])
        baseline_details = next(
            (
                item
                for item in comparison_details
                if (item["scheduler"], item["allocator"]) == baseline_key
            ),
            None,
        )

        if baseline_details is None:
            st.info("Baseline details not available for request-level comparison.")
        else:
            baseline_index = _build_request_index(baseline_details["completed_requests"])
            baseline_requests = set(baseline_index.keys())

            diff_rows = []
            for item in comparison_details:
                scheduler = item["scheduler"]
                allocator = item["allocator"]
                key = (scheduler, allocator)
                if key == baseline_key:
                    continue

                current_index = _build_request_index(item["completed_requests"])
                current_requests = set(current_index.keys())
                common = baseline_requests.intersection(current_requests)

                if not common:
                    continue

                order_changed = 0
                staff_changed = 0
                rank_shift_total = 0.0
                assign_delta_total = 0.0
                complete_delta_total = 0.0

                for request_id in common:
                    base = baseline_index[request_id]
                    current = current_index[request_id]
                    if base["rank"] != current["rank"]:
                        order_changed += 1
                        rank_shift_total += abs(current["rank"] - base["rank"])
                    if base.get("assigned_staff") != current.get("assigned_staff"):
                        staff_changed += 1

                    base_assign = base.get("assignment_time")
                    current_assign = current.get("assignment_time")
                    if base_assign and current_assign:
                        assign_delta_total += abs((current_assign - base_assign).total_seconds()) / 60.0

                    base_complete = base.get("completion_time")
                    current_complete = current.get("completion_time")
                    if base_complete and current_complete:
                        complete_delta_total += abs((current_complete - base_complete).total_seconds()) / 60.0

                total_common = len(common)
                avg_rank_shift = rank_shift_total / max(order_changed, 1)
                avg_assign_delta = assign_delta_total / total_common
                avg_complete_delta = complete_delta_total / total_common

                diff_rows.append(
                    {
                        "scheduler": scheduler,
                        "allocator": allocator,
                        "order_changed_count": order_changed,
                        "order_changed_pct": round((order_changed / total_common) * 100.0, 2),
                        "avg_abs_rank_shift": round(avg_rank_shift, 2),
                        "staff_changed_count": staff_changed,
                        "staff_changed_pct": round((staff_changed / total_common) * 100.0, 2),
                        "avg_assign_time_delta_min": round(avg_assign_delta, 2),
                        "avg_complete_time_delta_min": round(avg_complete_delta, 2),
                    }
                )

            diff_df = pd.DataFrame(diff_rows)
            if diff_df.empty:
                st.info("No comparable request-level differences found.")
            else:
                raw_variant_options = [
                    (row["scheduler"], row["allocator"]) for row in diff_rows
                ]

                diff_df = diff_df.rename(
                    columns={
                        "scheduler": "Scheduler",
                        "allocator": "Allocator",
                        "order_changed_count": "Order Changed Count",
                        "order_changed_pct": "Order Changed %",
                        "avg_abs_rank_shift": "Avg Abs Rank Shift",
                        "staff_changed_count": "Staff Changed Count",
                        "staff_changed_pct": "Staff Changed %",
                        "avg_assign_time_delta_min": "Avg Assign Delta (min)",
                        "avg_complete_time_delta_min": "Avg Complete Delta (min)",
                    }
                )
                diff_df["Scheduler"] = diff_df["Scheduler"].map(
                    lambda s: SCHEDULER_LABELS.get(s, str(s))
                )
                diff_df["Allocator"] = diff_df["Allocator"].map(
                    lambda a: ALLOCATOR_LABELS.get(a, str(a).replace("_", " ").title())
                )

                render_theme_table(diff_df, height_px=320)

                fig_diff = go.Figure()
                fig_diff.add_trace(
                    go.Bar(
                        name="Order Changed %",
                        x=diff_df["Allocator"],
                        y=diff_df["Order Changed %"],
                        marker_color="#a855f7",
                        text=diff_df["Order Changed %"].apply(lambda v: f"{v:.1f}%"),
                    )
                )
                fig_diff.add_trace(
                    go.Bar(
                        name="Staff Changed %",
                        x=diff_df["Allocator"],
                        y=diff_df["Staff Changed %"],
                        marker_color="#22d3ee",
                        text=diff_df["Staff Changed %"].apply(lambda v: f"{v:.1f}%"),
                    )
                )
                fig_diff.update_layout(
                    title="Request-Level Changes vs Baseline",
                    xaxis_title="Allocator",
                    yaxis_title="Percent of Requests",
                    barmode="group",
                    height=320,
                )
                apply_plot_theme(fig_diff)
                st.plotly_chart(fig_diff, use_container_width=True)

                selected_variant = st.selectbox(
                    "Inspect Variant",
                    options=raw_variant_options,
                    format_func=lambda v: f"{SCHEDULER_LABELS.get(v[0], v[0])} | {ALLOCATOR_LABELS.get(v[1], v[1].replace('_', ' ').title())}",
                    index=0,
                )

                if selected_variant:
                    selected_sched, selected_alloc = selected_variant
                    selected_detail = next(
                        (
                            item
                            for item in comparison_details
                            if item["scheduler"] == selected_sched
                            and item["allocator"] == selected_alloc
                        ),
                        None,
                    )
                    if selected_detail:
                        current_index = _build_request_index(
                            selected_detail["completed_requests"]
                        )
                        change_rows = []
                        for request_id in baseline_requests.intersection(current_index.keys()):
                            base = baseline_index[request_id]
                            current = current_index[request_id]
                            rank_shift = current["rank"] - base["rank"]
                            base_assign = base.get("assignment_time")
                            current_assign = current.get("assignment_time")
                            assign_delta = None
                            if base_assign and current_assign:
                                assign_delta = round(
                                    (current_assign - base_assign).total_seconds() / 60.0, 2
                                )
                            change_rows.append(
                                {
                                    "Request": request_id,
                                    "Rank Shift": rank_shift,
                                    "Assigned Staff": current.get("assigned_staff"),
                                    "Staff Changed": base.get("assigned_staff")
                                    != current.get("assigned_staff"),
                                    "Assign Delta (min)": assign_delta,
                                }
                            )

                        change_df = pd.DataFrame(change_rows)
                        change_df["_abs_shift"] = change_df["Rank Shift"].abs()
                        change_df = change_df.sort_values(
                            by=["_abs_shift", "Request"], ascending=[False, True]
                        ).drop(columns=["_abs_shift"])
                        render_theme_table(change_df.head(25), height_px=320)