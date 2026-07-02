# Thesis-Simulation Progress Notes

This file summarizes the current refactored structure and main behavior.

## Main Files

- `backend/api.py` - Flask API entrypoint and custom request endpoints.
- `backend/engine.py` - simulation engine, schedulers, allocator logic, request lifecycle.
- `backend/criteria.py` - built-in/custom priority criteria catalog and scoring.
- `backend/request_fields.py` - configurable generated request fields and option scores.
- `backend/roc.py` - ROC weight calculation and default ranking.
- `backend/data/` - local JSON/SQLite runtime data.
- `frontend/app.py` - Streamlit UI.
- `frontend/saved_presets.json` - saved UI presets.

## Current Priority Model

- Requirements completeness and payment status are gate checks.
- Weighted criteria are configurable through the UI.
- ROC ranking and manual weight modes are supported.
- Custom request fields define normalized option scores from `0.00` to `1.00`.
- Custom criteria simply link a custom request field into the weighted scheduler.

## Request Readiness

- Requests can progress from incomplete/unpaid to complete/paid.
- A request becomes assignable only when `current_time >= ready_time`.
- Ready-but-unassigned requests appear in the pending queue.
- Not-ready arrived requests appear in the unassignable waiting list.

## Run Commands

```powershell
python backend/api.py
streamlit run frontend/app.py
```
