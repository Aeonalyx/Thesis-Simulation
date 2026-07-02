"""
ROC weighting utilities.
Utility functions for calculating Rank Order Centroid (ROC) weights from staff rankings.
"""

def calculate_roc_weights(ranking):
    """
    Calculate ROC weights given a ranking list.

    Args:
        ranking (list): Criteria ranked from highest to lowest priority.

    Returns:
        dict: Mapping of criterion to its ROC weight.
    """
    n = len(ranking)
    return {
        criterion: sum(1 / (j + 1) for j in range(i, n)) / n
        for i, criterion in enumerate(ranking)
    }


# --- MANUAL RANKING FROM STAFF INTERVIEW ---
# Requirements completeness and payment status are readiness gates, not scored
# criteria. A request must satisfy those gates before it can be assigned.
GATE_CHECK_CRITERIA = [
    "completeness_of_requirements",
    "payment_status",
]

priority_criteria_ranking = [
    "document_type",
    "submission_time",
    "requester_status",
    "college_affiliation",
    # Note: `urgency` is optional. The base ROC weights (used by default)
    # consider only the criteria above. When urgency is enabled in the
    # simulation, include it as an additional criterion below.
]

# Compute weights
PRIORITY_ROC_WEIGHTS_BASE = calculate_roc_weights(priority_criteria_ranking)

# Full ranking including urgency (used when urgency is enabled)
priority_criteria_ranking_full = priority_criteria_ranking + ["urgency"]
PRIORITY_ROC_WEIGHTS_FULL = calculate_roc_weights(priority_criteria_ranking_full)

# Public default: base weighted criteria unless callers opt into urgency.
PRIORITY_ROC_WEIGHTS = PRIORITY_ROC_WEIGHTS_BASE

# Optional: expose individual weights (for direct import use)
submission_time_weight = PRIORITY_ROC_WEIGHTS["submission_time"]
document_type_weight = PRIORITY_ROC_WEIGHTS["document_type"]
requester_status_weight = PRIORITY_ROC_WEIGHTS["requester_status"]
college_affiliation_weight = PRIORITY_ROC_WEIGHTS["college_affiliation"]

def print_priority_roc_weights(include_urgency: bool = False):
    if not include_urgency:
        print("ROC Weights (base weighted criteria):")
        for k, v in PRIORITY_ROC_WEIGHTS_BASE.items():
            print(f"  {k}: {v:.4f}")
        print("")
        print("Note: urgency is optional. To see 7-criteria weights call with include_urgency=True.")
        return

    print("ROC Weights (full weighted criteria, including 'urgency'):")
    for k, v in PRIORITY_ROC_WEIGHTS_FULL.items():
        print(f"  {k}: {v:.4f}")


# Run only if executed directly
if __name__ == "__main__":
    print_priority_roc_weights()
