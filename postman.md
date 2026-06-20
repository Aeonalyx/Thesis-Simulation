Step 1: Open Postman and Create a Request
Open the Postman application.
Click the + (New tab) button at the top to open a new request workspace.
Step 2: Add a Custom Request (POST)
To store a new custom request into the simulation database:

Set the Request Method dropdown to POST.
Enter the URL: http://localhost:5000/api/custom-requests
Click the Headers tab below the URL bar.
Add a new row with Key: Content-Type and Value: application/json.
Click the Body tab, select the raw radio button, and choose JSON from the format dropdown.
Paste the following JSON data:
json
{
    "college": "COE",
    "document_type": "Diploma",
    "urgency": 9,
    "requester_type": "Graduating Student",
    "submission_time": "09:15",
    "payment_status": "Paid",
    "requirements_stage": "complete"
}
Click Send.
Expected Response (Status: 201 Created):
json
{
    "success": true,
    "message": "Custom request added successfully",
    "request_id": "CUST0001"
}
Step 3: Get the List of Custom Requests (GET)
To verify your custom request was stored in the SQLite database:

Open a new request tab in Postman.
Set the Method to GET.
Enter the URL: http://localhost:5000/api/custom-requests
Click Send.
Expected Response (Status: 200 OK):
json
[
    {
        "request_id": "CUST0001",
        "college": "COE",
        "document_type": "Diploma",
        "urgency": 9,
        "requester_type": "Graduating Student",
        "submission_time": "09:15",
        "payment_status": "Paid",
        "requirements_stage": "complete",
        ...
    }
]
Step 4: Run the Simulation (POST)
To run a simulation incorporating this custom request and excluding generated requests:

Open a new request tab in Postman.
Set the Method to POST.
Enter the URL: http://localhost:5000/simulate
Go to Body -> raw -> JSON.
Paste this configuration:
json
{
    "scheduler_type": "FCFS",
    "allocator_type": "college_based",
    "scenario": "baseline",
    "num_staff": 7,
    "quota_limit": 20,
    "disable_generated_requests": true
}
Click Send.
Expected Response (Status: 200 OK): You will receive the full simulation results, including metrics showing CUST0001 was processed and completed.
json
{
    "success": true,
    "results": {
        "completed_requests": [
            {
                "request_id": "CUST0001",
                "is_custom": true,
                ...
            }
        ],
        ...
    }
}
Step 5: Clean Up / Delete Requests
To delete a single request (DELETE):

Method: DELETE
URL: http://localhost:5000/api/custom-requests/CUST0001
Expected Response: {"success": true, "message": "Custom request CUST0001 deleted successfully"}
To delete all requests (DELETE):

Method: DELETE
URL: http://localhost:5000/api/custom-requests
Expected Response: {"success": true, "message": "All custom requests cleared successfully"}