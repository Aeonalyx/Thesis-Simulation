import streamlit as st
import pandas as pd
import plotly.graph_objects as go


# ============================================================
# PLAYBACK CONTROLS
# ============================================================

def render_playback_controls(max_step: int, SPEED_OPTIONS: dict, on_slider_change):
    st.header("Playback")

    controls = st.columns(6)

    if controls[0].button("▶ Play", use_container_width=True):
        st.session_state.playback_playing = True

    if controls[1].button("⏸ Pause", use_container_width=True):
        st.session_state.playback_playing = False

    if controls[2].button("◀ Step", use_container_width=True):
        st.session_state.playback_playing = False
        st.session_state.playback_frame = max(0, st.session_state.playback_frame - 1)

    if controls[3].button("Step ▶", use_container_width=True):
        st.session_state.playback_playing = False
        st.session_state.playback_frame = min(max_step, st.session_state.playback_frame + 1)

    if controls[4].button("⏭ End", use_container_width=True):
        st.session_state.playback_playing = False
        st.session_state.playback_frame = max_step

    controls[5].selectbox(
        "Speed",
        list(SPEED_OPTIONS.keys()),
        key="playback_speed"
    )

    st.slider(
        "Request Step",
        min_value=0,
        max_value=max_step,
        key="playback_frame_ui",
        on_change=on_slider_change,
    )


# ============================================================
# METRICS
# ============================================================

def render_playback_metrics(current_time, frame_data, pending_queue_rows, max_step):

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Simulation Clock", current_time.strftime("%Y-%m-%d %H:%M"))
    c2.metric("Current Step", f"{st.session_state.playback_frame}/{max_step}")
    c3.metric("Processed", frame_data["processed_count"])
    c4.metric("Assigned", frame_data["assigned_count"])
    c5.metric("Queue Size", len(pending_queue_rows) + frame_data["waiting_count"])


# ============================================================
# CURRENT EVENT DISPLAY
# ============================================================

def render_current_decision(current_event, format_staff_label, staff_college_map):

    st.markdown(
        "**Current Routing Decision:** "
        f"{current_event.get('event_type')} | "
        f"Request={current_event.get('request_id')} | "
        f"Staff={format_staff_label(current_event.get('staff_id'), staff_college_map)} | "
        f"Details={current_event.get('details')}"
    )


# ============================================================
# CAPACITY CHART
# ============================================================

def render_capacity_chart(capacity_rows):

    df = pd.DataFrame(capacity_rows)

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            name="Assigned Today",
            x=df["Staff"],
            y=df["Assigned Today"],
        )
    )

    if "Quota/Day" in df.columns:
        fig.add_trace(
            go.Bar(
                name="Quota",
                x=df["Staff"],
                y=df["Quota/Day"],
                opacity=0.5,
            )
        )

    fig.update_layout(
        title="Daily Staff Capacity",
        xaxis_title="Staff",
        yaxis_title="Requests",
        barmode="group",
        height=360,
    )

    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# STAFF LISTS
# ============================================================

def render_staff_lists(engine, staff_rows, staff_meta, assigned_maps, quota_enforced, format_staff_label, staff_college_map):

    st.subheader("Live Staff Request Lists")

    ordered_ids = [s.staff_id for s in engine.staff_pool]

    for i in range(0, len(ordered_ids), 3):
        cols = st.columns(3)

        for col, staff_id in zip(cols, ordered_ids[i:i+3]):

            with col:
                meta = staff_meta.get(staff_id, {"college": "-", "quota": None})

                assigned_today = assigned_maps["assigned_today"].get(staff_id, 0)
                total_assigned = assigned_maps["total_assigned"].get(staff_id, 0)

                if quota_enforced and meta.get("quota") is not None:
                    st.metric(
                        f"{staff_id} ({meta['college']})",
                        f"{assigned_today}/{meta['quota']}",
                        delta=f"Total {total_assigned}",
                    )
                else:
                    st.metric(
                        f"{staff_id}",
                        f"{total_assigned} assigned",
                    )

                rows = staff_rows.get(staff_id, [])

                if rows:
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, height=300)
                else:
                    st.caption("No requests yet.")


# ============================================================
# QUEUES
# ============================================================

def render_queue_tables(pending_queue_rows, waiting_rows):

    st.subheader("Queue and Waiting Lists")

    c1, c2 = st.columns(2)

    with c1:
        st.caption("Pending Queue")
        if pending_queue_rows:
            st.dataframe(pd.DataFrame(pending_queue_rows), use_container_width=True, height=300)
        else:
            st.caption("No pending queue.")

    with c2:
        st.caption("Waiting / Unassignable")
        if waiting_rows:
            st.dataframe(pd.DataFrame(waiting_rows), use_container_width=True, height=300)
        else:
            st.caption("No waiting requests.")


# ============================================================
# AUTOPLAY LOOP
# ============================================================

import time as tm


def handle_playback_autorun(max_step: int, SPEED_OPTIONS: dict):

    if not st.session_state.get("playback_playing", False):
        return

    if st.session_state.playback_frame < max_step:
        tm.sleep(SPEED_OPTIONS.get(st.session_state.playback_speed, 0.4))
        st.session_state.playback_frame += 1
        st.rerun()
    else:
        st.session_state.playback_playing = False