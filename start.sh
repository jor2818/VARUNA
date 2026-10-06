#!/bin/bash
echo "============================================================"
echo " 🚦 Starting VARUNA Traffic Insights Application Suite"
echo "============================================================"

# Start Flask Backend in background
python app.py &
FLASK_PID=$!
echo "[1/2] Flask server launched on http://localhost:5000 (PID: $FLASK_PID)"

# Start Streamlit Dashboard in background
python -m streamlit run dashboard.py --server.port 8501 --server.headless true &
STREAMLIT_PID=$!
echo "[2/2] Streamlit server launched on http://localhost:8501 (PID: $STREAMLIT_PID)"

echo "============================================================"
echo " 🎉 Both services are running!"
echo "  - Flask Web App: http://localhost:5000"
echo "  - Streamlit Dashboard: http://localhost:8501"
echo " Press Ctrl+C to stop both servers."
echo "============================================================"

cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $FLASK_PID 2>/dev/null
    kill $STREAMLIT_PID 2>/dev/null
    echo "Servers stopped."
    exit 0
}

trap cleanup SIGINT SIGTERM

wait
