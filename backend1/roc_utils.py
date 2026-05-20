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
    "urgency",
]

# Compute weights
PRIORITY_ROC_WEIGHTS = calculate_roc_weights(priority_criteria_ranking)

# Optional: expose individual weights (for direct import use)
completeness_of_requirements_weight = PRIORITY_ROC_WEIGHTS["completeness_of_requirements"]
submission_time_weight = PRIORITY_ROC_WEIGHTS["submission_time"]
document_type_weight = PRIORITY_ROC_WEIGHTS["document_type"]
requester_status_weight = PRIORITY_ROC_WEIGHTS["requester_status"]
college_affiliation_weight = PRIORITY_ROC_WEIGHTS["college_affiliation"]
payment_status_weight = PRIORITY_ROC_WEIGHTS["payment_status"]


# Debug / verification utility
def print_priority_roc_weights():
    print("Current ROC Weights for Interview Criteria:")
    for k, v in PRIORITY_ROC_WEIGHTS.items():
        print(f"  {k}: {v:.4f}")


# Run only if executed directly
if __name__ == "__main__":
    print_priority_roc_weights()