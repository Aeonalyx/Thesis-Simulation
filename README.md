# Thesis-Simulation System

A simulation-based document request processing system that models and evaluates different scheduling strategies, allocator policies, and workload scenarios using ROC-based priority weighting.

---

## 📌 Overview

This system simulates how document requests (e.g., TOR, certificates, etc.) are processed in an institutional setting. It evaluates different scheduling algorithms and staff allocation strategies under varying workload conditions.

It supports:
- FCFS and Weighted Priority Scheduling
- Multiple allocator strategies
- Scenario-based simulation (normal, peak, etc.)
- ROC-based dynamic priority weighting
- Realistic time progression and queue behavior

---

## ⚙️ Core Concept

Each request is processed using:

- **Scheduler** → decides *which request is next*
- **Allocator** → decides *which staff handles it*
- **Scenario Engine** → controls request generation behavior
- **ROC Weighting System** → defines priority importance

---

## 🧠 Request Characteristics (ROC Criteria)

Priority is based on ranked criteria:

1. Completeness of requirements  
2. Submission time  
3. Document type  
4. Requester status (student/alumni)  
5. College affiliation  
6. Payment status  
7. Urgency (optional / low priority factor)

---

## 🏫 Colleges

- COE  
- CASS  
- CCS  
- CSM  
- CED  
- CHS  
- CEBA  

Each college has assigned staff members (1–2 per college depending on configuration).

---

## 📊 Scenarios

### Normal Period
- ~100 requests/day

### Peak Period (Graduation)
- ~300 requests/day
- Increased probability for:
  - TOR
  - Certificates

### System Behavior
- Requests evolve over time (requirements → payment → ready state)
- Queue dynamically updates as time progresses

---

## ⏱ Request Lifecycle

Each request transitions through:

- Requirements incomplete → partial → complete  
- Payment pending → completed  
- Ready for assignment

### Timing Fields
- `requirements_partial_time`
- `requirements_complete_time`
- `payment_time`
- `ready_time`

A request becomes **assignable only when:**

```text```
current_time ≥ ready_time

## ROC-Based Priority System

Weights are dynamically generated using Rank Order Centroid (ROC):

priority_score =
(w1 × urgency_norm) +
(w2 × requester_norm) +
(w3 × waiting_norm) +
(w4 × document_norm) +
(...)

### Key Properties

- Fully configurable ranking system
- No hardcoded weights
- Easily extendable criteria list
- Transparent scoring model

## 🔄 Scheduling Algorithms

1. FCFS (Baseline)
- Oldest request first
- College-based assignment
- Respects quota + working hours

2. Weighted Priority Scheduler
- Dynamic priority scoring
- Event-driven re-evaluation
- Always selects highest scoring request

## 🏢 Allocator Strategies

College-Based
- Same college only
- Enforces academic separation

Workload-Based
- Chooses least loaded staff

Pooled
- Ignores college boundaries
- Global staff pool selection

Quota-Free
- No daily limits
- Still respects working hours

## ⏰ Working Hours Model
- 8:00 AM – 5:00 PM only
- Requests spanning beyond 5:00 PM roll over to next day
- Queue time includes overnight delays

## 📈 Metrics Output

The system evaluates:
- Total processed requests
- Average waiting time
- Turnaround time
- Throughput per day
- Staff load distribution
- Queue length behavior

## 🧪 Simulation Features

Core Controls
- Run / Reset simulation
- Scenario selection
- Scheduler & allocator selection
- Random seed for reproducibility

Weighted Controls
- ROC-based weight configuration
- Real-time priority visualization

Comparison Tools
- Side-by-side scheduler comparison
- Delta metrics (vs baseline)


Download requirements.txt