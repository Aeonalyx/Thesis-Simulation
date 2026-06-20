import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend1.scheduler_engine1 import SimulationEngine, DocumentRequest
import sqlite3

def debug():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(os.path.dirname(base_dir), 'backend1', 'custom_requests.db')
    print("Database path:", db_path)
    
    # 1. Clear database and insert test request
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("DELETE FROM custom_requests")
    cursor.execute('''
        INSERT INTO custom_requests (
            request_id, college, document_type, urgency, requester_type, submission_time,
            completeness_of_requirements, payment_status, requirements_stage
        ) VALUES ('CUST0001', 'COE', 'Diploma', 9, 'Graduating Student', '09:15', 1.0, 'Paid', 'complete')
    ''')
    conn.commit()
    
    # Query database to confirm
    cursor.execute("SELECT * FROM custom_requests")
    rows = cursor.fetchall()
    print("Stored custom requests in DB:")
    for row in rows:
        print(dict(row))
    conn.close()
    
    # 2. Run simulation engine
    print("\nRunning SimulationEngine...")
    engine = SimulationEngine(
        scheduler_type="FCFS",
        allocator_type="college_based",
        staff_config={"num_staff": 7, "quota_limit": 20},
    )
    
    results = engine.run(custom_config={
        "scenario": "baseline",
        "disable_generated_requests": True
    })
    
    print("\nCompleted Requests:")
    for req in results["completed_requests"]:
        print(req)
        
    print("\nWaiting Queue:")
    for req in results["waiting_queue"]:
        print(req)
        
    print("\nEvent Log:")
    for event in results["event_log"]:
        print(event)

if __name__ == "__main__":
    debug()
