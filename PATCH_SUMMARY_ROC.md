# Patch Summary: ROC-based Priority Weights Integration

## Overview
This document summarizes the key code changes made to integrate dynamic, ROC-based (Rank Order Centroid) priority weights into the scheduling simulation engine. These changes enable flexible, staff-driven ranking of scheduling criteria, making the system more adaptable and transparent.

---

## 1. Added `roc_utils.py`
- **Purpose:** Central utility for calculating ROC weights from a manually ranked list of criteria.
- **Key Features:**
  - `calculate_roc_weights(ranking)`: Computes ROC weights for any list of criteria.
  - `priority_criteria_ranking`: List of criteria (e.g., urgency, requester_type, etc.) ranked by importance.
  - `PRIORITY_ROC_WEIGHTS`: Dictionary of ROC weights, auto-updated from the ranking.
  - `print_priority_roc_weights()`: Prints the current ROC weights for verification.
  - Main block prints weights when run directly.

---

## 2. Refactored `scheduler_engine1.py`
- **Purpose:** Use ROC-based weights instead of hardcoded values for scheduling priority.
- **Key Changes:**
  - Imports `PRIORITY_ROC_WEIGHTS` from `roc_utils.py`.
  - Sets `PRIORITY_WEIGHTS = PRIORITY_ROC_WEIGHTS` for use throughout the engine.
  - The priority calculation logic in `DocumentRequest.calculate_priority` remains compatible with the four main criteria, but is now driven by the ROC weights.
  - The original hardcoded weights and calculation method are commented for reference.

---

## 3. Normalization Logic Explained
- Each criterion is normalized to a [0,1] scale before weighting:
  - **urgency_norm:** urgency (1-10) → 0.1–1.0
  - **requester_norm:** requester type mapped to a score (3–10) → 0.3–1.0
  - **waiting_norm:** waiting time in minutes, normalized to [0,1] based on up to 2 workdays
  - **doc_norm:** inverse of document complexity (1–4), so simpler docs get higher value
- These norms ensure fair weighting regardless of the original scale.

---

## 4. How to Adapt for Other Projects/Chats
- Place your criteria in `priority_criteria_ranking` in `roc_utils.py`.
- Use `calculate_roc_weights` to generate weights for any set of ranked criteria.
- Import and use `PRIORITY_ROC_WEIGHTS` in your main logic instead of hardcoded weights.
- The normalization logic in your scoring function should be updated to handle new criteria as needed.
- Use `print_priority_roc_weights()` for quick verification of current weights.

---

## 5. Benefits
- **Flexible:** Easily change criteria and their importance without code changes elsewhere.
- **Transparent:** Staff can see and verify how their rankings affect scheduling.
- **Reusable:** The ROC utility and integration pattern can be copied to other projects needing weighted multi-criteria decision-making.

---

## Files Changed/Added
- `backend1/roc_utils.py` (new)
- `backend1/scheduler_engine1.py` (modified)

---

## Example Usage
```python
from backend1.roc_utils import PRIORITY_ROC_WEIGHTS
# Use PRIORITY_ROC_WEIGHTS as your weights dictionary
```

---

## Next Steps
- To add new criteria, update `priority_criteria_ranking` and extend normalization logic in your scoring function.
- Remove any unused individual weight variables if not needed.


## TO DOs
- Finalize requester status and scoring, fix staffing tables, make queue list priority score adaptive to changes overtime, Finalize College scores as per group discussion. FINALIZE SCENARIOS, DO WE ADD PEAK PERIOD (GRADUATION PERIOD, ETC) AND OTHER?, CHANGE DAY COUNTING TO START FROM 1 INSTEAD FROM 0, FINALIZE QUOTA-FREE SINCE ITS NOT WORKING YET


## Done after todos
 - finalized requester types with equal scoring, added generate weights for requesters and document restrictions as per citizen's charter, fix minor frontend/table designs.


### what's new
- Added a checkbox for "peak period" which makes TOR and certification have 3x,2x more likely to be generated


### More to add
- add visual for document request spread, also disable priority score progression table when fcfs is selected as scheduler. custom request rather than generated? and the request must be inserted based on setup (time progression, when it was submitted, etc) and is highlighted to show where it would end up in the playback