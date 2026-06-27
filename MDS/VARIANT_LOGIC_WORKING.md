# FCFS + College-Based (Baseline)

## Needed Criteria

### Request
- request_id
- submission_time
- college
- document_type
- etc (i.e. completeness_of_requirements)

### Staff
- staff_id
- college_affiliation
- quota_limit
- is_available

## Logic
1. Sort requests by submission_time (oldest first).
2. Assign each request only to same-college staff.
3. Enforce daily quota_limit per staff.
4. If quota is full, assign on next available day.
5. completion_time = assignment_time + processing_duration.

## Pseudocode (Baseline)
1. requests = generate_requests(scenario)
2. sorted_requests = sort_by_submission_time(requests)
3. for each request in sorted_requests:
- staff = find_same_college_staff(request.college)
- if staff missing: waiting_queue.add(request); continue
- day = first_day_with_quota(staff, request.submission_time)
- assignment_time = compute_assignment_time(day, request.submission_time)
- processing_duration = get_processing_duration(request.document_type)
- completion_time = assignment_time + processing_duration
- save_assignment_and_completion(request, staff, assignment_time, completion_time)
4. metrics = calculate_metrics(completed)
5. return metrics

## Outputs
- total_processed
- avg_waiting_time_hours
- avg_turnaround_days
- total_days_elapsed
- throughput_req_per_day
- staff_load

throughput_req_per_day = total_processed / max(total_days_elapsed, 1)

## Working Hours Rollover (8:00 AM to 5:00 PM)

- Yes, this is doable and should be part of the model.
- If staff reaches 5:00 PM and cannot start the next request, that request starts next working day at 8:00 AM.
- The queue wait includes overnight non-working hours.
- So requests left after day-1 cutoff will show larger waiting time.

Example:
- submitted at 4:50 PM, starts at 8:00 AM next day
- queue wait includes 15 hours and 10 minutes (plus any prior queue delay)

## FCFS + Workload-Based

### Logic
1. Sort requests by submission_time (oldest first).
2. Try same-college staff first.
3. From same-college candidates, pick least-loaded staff (relevant only if there are multiple staff for that college).
4. If the same-college staff has already reached quota for that day, do same-day cross-college fallback before pushing to next day.
5. Submission hour matters: try to place the request on the same day and same time window if other staff still have slots.
6. If no same-day fallback slot exists, move to next available day.

### Pseudocode
1. sorted_requests = sort_by_submission_time(requests)
2. for each request in sorted_requests:
- same_college = same_college_staff(request.college)
- if same_college has free quota at request.submission_time day: assign to same_college
- else:
- fallback = any_other_staff_with_same_day_free_quota(request.submission_time)
- if fallback exists: assign to least_loaded(fallback)
- else: move_to_next_available_day(request)
- compute completion_time

## FCFS + Pooled

### Logic
1. Sort requests by submission_time (oldest first).
2. Ignore college boundaries during assignment.
3. Choose from all available staff under quota.
4. Pick staff with earliest next_available_time.
5. If none available, queue or move to next available slot.

### Pseudocode
1. sorted_requests = sort_by_submission_time(requests)
2. for each request in sorted_requests:
- pool = all_staff_available_under_quota()
- if pool empty: queue_or_move_to_next_available_day(request); continue
- staff = min(pool, key=next_available_time)
- assign_and_compute_completion(request, staff)

## FCFS + Quota-Free

### Logic
1. Sort requests by submission_time (oldest first).
2. Keep college-based assignment (same-college staff only).
3. Ignore quota_limit checks, but still respect staff availability and working hours.
4. If there is only one staff per college, all requests for that college line up under that one staff.
5. Staff works 8:00 AM to 5:00 PM only.
6. If the next request cannot start before 5:00 PM, it rolls to next day 8:00 AM.
7. Queue wait is based on when staff becomes available (not zero by default).
8. If no same-college staff exists, keep request in waiting_queue.

### Easy Process
1. Request arrives.
2. Find same-college staff.
3. Put request behind that staff's current workload.
4. Start when staff is free during working hours.
5. If day ends, continue next day at 8:00 AM.
6. Complete after processing time is consumed.

### Pseudocode
1. sorted_requests = sort_by_submission_time(requests)
2. for each request in sorted_requests:
- if no same-college staff exists: waiting_queue.add(request); continue
- staff = assigned_same_college_staff(request.college)
- assignment_time = next_working_start(max(request.submission_time, staff.next_available_time))
- assign_without_quota_check(request, staff, assignment_time)
- completion_time = add_processing_with_working_hours(assignment_time, processing_duration)
- staff.next_available_time = completion_time

## Weighted Priority Scheduler (Shared)

### Priority Criteria
- urgency
- requester_type priority
- waiting_time
- document_type factor
- and others

### Priority Formula
priority_score =
(w1 * urgency_norm) +
(w2 * requester_norm) +
(w3 * waiting_norm) +
(w4 * document_norm) +
(wN * other_criteria)

### Scheduler Logic
1. Before each assignment decision, compute/update priority_score for waiting requests.
2. Pick highest priority_score first.
3. If tie, use earlier submission_time.
4. Reordering is repeated every time a staff is ready for a next request (event-driven loop).

