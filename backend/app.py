"""
Flask API Backend for Registrar Simulation
Exposes real scheduling algorithms via REST endpoints
"""
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from scheduler_engine import SimulationEngine, DocumentRequest  # Import engine only

ACTIVE_QUEUE = {
    "scheduler": "FCFS",
    "requests": []
}

app = Flask(__name__)
CORS(app)

@app.route('/api/queue/add', methods=['POST'])
def add_to_queue():
    data = request.get_json()
    scheduler_type = data.get('scheduler', 'FCFS').upper()
    ACTIVE_QUEUE["scheduler"] = scheduler_type
    
    req = DocumentRequest(
        request_id=f"MANUAL-{len(ACTIVE_QUEUE['requests'])+1:03d}",
        college=data['college'],
        document_type=data['document_type'],
        urgency=int(data['urgency']),
        requester_type=data['requester_type'],
        submission_time=datetime.now(),
        priority_score=0.0
    )
    
    # Calculate priority if Weighted scheduler is active
    if scheduler_type == "WEIGHTED":
        req.calculate_priority(req.submission_time)
        
    ACTIVE_QUEUE["requests"].append(req)
    
    # Sort queue based on active scheduler
    if scheduler_type == "FCFS":
        ACTIVE_QUEUE["requests"].sort(key=lambda r: r.submission_time)
    else:
        ACTIVE_QUEUE["requests"].sort(key=lambda r: r.priority_score, reverse=True)
        
    return jsonify({
        "status": "added", 
        "request_id": req.request_id,
        "position": ACTIVE_QUEUE["requests"].index(req) + 1
    }), 200

@app.route('/api/queue/status', methods=['GET'])
def get_queue_status():
    queue_data = []
    for idx, req in enumerate(ACTIVE_QUEUE["requests"]):
        queue_data.append({
            "Position": idx + 1,
            "Request ID": req.request_id,
            "College": req.college,
            "Document Type": req.document_type,
            "Urgency": req.urgency,
            "Requester Type": req.requester_type,
            "Priority Score": round(req.priority_score, 2) if ACTIVE_QUEUE["scheduler"] == "WEIGHTED" else "N/A",
            "Submitted At": req.submission_time.strftime("%H:%M:%S"),
            "Is Manual": req.request_id.startswith("MANUAL-")
        })
        
    return jsonify({
        "scheduler": ACTIVE_QUEUE["scheduler"],
        "total_in_queue": len(queue_data),
        "queue": queue_data
    }), 200

@app.route('/api/queue/clear', methods=['POST'])
def clear_queue():
    ACTIVE_QUEUE["requests"].clear()
    return jsonify({"status": "cleared"}), 200

@app.route('/api/simulate', methods=['POST'])
def simulate():
    data = request.get_json()
    
    scheduler_map = {"FCFS": "FCFS", "Weighted Priority-Based": "WEIGHTED"}
    allocator_map = {
        "College-Based Assignment": "college_based",
        "Workload-Based Assignment with College Affiliation": "workload_based",
        "Pooled Scheduling": "pooled",
        "Quota-Free Allocation": "quota_free"
    }
    scenario_map = {
        "Baseline": "baseline",
        "Staff Absence": "staff_absence",
        "Peak Urgency": "peak_urgency",
        "Workload Imbalance": "workload_imbalance"
    }
    
    try:
        advanced = data.get('advanced_settings', {})
        staff_config = None
        if advanced.get('enable_custom_staff'):
            staff_config = {
                'enable_custom_staff': True,  
                'num_staff': int(advanced.get('num_staff', 6))
            }
            
        # ===== SYNC LOGIC =====
        use_queue = data.get('use_active_queue', False)
        preloaded_requests = None
        source_type = "Auto-Generated"
        
        if use_queue and len(ACTIVE_QUEUE.get('requests', [])) > 0:
            preloaded_requests = ACTIVE_QUEUE['requests']
            source_type = f"Active Queue ({len(preloaded_requests)} requests)"
            print(f"📥 Simulating with {len(preloaded_requests)} requests from queue")
        else:
            print("🔄 Generating fresh requests for simulation")
            
        engine = SimulationEngine(
            scheduler_type=scheduler_map.get(data['scheduler'], "FCFS"),
            allocator_type=allocator_map.get(data['allocator'], "college_based"),
            staff_config=staff_config
        )
        
        metrics = engine.run(
            scenario=scenario_map.get(data['scenario'], "baseline"),
            duration_min=data.get('duration_minutes', 60),
            preloaded_requests=preloaded_requests
        )
        
        # Add metadata to response
        metrics['data_source'] = source_type
        
        return jsonify(metrics), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "Backend is running"}), 200

@app.route('/api/queue/load-scenario', methods=['POST'])
def load_scenario_queue():
    data = request.get_json()
    
    # Clear existing queue to prevent duplicates
    ACTIVE_QUEUE["requests"].clear()
    
    scheduler_type = data.get('scheduler', 'FCFS').upper()
    ACTIVE_QUEUE["scheduler"] = scheduler_type
    
    # Use a temporary engine just for request generation
    temp_engine = SimulationEngine(
        scheduler_type=scheduler_type,
        allocator_type=data.get('allocator', 'college_based'),
        staff_config=None
    )
    
    # Generate auto-requests based on UI config
    scenario = data.get('scenario', 'baseline')
    duration = data.get('duration_minutes', 60)
    auto_requests = temp_engine._generate_requests(scenario, duration)
    
    # Add to global queue
    for req in auto_requests:
        # Tag as auto-generated
        req.is_manual = False
        ACTIVE_QUEUE["requests"].append(req)
        
    # Sort queue based on active scheduler
    if scheduler_type == "FCFS":
        ACTIVE_QUEUE["requests"].sort(key=lambda r: r.submission_time)
    else:
        for r in ACTIVE_QUEUE["requests"]:
            r.calculate_priority(r.submission_time)
        ACTIVE_QUEUE["requests"].sort(key=lambda r: r.priority_score, reverse=True)
        
    return jsonify({"status": "loaded", "count": len(ACTIVE_QUEUE["requests"])}), 200

if __name__ == '__main__':
    print("🚀 Starting Registrar Simulation Backend on http://localhost:5000")
    print("   Endpoints:")
    print("   - POST /api/simulate  : Run simulation with your algorithms")
    print("   - GET  /api/health    : Check if backend is running")
    app.run(host='127.0.0.1', port=5000, debug=False)