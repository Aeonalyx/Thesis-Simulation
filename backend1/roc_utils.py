"""
roc_utils.py
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
priority_criteria_ranking = [
    "completeness_of_requirements",
    "submission_time",
    "document_type",
    "requester_status",
    "college_affiliation",
    "payment_status",
    # Note: `urgency` is optional. The base ROC weights (used by default)
    # consider only the six criteria above. When urgency is enabled in the
    # simulation, include it as a seventh criterion below.
]

# Compute weights
PRIORITY_ROC_WEIGHTS_BASE = calculate_roc_weights(priority_criteria_ranking)

# Full ranking including urgency (used when urgency is enabled)
priority_criteria_ranking_full = priority_criteria_ranking + ["urgency"]
PRIORITY_ROC_WEIGHTS_FULL = calculate_roc_weights(priority_criteria_ranking_full)

# Public default: keep existing behavior (6 criteria) unless callers opt-in.
PRIORITY_ROC_WEIGHTS = PRIORITY_ROC_WEIGHTS_BASE

# Optional: expose individual weights (for direct import use)
completeness_of_requirements_weight = PRIORITY_ROC_WEIGHTS["completeness_of_requirements"]
submission_time_weight = PRIORITY_ROC_WEIGHTS["submission_time"]
document_type_weight = PRIORITY_ROC_WEIGHTS["document_type"]
requester_status_weight = PRIORITY_ROC_WEIGHTS["requester_status"]
college_affiliation_weight = PRIORITY_ROC_WEIGHTS["college_affiliation"]
payment_status_weight = PRIORITY_ROC_WEIGHTS["payment_status"]


# Debug / verification utility
def print_priority_roc_weights():
    """Print the default (base) ROC weights and explain urgency behavior.

    By default the module exposes the 6-criteria ROC weights. If you want
    to see the weights including `urgency` (7 criteria), call
    `print_priority_roc_weights(include_urgency=True)`.
    """
    print("ROC Weights (base 6 criteria):")
    for k, v in PRIORITY_ROC_WEIGHTS_BASE.items():
        print(f"  {k}: {v:.4f}")
    print("")
    print("Note: urgency is optional. To see 7-criteria weights call with include_urgency=True.")


def print_priority_roc_weights(include_urgency: bool = False):
    if not include_urgency:
        print("ROC Weights (base 6 criteria):")
        for k, v in PRIORITY_ROC_WEIGHTS_BASE.items():
            print(f"  {k}: {v:.4f}")
        print("")
        print("Note: urgency is optional. To see 7-criteria weights call with include_urgency=True.")
        return

    print("ROC Weights (full 7 criteria, including 'urgency'):")
    for k, v in PRIORITY_ROC_WEIGHTS_FULL.items():
        print(f"  {k}: {v:.4f}")


# Run only if executed directly
if __name__ == "__main__":
    print_priority_roc_weights()