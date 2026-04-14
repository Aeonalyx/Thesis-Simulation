from backend1.scheduler_engine1 import *
import random

# Run simulation
engine = SimulationEngine(
    scheduler_type="FCFS",
    allocator_type="college_based",
    staff_config={"num_staff": 6, "quota_limit": 20}
)

results = engine.run(scenario="baseline")

# Filter for IE requests only
ie_requests = [r for r in engine.completed if r.college == "IE"]

print("\n" + "="*120)
print("IE COLLEGE - DETAILED REQUEST ANALYSIS")
print("="*120)

print(f"\nTotal IE Requests: {len(ie_requests)}\n")

# Show FIRST 5 IE requests
print("\n" + "-"*120)
print("FIRST 5 IE REQUESTS:")
print("-"*120)
print(f"{'#':<3} {'Request ID':<12} {'Document Type':<30} {'Urgency':<8} {'Requester':<20} {'Queue Wait':<12} {'Assign Day':<11} {'Process':<8}")
print("-"*120)

for i, req in enumerate(ie_requests[:5], 1):
    queue_wait_hours = (req.assignment_time - req.submission_time).total_seconds() / 3600
    assignment_day = int((req.assignment_time - engine.start_time).total_seconds() / 86400)
    base_days = DOCUMENT_COMPLEXITY[req.document_type]
    process_days = (req.completion_time - req.assignment_time).total_seconds() / 86400
    
    print(f"{i:<3} {req.request_id:<12} {req.document_type:<30} {req.urgency:<8} {req.requester_type:<20} {queue_wait_hours:>10.1f}h {assignment_day:>10}d {process_days:>7.1f}d")

# Show LAST 5 IE requests
print("\n" + "-"*120)
print("LAST 5 IE REQUESTS:")
print("-"*120)
print(f"{'#':<3} {'Request ID':<12} {'Document Type':<30} {'Urgency':<8} {'Requester':<20} {'Queue Wait':<12} {'Assign Day':<11} {'Process':<8}")
print("-"*120)

for i, req in enumerate(ie_requests[-5:], len(ie_requests)-4):
    queue_wait_hours = (req.assignment_time - req.submission_time).total_seconds() / 3600
    assignment_day = int((req.assignment_time - engine.start_time).total_seconds() / 86400)
    base_days = DOCUMENT_COMPLEXITY[req.document_type]
    process_days = (req.completion_time - req.assignment_time).total_seconds() / 86400
    
    print(f"{i:<3} {req.request_id:<12} {req.document_type:<30} {req.urgency:<8} {req.requester_type:<20} {queue_wait_hours:>10.1f}h {assignment_day:>10}d {process_days:>7.1f}d")

# Summary statistics
print("\n" + "-"*120)
print("IE QUEUE WAIT ANALYSIS:")
print("-"*120)

queue_waits = [(r.assignment_time - r.submission_time).total_seconds() / 3600 for r in ie_requests]
print(f"Min Queue Wait: {min(queue_waits):.1f} hours")
print(f"Max Queue Wait: {max(queue_waits):.1f} hours")
print(f"Avg Queue Wait: {sum(queue_waits)/len(queue_waits):.1f} hours")

print("\n")
