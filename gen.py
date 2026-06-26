import json
import os
import random
from datetime import datetime, timedelta

# ============================================================================
# CONFIGURATION
# ============================================================================

random.seed(42)

OUTPUT_FOLDER = r"C:\Users\Acer\.vscode\Thesis-Simulation\json"

TOR_DOCUMENT = "Official Transcript of Records (TOR) and Transfer Credentials (TC)"
ALRP_DOCUMENT = "Academic Load Revision (ALRP)"

COLLEGES = [
    "COE",
    "CED",
    "CASS",
    "CSM",
    "CEBA",
    "CCS",
    "CHS",
]

COMPLETENESS_WEIGHTS = {
    "incomplete": 20,
    "partial": 30,
    "complete": 50,
}

PAYMENT_WEIGHTS = {
    "Paid": 70,
    "Unpaid": 30,
}


# ============================================================================
# HELPERS
# ============================================================================

def generate_time(start_hour=8, end_hour=17):
    start = datetime.strptime(f"{start_hour}:00", "%H:%M")
    end = datetime.strptime(f"{end_hour}:00", "%H:%M")

    delta_minutes = int((end - start).total_seconds() // 60)

    return (
        start + timedelta(minutes=random.randint(0, delta_minutes))
    ).strftime("%H:%M")


def weighted_choice(weight_dict):
    return random.choices(
        population=list(weight_dict.keys()),
        weights=list(weight_dict.values()),
        k=1,
    )[0]


# ============================================================================
# GENERATE REQUESTS
# ============================================================================

requests = []

# --------------------------------------------------------------------------
# 295 TOR Requests
# Restriction: TOR can ONLY be requested by Alumni
# --------------------------------------------------------------------------

for _ in range(295):
    requests.append({
        "college": random.choice(COLLEGES),
        "document_type": TOR_DOCUMENT,
        "urgency": random.randint(1, 10),
        "requester_type": "Alumni",
        "submission_time": generate_time(),
        "payment_status": weighted_choice(PAYMENT_WEIGHTS),
        "requirements_stage": weighted_choice(COMPLETENESS_WEIGHTS),
    })

# --------------------------------------------------------------------------
# 5 Academic Load Revision Requests
# Restriction: ALRP can ONLY be requested by Regular Student
# --------------------------------------------------------------------------

for _ in range(5):
    requests.append({
        "college": random.choice(COLLEGES),
        "document_type": ALRP_DOCUMENT,
        "urgency": random.randint(1, 10),
        "requester_type": "Regular Student",
        "submission_time": generate_time(),
        "payment_status": weighted_choice(PAYMENT_WEIGHTS),
        "requirements_stage": weighted_choice(COMPLETENESS_WEIGHTS),
    })

# Shuffle so the 5 ALRP requests aren't always at the end
random.shuffle(requests)

# ============================================================================
# SAVE JSON
# ============================================================================

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

output_file = os.path.join(
    OUTPUT_FOLDER,
    f"custom_requests_{timestamp}.json"
)

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(requests, f, indent=2)

print("=" * 60)
print(f"Generated {len(requests)} requests.")
print(f"TOR Requests   : 295")
print(f"ALRP Requests  : 5")
print(f"Saved to:")
print(output_file)
print("=" * 60)