### Event-Driven Queueing (Applies to ALL Weighted Variants)
1. Request arrives and enters pending queue.
2. If a staff becomes available, recompute scores for pending requests.
3. Pick highest-score request at that moment.
4. Assign it using the selected allocator rules.
5. When staff finishes, repeat the same steps.
6. Because waiting_time changes over time, ordering is dynamic and can change at each cycle.

### Scheduler Pseudocode
1. while pending requests exist:
- wait for next event (request arrival OR staff available)
- recompute priority_score for pending requests using event_time
- request = max(pending_requests, key=(priority_score, -submission_time))
- pass request to selected allocator

## Weighted + College-Based

### Logic
1. Scheduler picks highest-priority request first.
2. Assign only to same-college staff.
3. Enforce quota_limit and working hours.
4. If same-college quota is full, move request to next available day/time.

### Pseudocode
1. while pending requests exist:
- req = highest_priority_request(pending, current_time)
- staff = same_college_staff(req.college)
- if no staff: waiting_queue.add(req); remove req from pending; continue
- assignment_time = first_same_college_slot_with_quota_and_workhours(staff, req.submission_time)
- completion_time = add_processing_with_working_hours(assignment_time, processing_duration(req))
- save req assignment/completion; update staff availability

## Weighted + Workload-Based

### Logic
1. Scheduler picks highest-priority request first.
2. Try same-college staff first.
3. If same-college daily quota is full, try same-day cross-college fallback.
4. If no same-day fallback is available, move to next available day/time.

### Pseudocode
1. while pending requests exist:
- req = highest_priority_request(pending, current_time)
- if same_college_has_slot(req.college, req.submission_time): staff = least_loaded_same_college(req.college)
- else: staff = least_loaded_same_day_fallback(req.submission_time)
- if no staff: assignment_time = next_available_day_time(req)
- else: assignment_time = next_working_start(max(req.submission_time, staff.next_available_time))
- completion_time = add_processing_with_working_hours(assignment_time, processing_duration(req))
- save req assignment/completion; update staff availability

## Weighted + Pooled

### Logic
1. Scheduler picks highest-priority request first.
2. Ignore college boundaries for assignment.
3. Choose available staff under quota and within work hours.
4. Prefer earliest next_available_time.

### Pseudocode
1. while pending requests exist:
- req = highest_priority_request(pending, current_time)
- pool = all_staff_with_quota_and_workhours()
- if pool empty: assignment_time = next_available_day_time(req)
- else: staff = min(pool, key=next_available_time)
- assignment_time = next_working_start(max(req.submission_time, staff.next_available_time))
- completion_time = add_processing_with_working_hours(assignment_time, processing_duration(req))
- save req assignment/completion; update staff availability

## Weighted + Quota-Free

### Logic
1. Scheduler picks highest-priority request first.
2. Keep same-college assignment.
3. No quota_limit check, but still enforce staff availability and 8:00 AM to 5:00 PM work hours.
4. If day ends, request rolls to next day 8:00 AM.

### Pseudocode
1. while pending requests exist:
- req = highest_priority_request(pending, current_time)
- if no same-college staff: waiting_queue.add(req); remove req from pending; continue
- staff = assigned_same_college_staff(req.college)
- assignment_time = next_working_start(max(req.submission_time, staff.next_available_time))
- completion_time = add_processing_with_working_hours(assignment_time, processing_duration(req))
- save req assignment/completion; update staff availability

## Frontend Interactive Tools Needed

### A. Core Run Controls (Must Have)
1. Run Simulation button: executes the selected scheduler + allocator + scenario.
2. Reset/Clear button: clears current run results and visual state.
3. Random seed input: makes runs reproducible for fair comparison.

### B. Variant Selection Controls (Must Have)
1. Scheduler selector: FCFS or WEIGHTED.
2. Allocator selector: college_based, workload_based, pooled, quota_free.
3. Scenario selector: baseline, peak_urgency, workload_imbalance, staff_absence.

### C. Capacity and Policy Controls (Must Have)
1. Number of staff slider/input.
2. Daily quota slider/input (for quota-based variants).
3. Working hours config (start/end time, default 8:00 AM to 5:00 PM).

### D. Weighted Scheduler Controls (Must Have for WEIGHTED)
1. Weight sliders for urgency, requester_type, waiting_time, document_type.
2. Tie-break rule display (earlier submission_time when score ties).
3. Optional live display of current top-priority pending requests.

### E. Metrics and Results Display (Must Have)
1. KPI cards: total_processed, avg_waiting_time_hours, avg_turnaround_days, total_days_elapsed, throughput_req_per_day.
2. Staff load chart.
3. Waiting queue count and list.
4. Assignment timeline chart.

### F. Request Inspection Tools (Must Have)
1. Filter by college.
2. Filter by document type.
3. Sort by queue wait, turnaround, submission time, or assigned day.
4. Detailed request panel (submission, assignment, completion, assigned staff, waits).

### G. Comparison Tools (Highly Recommended)
1. Compare variants action: run same scenario across selected allocators/schedulers.
2. Side-by-side metrics table.
3. Delta highlights (for example throughput change vs baseline).

### H. Playback Tools (For Future Step-by-Step Mode)
1. Play/Pause button.
2. Step forward/backward.
3. Speed control (slow, normal, fast).
4. Current simulation clock display.
5. Event log view (arrival, queue, reprioritize, assign, complete, rollover).

### I. Export and Reproducibility Tools (Must Have)
1. Export run results to CSV.
2. Export run config + weights to JSON.
3. Save/load preset configurations.
