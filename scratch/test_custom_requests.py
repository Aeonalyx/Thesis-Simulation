import requests
import json
import time

BACKEND_URL = "http://localhost:5000"

def test_endpoints():
    print("1. Clearing custom requests...")
    res = requests.delete(f"{BACKEND_URL}/api/custom-requests")
    assert res.status_code == 200, f"Failed clearing: {res.text}"
    print("   Cleared successfully.")

    print("\n2. Getting custom requests (should be empty)...")
    res = requests.get(f"{BACKEND_URL}/api/custom-requests")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 0, f"Expected 0 requests, got {len(data)}"
    print("   Verified empty list.")

    print("\n3. Adding a custom request...")
    payload = {
        "college": "COE",
        "document_type": "Diploma",
        "urgency": 9,
        "requester_type": "Graduating Student",
        "submission_time": "09:15",
        "payment_status": "Paid",
        "requirements_stage": "complete"
    }
    res = requests.post(f"{BACKEND_URL}/api/custom-requests", json=payload)
    assert res.status_code == 201, f"Failed adding custom request: {res.text}"
    added_res = res.json()
    assert added_res["success"] is True
    req_id = added_res["request_id"]
    print(f"   Added successfully. ID: {req_id}")

    print("\n4. Getting custom requests (should contain 1 request)...")
    res = requests.get(f"{BACKEND_URL}/api/custom-requests")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["request_id"] == req_id
    assert data[0]["college"] == "COE"
    assert data[0]["document_type"] == "Diploma"
    print("   Verified request list correctly lists the added request.")

    print("\n5. Running simulation (with disable_generated_requests=True)...")
    sim_payload = {
        "scheduler_type": "FCFS",
        "allocator_type": "college_based",
        "scenario": "baseline",
        "num_staff": 7,
        "quota_limit": 20,
        "total_requests": 5,
        "disable_generated_requests": True
    }
    res = requests.post(f"{BACKEND_URL}/simulate", json=sim_payload)
    assert res.status_code == 200, f"Failed simulation: {res.text}"
    sim_res = res.json()
    assert sim_res["success"] is True
    
    completed = sim_res["results"]["completed_requests"]
    print(f"   Completed requests count: {len(completed)}")
    assert len(completed) == 1, f"Expected 1 completed request (our custom request), got {len(completed)}"
    assert completed[0]["request_id"] == req_id
    assert completed[0]["is_custom"] is True
    print("   Successfully verified that custom request was simulated with is_custom=True!")

    print("\n6. Running simulation (with disable_generated_requests=False)...")
    sim_payload["disable_generated_requests"] = False
    res = requests.post(f"{BACKEND_URL}/simulate", json=sim_payload)
    assert res.status_code == 200
    sim_res = res.json()
    completed = sim_res["results"]["completed_requests"]
    print(f"   Completed requests count with generator enabled: {len(completed)}")
    # Should be 5 generated + 1 custom = 6 overall
    assert len(completed) == 6, f"Expected 6 completed requests, got {len(completed)}"
    
    custom_in_list = [r for r in completed if r["is_custom"]]
    assert len(custom_in_list) == 1
    assert custom_in_list[0]["request_id"] == req_id
    print("   Successfully verified combined run (5 generated + 1 custom = 6 total)!")

    print("\n7. Deleting the custom request...")
    res = requests.delete(f"{BACKEND_URL}/api/custom-requests/{req_id}")
    assert res.status_code == 200
    print("   Deleted successfully.")

    print("\n8. Getting custom requests (should be empty again)...")
    res = requests.get(f"{BACKEND_URL}/api/custom-requests")
    data = res.json()
    assert len(data) == 0
    print("   Verified empty list after deletion.")
    
    print("\nALL BACKEND TESTS PASSED!")

if __name__ == "__main__":
    test_endpoints()
