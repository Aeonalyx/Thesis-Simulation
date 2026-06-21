import json
import random
from datetime import datetime, timedelta

colleges = ["COE", "CED", "CASS", "CSM", "CEBA", "CCS", "CHS"]
documents = [
    "Diploma",
]
requesters = [
    "Graduating Student",
]

requests = []

# First 5 requests have identical time
for i in range(5):
    requests.append({
        "college": "COE",
        "document_type": "Diploma",
        "urgency": random.randint(1, 10),
        "requester_type": random.choice(requesters),
        "submission_time": "09:15",
        "payment_status": "Paid",
        "requirements_stage": "complete"
    })

# Remaining 95 requests
start = datetime.strptime("09:16", "%H:%M")

for i in range(95):
    t = start + timedelta(minutes=i)
    requests.append({
        "college": random.choice(colleges),
        "document_type": random.choice(documents),
        "urgency": random.randint(1, 10),
        "requester_type": random.choice(requesters),
        "submission_time": t.strftime("%H:%M"),
        "payment_status": random.choice(["Paid", "Unpaid"]),
        "requirements_stage": random.choice(["complete", "partial", "incomplete"])
    })

print(json.dumps(requests, indent=2))