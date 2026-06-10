import streamlit as st
from dataclasses import dataclass
from frontend2.components.simulation import build_staff_college_map
from frontend2.components.config import SCHEDULER_LABELS, ALLOCATOR_LABELS


@dataclass
class SimulationContext:
    engine: object
    results: dict
    snapshot: dict
    staff_map: dict
    session: object
    scheduler_labels: dict
    allocator_labels: dict

    @property
    def is_weighted(self) -> bool:
        return self.results.get("scheduler_type") == "WEIGHTED"


def get_context() -> SimulationContext:
    if (
        "simulation_engine" not in st.session_state
        or "simulation_results" not in st.session_state
        or st.session_state.simulation_engine is None
        or st.session_state.simulation_results is None
    ):
        st.info("Use sidebar controls, then click Run to start simulation.")
        st.stop()

    engine = st.session_state.simulation_engine
    results = st.session_state.simulation_results
    snapshot = st.session_state.get("run_snapshot", {})

    return SimulationContext(
        engine=engine,
        results=results,
        snapshot=snapshot,
        staff_map=build_staff_college_map(engine.staff_pool),
        session=st.session_state,
        scheduler_labels=SCHEDULER_LABELS,
        allocator_labels=ALLOCATOR_LABELS,
    )