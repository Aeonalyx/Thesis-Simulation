from backend2.roc_utils import PRIORITY_ROC_WEIGHTS

# ============================================================================
# DEFAULT CONFIGURATION
# ============================================================================

# from backend1.roc_utils import (
#     urgency_weight,
#     requester_type_weight,
#     waiting_time_weight,
#     document_type_weight,
# )
PRIORITY_WEIGHTS = PRIORITY_ROC_WEIGHTS
# PRIORITY_WEIGHTS = {
#     "urgency": 0.40,
#     "requester_type": 0.25,
#     "waiting_time": 0.20,
#     "document_type": 0.15,
# }

REQUESTER_PRIORITY = {
    "Graduating Student": 1,
    "Faculty": 1,
    "Alumni": 1,
    "Regular Student": 1,
}

# Not made to match data from Student Population 2025-2026 Semester 2 from OUR, slightly adjusted

REQUESTER_GENERATION_WEIGHTS = {
    "Regular Student": 0.65,
    "Graduating Student": 0.18,
    "Alumni": 0.10,
    "Faculty": 0.07,
}
REQUESTER_PRIORITY_MAX = max(REQUESTER_PRIORITY.values()) if REQUESTER_PRIORITY else 1

# Controls the final priority score soft-cap (lower raises scores faster).
PRIORITY_SCORE_HALF_LIFE = 0.15

# Durations can be workdays (number) or strings like "2 day" / "18 hour".
DOCUMENT_COMPLEXITY = {
    "Certification, Authentication and Verification (CAV)": "3 days",
    "Official Transcript of Records (TOR) and Transfer Credentials (TC)": "3 days",
    "Certification": "1 day",
    "Diploma": "4 hours",
    "Evaluation of Grades; Report of Grades (ROG); Certificate of Registration (COR)": "4 hours",
    "Permit to Cross-Enrol": "1 hour",
    "Authentication": "4 hours",
    "Academic Load Revision (ALRP)": "1 hour",
    "Grading Sheets": "1 day",
    "Shifter’s Form, Returnee’s Form or Leave of Absence": "1 day",
    "Completion Forms": "1 day",
    "Advance Credit": "1 day",
    "Registration of Old and Returnee Students": "1 hour",
}

DOCUMENT_REQUESTER_RESTRICTIONS = {
    "Certification, Authentication and Verification (CAV)": ["Graduating Student", "Alumni"],
    "Official Transcript of Records (TOR) and Transfer Credentials (TC)": ["Alumni"],
    "Certification": ["Alumni"],
    "Diploma": ["Alumni"],
    "Evaluation of Grades; Report of Grades (ROG); Certificate of Registration (COR)": [
        "Graduating Student",
        "Alumni",
        "Regular Student",
    ],
    "Permit to Cross-Enrol": ["Graduating Student", "Alumni", "Regular Student"],
    "Authentication": ["Graduating Student", "Alumni", "Regular Student"],
    "Academic Load Revision (ALRP)": ["Regular Student"],
    "Grading Sheets": ["Faculty"],
    "Shifter’s Form, Returnee’s Form or Leave of Absence": ["Regular Student"],
    "Completion Forms": ["Faculty"],
    "Registration of Old and Returnee Students": ["Regular Student"],
}

DOCUMENT_PAYMENT_REQUIRED = {
    "Grading Sheets": False,
}

COLLEGES = ["COE", "CED", "CASS", "CSM", "CEBA", "CCS", "CHS"]

# COE 3236
# CED 2533
# CASS 2515
# CSM 2047
# CEBA 1296
# CCS 1037
# CHS 520
# Total = 13,184, 13881 if including other colleges as per Student Population 2025-2026 Semester 2 from OUR

COLLEGE_POPULATION = {
    "COE": 0.2454,
    "CED": 0.1921,
    "CASS": 0.1908,
    "CSM": 0.1553,
    "CEBA": 0.0983,
    "CCS": 0.0787,
    "CHS": 0.0394,
}

COMPLETENESS_LEVELS = {
    "incomplete": 0.3,
    "partial": 0.7,
    "complete": 1.0,
}
REQUIREMENTS_PARTIAL_DELAY_HOURS_RANGE = (0.0, 0.2) # up to 12 minutes for partial requirements
REQUIREMENTS_COMPLETE_EXTRA_DELAY_HOURS_RANGE = (0.0, 1.0) # up to 1 hour after partial for complete requirements
PAYMENT_DELAY_HOURS_RANGE = (0.0, 48.0) # up to 2 days for payment after submission (if required)