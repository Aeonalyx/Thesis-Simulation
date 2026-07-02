from backend.engine import SimulationEngine, _soft_cap, DOCUMENT_COMPLEXITY, COLLEGE_PRIORITY, REQUESTER_PRIORITY, REQUESTER_PRIORITY_MAX, COMPLETENESS_LEVELS, _duration_to_schedule


def inspect(seed=12345):
    engine = SimulationEngine(scheduler_type="WEIGHTED", allocator_type="college_based", random_seed=seed, urgency=False)
    config = engine._build_run_config({"total_requests": 60, "urgency_base": 5})
    requests = engine._generate_requests(config)
    engine.generated_requests = requests
    results = engine.run(custom_config=config)

    print("Engine priority_weights:")
    for k,v in engine.priority_weights.items():
        print(f"  {k}: {v:.6f}")

    completed = engine.completed
    print(f"Generated {len(requests)} requests, completed {len(completed)}")
    # pick first 5 completed
    for req in completed[:5]:
        print('\n----')
        print(f"Request {req.request_id} college={req.college} doc={req.document_type} urgency={req.urgency}")
        stages = [
            ("Submitted", req.submission_time),
            ("Requirements Partial", getattr(req, 'requirements_partial_time', None)),
            ("Requirements Complete", getattr(req, 'requirements_complete_time', None)),
            ("Payment", getattr(req, 'payment_time', None)),
            ("Ready", getattr(req, 'ready_time', None)),
            ("Assigned", req.assignment_time),
        ]
        for label, ts in stages:
            if ts is None:
                continue
            # compute feature scores like calculate_priority
            req.update_status(ts)
            completeness_norm = max(0.0, min(float(req.completeness_of_requirements), 1.0))
            requester_raw = REQUESTER_PRIORITY.get(req.requester_type, 3)
            requester_norm = requester_raw / max(float(REQUESTER_PRIORITY_MAX), 1.0)
            waiting_minutes = max(0.0, (ts - req.submission_time).total_seconds() / 60.0)
            submission_norm = _soft_cap(waiting_minutes, max(float(engine.workday_minutes * 2), 1.0))
            base_duration, _ = _duration_to_schedule(DOCUMENT_COMPLEXITY.get(req.document_type, 1))
            complexity_days = max(base_duration.total_seconds() / 86400.0, 1e-6)
            doc_norm = 1.0 / (1.0 + complexity_days)
            college_norm = float(COLLEGE_PRIORITY.get(req.college, 0.5))
            payment_norm = 0.0
            if isinstance(req.payment_status, str):
                status_text = req.payment_status.strip().lower()
                if status_text in {"paid", "settled", "complete", "cleared", "yes", "y", "true", "1"}:
                    payment_norm = 1.0
            else:
                payment_norm = 1.0 if bool(req.payment_status) else 0.0
            urgency_norm = float(req.urgency) / 10.0 if engine.urgency else 0.0

            scores_map = {
                "completeness_of_requirements": completeness_norm,
                "submission_time": submission_norm,
                "document_type": doc_norm,
                "requester_status": requester_norm,
                "college_affiliation": college_norm,
                "payment_status": payment_norm,
                "urgency": urgency_norm,
            }
            total_raw = 0.0
            for k,w in engine.priority_weights.items():
                if k == 'urgency' and not engine.urgency:
                    continue
                val = scores_map.get(k, 0.0)
                contrib = float(w) * float(val)
                total_raw += contrib
            final = _soft_cap(total_raw, 0.15)
            print(f"{label:20s} | score_pre={total_raw:.6f} score_post={final:.6f}")


if __name__=='__main__':
    inspect(12345)
