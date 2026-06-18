# FULL REFACTOR PROMPT — MIGRATE EXISTING THESIS SIMULATION TO CONTINUOUS API-DRIVEN ARCHITECTURE

You are a senior Python software architect and thesis systems engineer.

Your task is to completely refactor my EXISTING thesis simulation project into a continuous API-driven architecture while preserving all existing simulation logic, scheduling behavior, allocator behavior, metrics calculations, visualizations, presets, and thesis functionality.

IMPORTANT:

This is NOT a greenfield project.

Do NOT create a new simulation.

Do NOT replace existing scheduling algorithms.

Do NOT simplify the thesis logic.

Instead, analyze the existing codebase and evolve it into a production-style architecture.

---

# EXISTING PROJECT STRUCTURE

The project already contains:

```text
backend2/
    config.py
    engine.py
    models.py
    roc_utils.py
    rules.py
frontend2/
    components/
        charts.py
        config.py
        context.py
        simulation.py
        state.py
    ui/
        metrics.py
        playback.py
        results.py
        sidebar.py
        theme.py
app.py (outside the folders for the streamlit to run)
```

Both folders already contain working code.

You must inspect the existing files before making changes.

Assume that the current system already supports:

* FCFS scheduling
* Weighted Priority scheduling
* ROC weighting system
* Staff allocation strategies
* Event logging
* Metrics calculation
* Presets
* Scenario generation
* Streamlit visualizations
* Automated request generation
* Manual configuration options

````

---

# PRIMARY OBJECTIVE

Convert the existing batch simulation into a continuous real-time simulation where:

1. Requests are submitted through FastAPI endpoints.
2. Requests are captured while the simulation is actively running.
3. The engine continuously processes incoming requests.
4. Metrics update live.
5. Streamlit displays live results.
6. Historical requests are stored.
7. Simulation state survives restart.
8. Historical requests can be replayed for comparison experiments.

The existing thesis logic must remain intact.

---

# REQUIRED ARCHITECTURE

## Backend

Refactor backend2 into:

```text
backend2/
│
├── config.py
├── rules.py
├── models.py
├── engine.py
├── roc_utils.py
│
├── api.py
├── database.py
├── queue_manager.py
├── simulation_clock.py
├── traffic_generator.py
└── schemas.py
````

Preserve existing files whenever possible.

Only extend them.

---

# BACKEND REQUIREMENTS

## database.py

Implement SQLite + SQLAlchemy.

Persist:

* requests
* completed requests
* event logs
* metrics snapshots
* simulation runs
* replay datasets

Required capabilities:

* save incoming requests
* update request status
* resume after restart
* export data
* replay historical requests

---

## simulation_clock.py

Create an independent simulation clock.

Requirements:

```python
tick()
pause()
resume()
reset()
is_office_hours()
is_working_day()
```

Clock must advance independently from real-world time.

Configurable tick rate:

```text
1 second = 1 simulation minute
```

by default.

---

## queue_manager.py

Create thread-safe request handling.

Responsibilities:

```python
enqueue_request()
dequeue_request()
peek_queue()
clear_queue()
queue_length()
```

This queue acts as the bridge between:

```text
FastAPI
↓
Queue
↓
Simulation Engine
```

---

## engine.py

DO NOT rewrite scheduling logic.

Reuse existing:

* FCFS logic
* Weighted logic
* Allocator logic
* Priority logic
* Metrics logic

Refactor engine to support:

```python
run_continuous()
run_replay()
submit_request()
pause()
resume()
reset()
get_live_metrics()
```

The simulation must process requests continuously.

Pseudo-flow:

```text
while simulation_running:

    tick_clock()

    pull_new_requests_from_queue()

    process_scheduler()

    process_allocator()

    update_request_status()

    update_metrics()

    persist_changes()

    sleep()
