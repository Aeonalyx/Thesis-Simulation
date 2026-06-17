"""
Flask Backend API for Thesis Simulation Engine
Wraps the scheduler_engine1.py with REST endpoints for running simulations
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
try:
    # Works when run from workspace root as a package
    from backend1.scheduler_engine1 import SimulationEngine, COLLEGES, DOCUMENT_COMPLEXITY, COLLEGE_POPULATION
    from backend1.roc_utils import PRIORITY_ROC_WEIGHTS_BASE, PRIORITY_ROC_WEIGHTS_FULL
except ImportError:
    # Works when run directly from backend1/ as a script
    from scheduler_engine1 import SimulationEngine, COLLEGES, DOCUMENT_COMPLEXITY, COLLEGE_POPULATION
    from roc_utils import PRIORITY_ROC_WEIGHTS_BASE, PRIORITY_ROC_WEIGHTS_FULL


app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access



# ============================================================================
# HELPER: Convert responses to JSON-serializable format
# ============================================================================

def to_json_serializable(obj):
    """Convert datetime objects to ISO format strings for JSON"""
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    return str(obj)

app.json.default = to_json_serializable 

def get_staff_info(engine):
    return [{
        "staff_id": s.staff_id, "name": s.name, 
        "college_affiliation": s.college_affiliation, "quota_limit": s.quota_limit
    } for s in engine.staff_pool]

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "Thesis Simulation Backend Running"})


@app.route('/config', methods=['GET'])
def get_config():
    """Get simulation configuration and constants"""
    return jsonify({
        "colleges": COLLEGES,
        "document_types": list(DOCUMENT_COMPLEXITY.keys()),
        "document_complexity": DOCUMENT_COMPLEXITY,
        "college_population": COLLEGE_POPULATION,
        "allocator_types": ["college_based", "workload_based", "pooled", "quota_free"],
        "scheduler_types": ["FCFS", "WEIGHTED"],
        "scenarios": ["baseline", "staff_absence", "peak_urgency", "workload_imbalance","peak_period"],
        "priority_weights_base": PRIORITY_ROC_WEIGHTS_BASE,
        "priority_weights_full": PRIORITY_ROC_WEIGHTS_FULL
    })


@app.route('/simulate', methods=['POST'])
def run_simulation():
    """
    Run a simulation with custom parameters
    
    Request JSON (all optional):
    {
        "scheduler_type": "FCFS",
        "allocator_type": "college_based",
        "scenario": "baseline",
        "num_staff": 6,
        "quota_limit": 20,
        "total_requests": 200,
        "urgency_base": 5,
        "imbalance_factor": 0,
        "num_absent_staff": 0,
        "random_seed": 12345,
        "work_start": "08:00",
        "work_end": "17:00",
        "priority_weights": {
            "completeness_of_requirements": 0.30,
            "submission_time": 0.22,
            "document_type": 0.18,
            "requester_status": 0.14,
            "college_affiliation": 0.10,
            "payment_status": 0.06
        }
    }
    
    Returns: Simulation metrics and results
    """
    try:
        data = request.get_json() or {}
        
        # Extract parameters with defaults
        scheduler_type = data.get('scheduler_type', 'FCFS')
        allocator_type = data.get('allocator_type', 'college_based')
        scenario = data.get('scenario', 'baseline')
        num_staff = data.get('num_staff', len(COLLEGES))
        quota_limit = data.get('quota_limit', 20)
        total_requests = data.get('total_requests', data.get('num_requests', 200))
        urgency_base = data.get('urgency_base', 5)
        imbalance_factor = data.get('imbalance_factor', 0)
        num_absent_staff = data.get('num_absent_staff', 0)
        random_seed = data.get('random_seed')
        work_start = data.get('work_start', '08:00')
        work_end = data.get('work_end', '17:00')
        priority_weights = data.get('priority_weights')
        urgency = data.get('urgency', False)
        
        # Validate inputs
        if scheduler_type not in ['FCFS', 'WEIGHTED']:
            return jsonify({"error": f"Invalid scheduler_type: {scheduler_type}"}), 400
        
        if allocator_type not in ['college_based', 'workload_based', 'pooled', 'quota_free']:
            return jsonify({"error": f"Invalid allocator_type: {allocator_type}"}), 400
        
        if scenario not in ['baseline', 'staff_absence', 'peak_urgency', 'workload_imbalance','peak_period']:
            return jsonify({"error": f"Invalid scenario: {scenario}"}), 400
        
        # Create and run simulation
        engine = SimulationEngine(
            scheduler_type=scheduler_type,
            allocator_type=allocator_type,
            staff_config={
                "num_staff": num_staff,
                "quota_limit": quota_limit
            },
            priority_weights=priority_weights,
            random_seed=random_seed,
            work_start=work_start,
            work_end=work_end,
            urgency=urgency,
        )

        results = engine.run(custom_config={
            "scenario": scenario,
            "total_requests": total_requests,
            "urgency_base": urgency_base,
            "imbalance_factor": imbalance_factor,
            "num_absent_staff": num_absent_staff,
        })

        staff_info = get_staff_info(engine)
        
        # Return results with additional metadata
        return jsonify({
            "success": True,
            "parameters": {
                "scheduler_type": scheduler_type,
                "allocator_type": allocator_type,
                "scenario": scenario,
                "num_staff": num_staff,
                "quota_limit": quota_limit,
                "total_requests": total_requests,
                "urgency_base": urgency_base,
                "imbalance_factor": imbalance_factor,
                "num_absent_staff": num_absent_staff,
                "random_seed": results.get("seed_used"),
                "work_start": work_start,
                "work_end": work_end,
            },
            "results": {**results, "staff_info": staff_info},
            "completed_requests": len(engine.completed),
            "staff_load": results['staff_load']
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/simulate/quick', methods=['POST'])
def run_quick_simulation():
    """
    Run a quick baseline simulation (default parameters)
    
    Request JSON (optional):
    {
        "num_requests": 80  (optional)
    }
    """
    try:
        data = request.get_json() or {}
        random_seed = data.get('random_seed')
        total_requests = data.get('total_requests', data.get('num_requests', 200))
        
        engine = SimulationEngine(
            scheduler_type='FCFS',
            allocator_type='college_based',
            staff_config={"num_staff": len(COLLEGES), "quota_limit": 20},
            random_seed=random_seed,
        )

        results = engine.run(custom_config={
            "scenario": 'baseline',
            "total_requests": total_requests,
        })

        staff_info = get_staff_info(engine)
        
        return jsonify({
            "success": True,
            "results": {**results, "staff_info": staff_info},
            "staff_load": results['staff_load']
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/simulate/compare', methods=['POST'])
def compare_allocators():
    """
    Compare different allocator strategies on same scenario
    
    Request JSON:
    {
        "scenario": "baseline",
        "num_staff": 6,
        "quota_limit": 20
    }
    
    Returns: Results for all 4 allocator types
    """
    try:
        data = request.get_json() or {}
        
        scheduler_type = data.get('scheduler_type', 'FCFS')
        scenario = data.get('scenario', 'baseline')
        num_staff = data.get('num_staff', len(COLLEGES))
        quota_limit = data.get('quota_limit', 20)
        total_requests = data.get('total_requests', 200)
        urgency_base = data.get('urgency_base', 5)
        imbalance_factor = data.get('imbalance_factor', 0)
        num_absent_staff = data.get('num_absent_staff', 0)
        random_seed = data.get('random_seed', 12345)
        work_start = data.get('work_start', '08:00')
        work_end = data.get('work_end', '17:00')
        priority_weights = data.get('priority_weights')
        urgency = data.get('urgency', False)
        
        allocators = ['college_based', 'workload_based', 'pooled', 'quota_free']
        results = {}
        
        for allocator in allocators:
            engine = SimulationEngine(
                scheduler_type=scheduler_type,
                allocator_type=allocator,
                staff_config={"num_staff": num_staff, "quota_limit": quota_limit},
                priority_weights=priority_weights,
                random_seed=random_seed,
                work_start=work_start,
                work_end=work_end,
                urgency=urgency,
            )

            sim_results = engine.run(custom_config={
                "scenario": scenario,
                "total_requests": total_requests,
                "urgency_base": urgency_base,
                "imbalance_factor": imbalance_factor,
                "num_absent_staff": num_absent_staff,
            })
            staff_info = get_staff_info(engine)
            results[allocator] = {
                "metrics": {**sim_results, "staff_info": staff_info},
                "staff_load": sim_results['staff_load']
            }
        
        return jsonify({
            "success": True,
            "scheduler_type": scheduler_type,
            "scenario": scenario,
            "seed_used": random_seed,
            "comparison": results
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/info', methods=['GET'])
def api_info():
    """Get API documentation and available endpoints"""
    return jsonify({
        "version": "1.0",
        "name": "Thesis Simulation Backend",
        "endpoints": {
            "GET /health": "Health check",
            "GET /config": "Get simulation configuration",
            "GET /api/info": "Get API documentation",
            "POST /simulate": "Run simulation with custom parameters",
            "POST /simulate/quick": "Run baseline simulation",
            "POST /simulate/compare": "Compare allocator strategies"
        }
    })


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("""
    ═══════════════════════════════════════════════════════════════════
    🎓 Thesis Simulation Backend API
    ═══════════════════════════════════════════════════════════════════
    
    Server running on: http://localhost:5000
    
    Available endpoints:
    • GET  http://localhost:5000/health          - Health check
    • GET  http://localhost:5000/config          - Configuration
    • GET  http://localhost:5000/api/info        - API documentation
    • POST http://localhost:5000/simulate        - Run simulation
    • POST http://localhost:5000/simulate/quick  - Quick baseline
    • POST http://localhost:5000/simulate/compare - Compare allocators
    
    ═══════════════════════════════════════════════════════════════════
    """)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False  # Disable reloader to avoid double-running simulations
    )
