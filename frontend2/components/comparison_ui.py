import streamlit as st


def render_comparison_controls(SCHEDULER_OPTIONS, ALLOCATOR_OPTIONS):
    c1, c2 = st.columns(2)

    with c1:
        schedulers = st.multiselect("Schedulers", SCHEDULER_OPTIONS, default=SCHEDULER_OPTIONS)

    with c2:
        allocators = st.multiselect("Allocators", ALLOCATOR_OPTIONS, default=ALLOCATOR_OPTIONS)

    run = st.button("Run Comparison Across Selected Variants", use_container_width=True)

    return schedulers, allocators, run


def render_comparison_table(df):
    st.dataframe(df, use_container_width=True, height=360)


def render_export_csv(df, filename):
    csv = df.to_csv(index=False)
    st.download_button(
        "Download Results CSV",
        data=csv,
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
    )


def render_export_json(json_data, filename):
    import json

    st.download_button(
        "Download Run Config JSON",
        data=json.dumps(json_data, indent=2),
        file_name=filename,
        mime="application/json",
        use_container_width=True,
    )