# Thesis-Simulation Progress Notes

This file summarizes recent changes so work can continue in another session.

## Key Changes
- ROC criteria updated (no urgency). Criteria keys:
  - completeness_of_requirements
  - submission_time
  - document_type
  - requester_status
  - college_affiliation
  - payment_status
- Frontend weight sliders and defaults are now dynamic based on ROC keys.
- Priority scoring in scheduler uses the ROC keys above.

## Request Readiness (Requirements + Payment)
- Requests now progress over time from incomplete/unpaid to complete/paid.
- New time fields per request:
  - requirements_partial_time
  - requirements_complete_time
  - payment_time
  - ready_time
- A request becomes assignable only when current_time >= ready_time.
- The readiness delays are currently set as ranges (can be tuned):
  - REQUIREMENTS_PARTIAL_DELAY_HOURS_RANGE = (0.0, 6.0)
  - REQUIREMENTS_COMPLETE_EXTRA_DELAY_HOURS_RANGE = (2.0, 24.0)
  - PAYMENT_DELAY_HOURS_RANGE = (0.0, 48.0)

## Waiting List Behavior
- Waiting list is now filtered to show only requests still unassigned at the current playback step.
- Detailed Request Panel shows:
  - Requirements Partial/Complete time
  - Payment time
  - Ready time

## Colleges + Staff
- Colleges updated to match Criteria.md:
  - COE, CASS, CCS, CSM, CED, CHS, CEBA
- Staff count now supports 7 to 14 (2 per college). Assignment is round-robin by college.
- Staff names are unique first names (no repeats). Frontend labels show "STAFF### (Name)".

## Files Touched
- backend1/roc_utils.py
- backend1/scheduler_engine1.py
- backend1/app1.py
- frontend1/app1.py

## Known TODO / Next Steps
- Decide actual college scoring rule for college_affiliation (currently population-based helper exists).
- Decide real delay ranges for requirement/payment per document type (from citizen's charter).
- Optional: expose readiness delay ranges in frontend controls.
- Optional: include readiness timestamps in exported CSV.

## Notes
- Urgency still exists for request generation but is not part of ROC scoring.
- All requests eventually become complete/paid; no "never completes" probability yet.
