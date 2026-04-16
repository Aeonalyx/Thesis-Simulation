"""
Frontend UI that connects to REAL simulation engine
Displays actual metrics from your scheduling algorithms
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="Registrar Simulation System",
    layout="wide"
)

# Custom styling to match thesis mockup
st.markdown("""
<style>
    .metric-card { border-radius: 10px; padding: 15px; background-color: #f8f9fa; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 15px; }
    .staff-card { border-radius: 8px; padding: 12px; background-color: #e9f7fe; margin-bottom: 10px; border-left: 4px solid #1f77b4; }
    .scenario-tag { display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 0.85rem; font-weight: 500; }
    .baseline { background-color: #e3f2fd; color: #1976d2; }
    .staff-absence { background-color: #ffebee; color: #d32f2f; }
    .peak-urgency { background-color: #fff8e1; color: #f57c00; }
    .workload-imbalance { background-color: #e8f5e8; color: #388e3c; }
</style>
""", unsafe_allow_html=True)

# Header
col1 = st.columns([1, 5])
with col1[1]:
    st.title("MSU-IIT Registrar Document Request Simulation")
    st.markdown("Evaluating Priority-Based Scheduling & Workload Allocation")

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Simulation Configuration")
    
    scheduling_method = st.selectbox(
        "First-Level Scheduling",
        ["FCFS", "Weighted Priority-Based"],
        index=1,
        help="How requests are ordered in the queue"
    )
    
    allocation_method = st.selectbox(
        "Second-Level Allocation",
        [
            "College-Based Assignment",
            "Workload-Based Assignment with College Affiliation",
            "Pooled Scheduling",
            "Quota-Free Allocation"
        ],
        index=1,
        help="How requests are assigned to staff"
    )
    
    scenario = st.selectbox(
        "Simulation Scenario",
        ["Baseline", "Staff Absence", "Peak Urgency", "Workload Imbalance"],
        index=0,
        help="Operational condition to simulate"
    )
    
    duration = st.slider("Duration (minutes)", 30, 180, 60, 30)


    # 👇 NEW: Load auto-generated requests into queue
    if st.button("📥 Load Scenario Queue", type="secondary", use_container_width=True):
        with st.spinner("Generating auto-requests based on config..."):
            try:
                res = requests.post(
                    "http://localhost:5000/api/queue/load-scenario",
                    json={
                        "scheduler": scheduling_method,
                        "allocator": allocation_method,
                        "scenario": scenario,
                        "duration_minutes": duration
                    },
                    timeout=15
                )
                if res.status_code == 200:
                    count = res.json()['count']
                    st.success(f"✅ Loaded {count} auto-generated requests!")
                    st.session_state.show_queue = True
                    st.rerun()
                else:
                    st.error("Failed to load queue")
            except Exception as e:
                st.error(f"Connection error: {e}")

    st.divider()
    st.subheader("📝 Manual Request Entry")
    with st.form("manual_request_form"):
        manual_college = st.selectbox("College", ['COE', 'CAS', 'CBA', 'CEGE', 'CS', 'IE'])
        manual_doc = st.selectbox("Document Type", [
            'Transcript of Records', 'Certificate of Enrollment', 
            'Honorable Dismissal', 'Certification'
        ])
        manual_urgency = st.slider("Urgency (1-10)", 1, 10, 5)
        manual_req_type = st.selectbox("Requester Type", [
            'Graduating Student', 'Enrolling Student', 
            'Faculty', 'Alumni', 'Regular Student'
        ])
        submit_manual = st.form_submit_button("➕ Add to Queue", type="secondary")
        
        if submit_manual:
            try:
                res = requests.post(
                    "http://localhost:5000/api/queue/add",
                    json={
                        "college": manual_college,
                        "document_type": manual_doc,
                        "urgency": manual_urgency,
                        "requester_type": manual_req_type,
                        "scheduler": scheduling_method
                    },
                    timeout=10
                )
                if res.status_code == 200:
                    data = res.json()
                    st.success(f"✅ Added! Position: #{data['position']}")
                    st.session_state.show_queue = True
                else:
                    st.error("Failed to add request")
            except Exception as e:
                st.error(f"Connection error: {e}")

    

    with st.expander("🛠️ Advanced Settings", expanded=False):
        enable_custom_staff = st.checkbox("Customize Staff Count", value=False)
        if enable_custom_staff:
            num_staff = st.slider("Number of Staff", min_value=1, max_value=20, value=6, step=1)
            advanced_settings = {
                "enable_custom_staff": True,
                "num_staff": num_staff
            }
        else:
            advanced_settings = {"enable_custom_staff": False}

    queue_source = "🔄 Generating fresh auto-requests"
    use_queue_flag = False
    try:
        q_res = requests.get("http://localhost:5000/api/queue/status", timeout=5)
        if q_res.status_code == 200:
            q_count = q_res.json()['total_in_queue']
            if q_count > 0:
                use_queue_flag = True
                queue_source = f"✅ Using {q_count} requests from Active Queue"
    except:
        pass

    st.info(queue_source, icon="ℹ️")

    
    if st.button("Run Simulation", type="primary", use_container_width=True):
        with st.spinner("Running REAL simulation with your algorithms..."):
            try:
                response = requests.post(
                    "http://localhost:5000/api/simulate",
                    json={
                        "scheduler": scheduling_method,
                        "allocator": allocation_method,
                        "scenario": scenario,   
                        "duration_minutes": duration,
                        "use_active_queue": use_queue_flag, 
                        "advanced_settings": advanced_settings
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    st.session_state.simulation_data = response.json()
                    st.session_state.last_run = datetime.now().strftime("%H:%M:%S")
                    st.session_state.last_config = {
                        "scheduler": scheduling_method,
                        "allocator": allocation_method,
                        "scenario": scenario,
                        "advanced_settings": advanced_settings
                    }
                    st.success("Simulation completed with REAL algorithm data!")
                else:
                    st.error(f"Simulation failed: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to backend. Is Flask server running on port 5000?")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Main content
if 'simulation_data' not in st.session_state:
    st.info("Configure parameters in sidebar and click **Run Simulation** to see REAL metrics from your algorithms")
    
    # Show what real data looks like
    st.markdown("### Expected Output:")
    st.markdown("""
    - **Avg Waiting Time**: Calculated from `(completion_time - submission_time)` for all requests
    - **Avg Turnaround**: Total processing time including queue wait
    - **Throughput**: `total_processed / simulation_duration_hours`
    - **Staff Load**: Real workload distribution from your allocator logic
    """)
    
    st.markdown("#### Example Real Metrics (from Priority + Workload-Based):")
    example_df = pd.DataFrame({
        'Metric': ['Avg Waiting Time', 'Avg Turnaround', 'Throughput', 'Total Processed'],
        'Value': ['8.2 min', '12.5 min', '24.3/hr', '189 requests'],
        'Source': [
            'Computed from request timestamps',
            'Waiting time + processing time',
            'Requests per simulation hour',
            'Count of completed requests'
        ]
    })
    st.dataframe(example_df, use_container_width=True)
    
else:
    # Display real metrics
    metrics = st.session_state.simulation_data
    
    # Scenario tag
    scenario_class = scenario.lower().replace(" ", "-")
    st.markdown(f'<span class="scenario-tag {scenario_class}">Scenario: {scenario}</span>', unsafe_allow_html=True)
    
    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Avg Waiting Time", f"{metrics['avg_waiting_time']:.1f} min")
    with col2:
        st.metric("Avg Turnaround", f"{metrics['avg_turnaround']:.1f} min")
    with col3:
        st.metric("Throughput", f"{metrics['throughput']:.1f}/hr")
    with col4:
        st.metric("Total Processed", metrics['total_processed'])
    
    # Staff workload distribution
    st.subheader("👥 Staff Workload Distribution (REAL DATA)")
    if 'staff_load' in metrics and metrics['staff_load']:
        workload_df = pd.DataFrame({
            'Staff ID': list(metrics['staff_load'].keys()),
            'Workload': list(metrics['staff_load'].values())
        })
        
        col_chart, col_table = st.columns([2, 1])
        with col_chart:
            fig = px.bar(
                workload_df,
                x='Staff ID',
                y='Workload',
                color='Workload',
                color_continuous_scale='Blues',
                labels={'Workload': 'Requests Processed', 'Staff ID': 'Staff Member'},
                text='Workload'
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_table:
            st.dataframe(workload_df, use_container_width=True, hide_index=True)
    
    # Raw data for verification
    with st.expander("🔍 View Raw Simulation Data (for panel verification)"):
        st.json(metrics)
    
    # Algorithm summary
    st.markdown("---")
    st.markdown("### Simulation Configuration Used")
    config = st.session_state.last_config
    st.markdown(f"""
    - **Scheduling Method**: `{config['scheduler']}`
    - **Allocation Method**: `{config['allocator']}`
    - **Scenario**: `{config['scenario']}`
    - **Duration**: `{duration} minutes`
    - **Run Time**: `{st.session_state.last_run}`
    """)

    # Queue Viewer Toggle
    st.toggle("👁️ Show Live Queue", key="show_queue", value=st.session_state.get('show_queue', False))
    
    if st.session_state.get('show_queue', False):
        try:
            queue_res = requests.get("http://localhost:5000/api/queue/status", timeout=10)
            if queue_res.status_code == 200:
                q_data = queue_res.json()
                if q_data['total_in_queue'] > 0:
                    df = pd.DataFrame(q_data['queue'])
                    
                    # Highlight manual row
                    def highlight_manual(row):
                        if row['Is Manual']:
                            return ['background-color: #fff3cd; font-weight: bold; border-left: 3px solid #ffc107;'] * len(row)
                        return [''] * len(row)
                        
                    st.dataframe(
                        df.style.apply(highlight_manual, axis=1),
                        hide_index=True,
                        use_container_width=True,
                        height=400
                    )
                    
                    col_a, col_b = st.columns([1, 3])
                    with col_a:
                        if st.button("🗑️ Clear Queue", use_container_width=True):
                            requests.post("http://localhost:5000/api/queue/clear", timeout=10)
                            st.session_state.show_queue = False
                            st.rerun()
                    with col_b:
                        st.caption(f"Scheduler: {q_data['scheduler']} | Total: {q_data['total_in_queue']}")
                else:
                    st.info("Queue is empty. Add a manual request to see it here.")
        except Exception as e:
            st.error(f"Failed to fetch queue: {e}")

# Footer
st.markdown("---")
st.markdown(
    f"<div style='text-align: center; color: #666; font-size: 0.9em;'>"
    f"Thesis Project • B.S. Computer Science • MSU-IIT • {datetime.now().year}<br>"
    f"Evaluating Priority-Based Scheduling and Workload Allocation in an Online Registrar Document Request System"
    f"</div>",
    unsafe_allow_html=True
)