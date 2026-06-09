# Thesis-Simulation

istall the requiremtns first

adadasd;asmdko


thesis-simulation/
│
├── frontend/
│   ├── app.py                 # Streamlit entry point (navigation only)
│   ├── pages/
│   │   ├── dashboard.py
│   │   ├── simulation.py
│   │   └── results.py
│   ├── api.py                # all API calls
│   ├── components.py         # all UI components
│   ├── state.py              # session_state handling
│   └── config.py             # frontend config (dropdowns, defaults)
│
├── backend/
│   ├── server.py             # Flask API entry point
│   ├── engine.py             # simulation orchestrator
│   ├── scheduler.py          # FCFS / Weighted logic
│   ├── allocator.py          # allocation strategies
│   ├── requests_generator.py # request generation
│   ├── models.py             # data structures
│   └── utils.py              # helper functions
│
├── data/
│   ├── presets.json         # saved configurations
│
├── requirements.txt
└── README.md


import json
import os
import sys
import time as tm
from datetime import datetime, time
from typing import Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# Add project root to path so frontend1 can import backend1 modules reliably.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend1.scheduler_engine1 import (  # noqa: E402
    COLLEGES,
    DOCUMENT_COMPLEXITY,
    PRIORITY_WEIGHTS,
    COLLEGE_PRIORITY,
    COMPLETENESS_LEVELS,
    REQUESTER_PRIORITY,
    REQUESTER_PRIORITY_MAX,
    DocumentRequest,
    SimulationEngine,
    _duration_to_schedule,
)


CRITERIA_KEYS = list(PRIORITY_WEIGHTS.keys())
CRITERIA_LABELS = {
    "completeness_of_requirements": "Completeness of requirements",
    "submission_time": "Submission time",
    "document_type": "Document type",
    "requester_status": "Requester status",
    "college_affiliation": "College affiliation",
    "payment_status": "Payment status",
}


project/
│
├── app.py                  # ENTRY POINT (very small)
│
├── config/
│   └── settings.py        # constants, config, env vars
│
├── state/
│   └── session.py         # st.session_state management
│
├── services/
│   ├── api_service.py     # API calls / backend requests
│   ├── model_service.py   # ML inference / processing logic
│
├── ui/
│   ├── sidebar.py        # sidebar UI
│   ├── dashboard.py      # main dashboard UI
│   ├── results.py        # result display components
│
├── utils/
│   ├── preprocessing.py
│   ├── helpers.py
│
└── assets/ (optional)