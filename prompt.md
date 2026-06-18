# ARCHITECTURAL CONSTRAINTS

The purpose of this refactor is to evolve the existing thesis simulation into a continuous API-driven architecture while preserving all existing simulation functionality, scheduling behavior, allocator behavior, metrics calculations, visualizations, presets, scenarios, and comparison workflows.

This is an infrastructure refactor, not a simulation rewrite.

The existing simulation logic must remain behaviorally equivalent after migration.

---

## Existing System Preservation

This is NOT a greenfield project.

Before making changes:

1. Analyze the entire backend2 structure.
2. Analyze the entire frontend2 structure.
3. Identify all affected files.
4. Produce a migration plan.
5. Produce file-by-file modifications.
6. Reuse existing code whenever possible.

Preserve:

* FCFS scheduling
* Weighted Priority scheduling
* ROC weighting
* Staff allocation strategies
* Request eligibility rules
* Document complexity rules
* College priority rules
* Scenario generation
* Presets
* Seeds
* Metrics calculations
* Event logging
* Streamlit visualizations
* Existing comparisons
* Existing simulation outputs

Scheduling, allocation, weighting, and metrics logic should be extended rather than rewritten.

---

## Backward Compatibility Requirement

Any workflow that currently works must continue to work after the refactor.

Examples include:

* preset execution
* scenario execution
* simulation execution
* comparison workflows
* metrics generation
* visualization workflows
* result generation

The API architecture is an infrastructure upgrade, not a replacement for existing simulation functionality.

---

## Architectural Boundary Requirement

Maintain clear separation of concerns.

The frontend must never import simulation logic.

The FastAPI layer must never import Streamlit components.

The simulation engine must not depend on FastAPI.

The engine should remain executable independently of the API layer.

Dependencies should flow only in this direction:

Streamlit
↓
FastAPI
↓
Application Services
↓
Simulation Engine
↓
Database

Avoid circular dependencies.

Avoid placing business logic inside API endpoints.

Avoid placing simulation logic inside Streamlit code.

---

## Simulation State Management

Simulation state must be explicit and centrally managed.

Supported states:

* STOPPED
* RUNNING
* PAUSED
* REPLAYING
* RESETTING

Invalid transitions must be rejected.

The simulation state should survive application restart whenever possible.

---

## Continuous Simulation Behavior

The simulation must support continuous execution.

Requests may arrive while the simulation is already running.

Request sources include:

* automated traffic generation
* manual request submission
* bulk request submission
* historical replay datasets

All requests must pass through the same architecture:

Request Source
↓
FastAPI
↓
Queue Manager
↓
Simulation Engine

No request source should bypass the queue.

No request source should inject directly into the engine.

---

## Automated Traffic Generation

Generated requests must use the same submission pathway as manual requests.

Preferred flow:

Traffic Generator
↓
POST /request
↓
API
↓
Queue
↓
Simulation Engine

The existing request-generation logic must be preserved.

Preserve:

* requester distributions
* college distributions
* urgency distributions
* eligibility rules
* complexity rules
* scenario definitions

---

## Manual Request Submission During Execution

The system must support manual submissions while generated traffic is already being processed.

Example:

100 generated requests

Simulation Running

User submits 5 additional requests

The simulation should immediately accept those requests without requiring restart or regeneration.

---

## Concurrent Request Demonstration

The system must support multiple requests sharing the same simulated arrival timestamp.

Example:

Submit 5 requests simultaneously

All requests receive:

10:30:00 AM

The active scheduler determines processing order.

This capability is required for demonstrating:

* FCFS
* Weighted Priority

under identical arrival conditions.

---

## Mixed Traffic Scenarios

The architecture must support:

Generated Requests
+
Manual Requests
+
Bulk Requests

within the same simulation run.

Example:

100 generated requests

*

5 manual requests

=
105 total requests

Manual requests should be treated as new arrivals rather than replacing generated traffic.

---

## Simulation Clock Requirements

The simulation clock must be independent of wall-clock time.

Support:

* tick()
* pause()
* resume()
* reset()

Support configurable acceleration rates.

Examples:

* 1 second = 1 simulation minute
* 1 second = 15 simulation minutes
* 1 second = 30 simulation minutes
* 1 second = 1 simulation hour

The selected speed should be configurable through the frontend.

---

## Office Hour Constraints

The simulation must preserve office-hour behavior.

Example:

Monday–Friday

8:00 AM – 5:00 PM

Requests may arrive outside office hours.

Processing should occur only during valid working periods.

Example:

Friday 4:55 PM

Request arrives

Processing continues until:

Friday 5:00 PM

Remaining work is paused.

Processing automatically resumes on:

Monday 8:00 AM

The simulation clock should automatically advance through:

* nights
* weekends
* non-working periods

without wasting execution time.

---

## Demonstration Mode

Used for thesis defense.

Requirements:

* live dashboard
* queue visualization
* continuous execution
* manual submissions
* bulk submissions
* concurrent submissions
* configurable simulation speed
* live metrics
* export capability

---

## Research Mode

Used for simulation analysis and comparisons.

Requirements:

* maximum execution speed
* no real-time waiting
* replay support
* scheduler comparison
* allocator comparison
* rapid metrics generation
* reproducible execution

Both modes must use identical simulation logic.

Only execution strategy may differ.

---

## Replay Accuracy Requirement

Historical replay must preserve:

* arrival timestamps
* requester types
* colleges
* document types
* priorities
* urgency values
* eligibility attributes
* complexity attributes

Replay executions should produce behavior equivalent to the original dataset when using the same scheduler and allocator settings.

---

## Frontend Migration Requirements

The frontend is implemented in Streamlit.

The objective is to migrate from direct engine execution to API consumption.

The objective is NOT to redesign the frontend.

Before making frontend modifications:

1. Analyze all Streamlit ui.
2. Analyze all components.
3. Identify direct SimulationEngine dependencies.
4. Replace those dependencies with API communication.

Preserve existing:

* dashboards
* charts
* tables
* metrics cards
* result ui
* comparison ui
* presets
* configuration panels
* workflows
* visualizations

The preferred migration strategy is:

Existing UI
↓
API Adapter
↓
FastAPI

rather than rebuilding ui from scratch.

---

## UI Preservation Requirement

The frontend appearance should remain substantially unchanged.

A user familiar with the current interface should still recognize:

* ui structure
* navigation
* controls
* charts
* tables
* result screens
* comparison views

after migration.

Migration priority:

1. Reuse ui.
2. Reuse component.
3. Reuse chart.
4. Reuse table.
5. Reuse metric card.
6. Replace data source.
7. Redesign only when unavoidable.

---

## Live Dashboard Integration

The Streamlit frontend should function as a pure API client.

Live updates should use periodic polling.

WebSockets are not required.

Recommended polling interval:

2 seconds

Existing dashboard components should remain whenever possible.

Replace only the data source.

Example:

Before:

Chart
↓
Local Simulation Data

After:

Chart
↓
FastAPI Metrics Endpoint

---

## Fault Recovery Requirement

The system must support recovery after unexpected interruption.

Required demonstration scenario:

1. Start simulation.
2. Submit requests.
3. Stop FastAPI unexpectedly.
4. Restart FastAPI.
5. Resume pending requests automatically.

The following must persist:

* pending requests
* completed requests
* event logs
* metrics snapshots
* simulation state
* replay datasets

SQLite persistence must support automatic recovery and resumption.
