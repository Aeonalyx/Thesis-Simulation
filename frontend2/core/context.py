import streamlit as st

def get_context():
    return st.session_state.sim_context


def set_context(engine=None, results=None, config=None):
    ctx = st.session_state.sim_context

    if engine is not None:
        ctx.engine = engine

    if results is not None:
        ctx.results = results

    if config is not None:
        ctx.config = config