```

Existing functionality must remain available.

---

## traffic_generator.py

Move request generation out of engine.py.

Reuse existing request generation code.

Support:

* baseline
* peak period
* workload imbalance
* urgency scenarios
* custom traffic scenarios

Generator should submit requests through the same API used by manual users.

---

## api.py

Build FastAPI endpoints.

Required endpoints:

### Request Submission

```text
POST /request
POST /request/bulk
```

Accept requests while simulation is running.

Immediately:

1. validate
2. store in database
3. push into queue

---

### Simulation Control

```text
POST /simulation/start
POST /simulation/pause
POST /simulation/resume
POST /simulation/reset
```

---

### Metrics

```text
GET /metrics
```

Return:

```json
{
  "queue_length": 0,
  "throughput": 0,
  "avg_waiting_time": 0,
  "avg_turnaround_time": 0,
  "staff_utilization": 0,
  "processed_requests": 0,
  "pending_requests": 0
}
```

---

### Replay and Comparison

```text
POST /simulation/compare
```

Must:

1. Load historical requests.
2. Replay identical requests.
3. Compare schedulers.
4. Compare allocators.
5. Return comparison metrics.

---

### Export

```text
GET /export/csv
GET /export/events
GET /export/metrics
```

---

# FRONTEND REQUIREMENTS

Analyze the entire frontend2 folder.

Remove direct coupling to backend simulation classes.

The frontend must become a pure API client.

Replace any code that does:

```python
SimulationEngine(...)
```

with:

```python
requests.get(...)
requests.post(...)
```

calls to FastAPI.

---

# REQUIRED FRONTEND FEATURES

## Live Dashboard

Display:

* queue length
* throughput
* waiting time
* turnaround time
* staff utilization
* active staff
* processed requests

Update automatically.

Use polling.

No WebSockets.

Polling interval:

```python
2 seconds
```

---

## Manual Request Submission

Create a form.

Fields:

* requester type
* college
* document type
* urgency
* requirements completeness

Submit through:

```text
POST /request
```

---

## Bulk Request Submission

Create a tool that can submit:

```text
2–20 requests simultaneously
```

through:

```text
POST /request/bulk
```

This is required for thesis defense demonstrations.

---

## Simulation Controls

Buttons:

```text
Start
Pause
Resume
Reset
```

connected to FastAPI endpoints.

---

## Replay Comparison Screen

Allow users to compare:

```text
FCFS vs Weighted
College vs Pooled
Quota vs Workload
```

through:

```text
POST /simulation/compare
```

and visualize results.

---

## Export Screen

Allow downloading:

```text
CSV
Metrics
Events
```

from backend endpoints.

---

# PRESERVE EXISTING FEATURES

Do NOT remove:

* presets
* seeds
* chart visualizations
* allocator settings
* scheduler settings
* scenario settings
* thesis metrics
* event logs
* ROC weighting
* request eligibility rules
* document complexity rules
* college priority rules

These are core thesis features.

---

# DATABASE RECOVERY REQUIREMENT

The system must support:

1. Start simulation.
2. Submit requests.
3. Stop FastAPI unexpectedly.
4. Restart FastAPI.
5. Resume processing pending requests automatically.

This is a required thesis demonstration feature.

---

# IMPLEMENTATION STRATEGY

Perform the refactor incrementally.

Phase 1:

* database.py
* queue_manager.py
* simulation_clock.py

Phase 2:

* engine.py continuous mode

Phase 3:

* api.py

Phase 4:

* frontend2 API integration

Phase 5:

* replay system

Phase 6:

* recovery system

Phase 7:

* export system

---

# OUTPUT REQUIREMENTS

Before modifying code:

1. Analyze backend2 structure.
2. Analyze frontend2 structure.
3. Identify all affected files.
4. Produce a migration plan.
5. Show file-by-file changes.

Then implement changes incrementally.

Never replace thesis logic unless absolutely necessary.

Always reuse existing logic when possible.

The final result must be a fully functional continuous API-driven thesis simulation where backend2 runs the simulation engine and frontend2 operates entirely through FastAPI.
