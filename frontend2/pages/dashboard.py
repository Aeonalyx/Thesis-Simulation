import streamlit as st


def show_dashboard(ctx):

    if not ctx.is_ready():
        st.info("Run simulation first.")
        return

    results = ctx.results
    engine = ctx.engine

    st.success("Simulation complete")

    st.markdown(
        f"""
        <div class="hero-band">
            <div>
                <p class="hero-kicker">Simulation Snapshot</p>
                <p class="hero-title">
                    Scheduler: {results.get('scheduler_type')} |
                    Allocator: {results.get('allocator_type')}
                </p>
                <p class="hero-sub">
                    Seed: {results.get('seed_used')}
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.metric("Total Requests", len(engine.completed))
    st.metric("Processed", results.get("total_processed", 0))