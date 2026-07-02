"""Start the backend API and Streamlit frontend together."""

import signal
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def start_process(command):
    return subprocess.Popen(command, cwd=str(ROOT))


def main():
    backend = start_process([sys.executable, "backend/api.py"])
    time.sleep(1.0)
    frontend = start_process([sys.executable, "-m", "streamlit", "run", "frontend/app.py"])

    processes = [backend, frontend]

    def stop_all(*_):
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

    signal.signal(signal.SIGINT, stop_all)
    signal.signal(signal.SIGTERM, stop_all)

    try:
        while all(process.poll() is None for process in processes):
            time.sleep(0.5)
    finally:
        stop_all()


if __name__ == "__main__":
    main()
