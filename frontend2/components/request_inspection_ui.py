import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def render_filters(colleges, doc_types, sort_options):
    c1, c2, c3 = st.columns(3)

    with c1:
        filter_college = st.selectbox("Filter by College", ["All"] + colleges)

    with c2:
        filter_doc = st.selectbox("Filter by Document", ["All"] + doc_types)

    with c3:
        sort_by = st.selectbox("Sort by", sort_options, index=0)

    return filter_college, filter_doc, sort_by


def render_request_table(df):
    st.dataframe(df, use_container_width=True, height=430)


def render_selected_request(req, format_compact_datetime, format_staff_label, staff_college_map):
    st.subheader("Detailed Request Panel")

    d1, d2 = st.columns(2)

    with d1:
        st.write(f"**Request ID:** {req['request_id']}")
        st.write(f"**College:** {req['college']}")
        st.write(f"**Document Type:** {req['document_type']}")
        st.write(f"**Completeness:** {req['completeness']:.2f}")
        st.write(f"**Requester Status:** {req['requester_type']}")
        st.write(f"**Payment Status:** {req['payment_status']}")
        st.write(f"**Priority Score:** {req['priority_score']:.4f}")
        st.write(f"**Assigned Staff:** {format_staff_label(req['assigned_staff'], staff_college_map)}")

    with d2:
        st.write(f"**Submission:** {format_compact_datetime(req['submission_time'])}")
        st.write(f"**Assignment:** {format_compact_datetime(req['assignment_time'])}")
        st.write(f"**Completion:** {format_compact_datetime(req['completion_time'])}")

    return req["req"]


def render_priority_progression(stage_df):
    st.subheader("Priority Score Progression")
    if not stage_df.empty:
        st.dataframe(stage_df, use_container_width=True, height=220)
    else:
        st.write("No stage timestamps available.")


def render_lifecycle_chart(fig):
    st.subheader("Request Lifecycle Timeline")
    st.plotly_chart(fig, use_container_width=True)