import sys
import subprocess
import time
import os

# Set stdout/stderr encoding to utf-8 if possible
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=" * 60)
    print(" Starting VARUNA Traffic Insights Application Suite")
    print("=" * 60)
    
    python_exe = sys.executable
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    flask_cmd = [python_exe, os.path.join(base_dir, "app.py")]
    streamlit_cmd = [
        python_exe, "-m", "streamlit", "run", 
        os.path.join(base_dir, "dashboard.py"), 
        "--server.port", "8501", 
        "--server.headless", "true"
    ]

    print("\n[1/2] Launching Flask Backend on http://localhost:5000...")
    flask_proc = subprocess.Popen(flask_cmd, cwd=base_dir)

    time.sleep(2)

    print("\n[2/2] Launching Streamlit Dashboard on http://localhost:8501...")
    streamlit_proc = subprocess.Popen(streamlit_cmd, cwd=base_dir)

    print("\n" + "=" * 60)
    print(" Both services are up and running!")
    print("  - Flask Web App & REST API: http://localhost:5000")
    print("  - Streamlit Data Dashboard: http://localhost:8501")
    print(" Press Ctrl+C to terminate both servers.")
    print("=" * 60 + "\n")

    try:
        while True:
            if flask_proc.poll() is not None:
                print(" Flask process exited unexpectedly.")
                break
            if streamlit_proc.poll() is not None:
                print(" Streamlit process exited unexpectedly.")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n Shutting down servers gracefully...")
    finally:
        if flask_proc.poll() is None:
            flask_proc.terminate()
            flask_proc.wait()
        if streamlit_proc.poll() is None:
            streamlit_proc.terminate()
            streamlit_proc.wait()
        print(" All servers stopped successfully.")

if __name__ == "__main__":
    main()
