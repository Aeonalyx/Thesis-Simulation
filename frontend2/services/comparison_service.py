import pandas as pd

from backend1.scheduler_engine1 import SimulationEngine


def run_comparison(
    schedulers,
    allocators,
    seed,
    staff_config,
    priority_weights_fn,
    custom_config,
    st_state,
):
    compare_rows = []

    for scheduler in schedulers:
        for allocator in allocators:

            engine = SimulationEngine(
                scheduler_type=scheduler,
                allocator_type=allocator,
                staff_config=staff_config,
                priority_weights=priority_weights_fn(),
                random_seed=seed,
                work_start=st_state.work_start_time.strftime("%H:%M"),
                work_end=st_state.work_end_time.strftime("%H:%M"),
            )

            result = engine.run(custom_config=custom_config)

            compare_rows.append({
                "scheduler": scheduler,
                "allocator": allocator,
                "total_processed": result.get("total_processed", 0),
                "avg_waiting_time_hours": result.get("avg_waiting_time_hours", 0.0),
                "avg_turnaround_days": result.get("avg_turnaround_days", 0.0),
                "total_days_elapsed": result.get("total_days_elapsed", 0.0),
                "throughput_req_per_day": result.get("throughput_req_per_day", 0.0),
            })

    df = pd.DataFrame(compare_rows)

    baseline = df[
        (df["scheduler"] == "FCFS") &
        (df["allocator"] == "college_based")
    ]

    baseline_row = baseline.iloc[0] if not baseline.empty else df.iloc[0]

    df["delta_wait_vs_baseline"] = (
        df["avg_waiting_time_hours"] - baseline_row["avg_waiting_time_hours"]
    ).round(2)

    df["delta_throughput_vs_baseline"] = (
        df["throughput_req_per_day"] - baseline_row["throughput_req_per_day"]
    ).round(2)

    df["delta_turnaround_vs_baseline"] = (
        df["avg_turnaround_days"] - baseline_row["avg_turnaround_days"]
    ).round(2)

    return df