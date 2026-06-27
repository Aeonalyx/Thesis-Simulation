"""
run.py
Runs both the Flask API backend (api.py) and the Streamlit frontend (frontend/app.py) concurrently.
Handles clean shutdown on Ctrl+C.
"""

import os
import sys
import time
import subprocess

def main():
    # Detect the current Python executable
    python_exe = sys.executable
    print(f"Using Python executable: {python_exe}")
    
    # Verify file existence before running
    if not os.path.exists("api.py"):
        print("Error: api.py not found in the root directory!")
        sys.exit(1)
    if not os.path.exists(os.path.join("frontend1", "app1.py")):
        print("Error: frontend/app.py not found!")
        sys.exit(1)

    print("Starting Flask API and Streamlit Frontend concurrently...")
    print("Press Ctrl+C to stop both servers.")
    print("-" * 60)

    # Command lines
    flask_cmd = [python_exe, "api.py"]
    streamlit_cmd = [python_exe, "-m", "streamlit", "run", "frontend1/app1.py"]

    # Start Flask API
    flask_proc = subprocess.Popen(
        flask_cmd,
        stdout=None,  
        stderr=None,  
    )
    
    time.sleep(1.5)

    # Start Streamlit
    streamlit_proc = subprocess.Popen(
        streamlit_cmd,
        stdout=None,
        stderr=None,
    )

    try:
        while True:
            # Poll status of Flask process
            flask_status = flask_proc.poll()
            if flask_status is not None:
                print(f"\n[System] Flask API exited unexpectedly with code {flask_status}")
                break

            # Poll status of Streamlit process
            streamlit_status = streamlit_proc.poll()
            if streamlit_status is not None:
                print(f"\n[System] Streamlit Frontend exited unexpectedly with code {streamlit_status}")
                break

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[System] Ctrl+C detected. Terminating servers...")

    finally:
        # Gracefully terminate Flask API
        if flask_proc.poll() is None:
            print("[System] Terminating Flask API...")
            flask_proc.terminate()
            try:
                flask_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                print("[System] Killing Flask API forcefully...")
                flask_proc.kill()

        # Gracefully terminate Streamlit Frontend
        if streamlit_proc.poll() is None:
            print("[System] Terminating Streamlit Frontend...")
            streamlit_proc.terminate()
            try:
                streamlit_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                print("[System] Killing Streamlit Frontend forcefully...")
                streamlit_proc.kill()

    print("[System] Both servers stopped.")

if __name__ == "__main__":
    main()
