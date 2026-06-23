import json
import random
from datetime import datetime, timedelta

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

colleges = ["COE", "CED", "CASS", "CSM", "CEBA", "CCS", "CHS"]
requesters = ["Graduating Student", "Alumni", "Regular Student", "Faculty"]

COMPLETENESS_LEVELS = {
    "incomplete": 0.3,
    "partial": 0.7,
    "complete": 1.0,
}

# build reverse map: requester -> allowed documents
requester_to_docs = {}
for doc, allowed_requesters in DOCUMENT_REQUESTER_RESTRICTIONS.items():
    for r in allowed_requesters:
        requester_to_docs.setdefault(r, []).append(doc)

def generate_time(start_hour=8, end_hour=17):
    start = datetime.strptime(f"{start_hour}:00", "%H:%M")
    end = datetime.strptime(f"{end_hour}:00", "%H:%M")
    delta = int((end - start).total_seconds() // 60)
    return (start + timedelta(minutes=random.randint(0, delta))).strftime("%H:%M")

requests = []

# First 5 FCFS stress test (same time)
base_time = "09:15"

for i in range(5):
    requester = random.choice(requesters)
    doc = random.choice(requester_to_docs.get(requester, ["Certification"]))

    requests.append({
        "college": "COE",
        "document_type": doc,
        "urgency": 10,
        "requester_type": requester,
        "submission_time": base_time,
        "payment_status": "Unpaid",
        "requirements_stage": "incomplete"
    })

# Remaining requests
for i in range(295):
    requester = random.choice(requesters)
    doc = random.choice(requester_to_docs.get(requester, ["Certification"]))

    requests.append({
        "college": random.choice(colleges),
        "document_type": doc,
        "urgency": random.randint(1, 10),
        "requester_type": requester,
        "submission_time": generate_time(8, 17),
        "payment_status": random.choice(["Paid", "Unpaid"]),
        "requirements_stage": random.choices(
            population=list(COMPLETENESS_LEVELS.keys()),
            weights=list(COMPLETENESS_LEVELS.values()),
            k=1
        )[0]
    })

print(json.dumps(requests, indent=2))