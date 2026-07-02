# Thesis Simulation

Registrar document-request scheduling simulation with FCFS and weighted-priority routing.

## Main Structure

- `backend/api.py` - Flask API entrypoint.
- `backend/engine.py` - simulation engine, schedulers, allocators, and request lifecycle.
- `backend/criteria.py` - built-in/custom priority criteria scoring.
- `backend/request_fields.py` - configurable request fields for generation and scoring.
- `backend/roc.py` - ROC weight calculation and default criteria ranking.
- `backend/data/` - local JSON/SQLite runtime data.
- `frontend/app.py` - Streamlit UI.
- `frontend/saved_presets.json` - saved UI presets.

## Run

Install dependencies:

```powershell
pip install -r requirements.txt
```

Start both backend and frontend:

```powershell
python run_app.py
```

Or start them separately.

Start the backend:

```powershell
python backend/api.py
```

Start the frontend in another terminal:

```powershell
streamlit run frontend/app.py
```
