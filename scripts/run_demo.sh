#!/usr/bin/env bash
# scripts/run_demo.sh - Local Orchestration Demo Runner for FedMed
# Owner: M1 (Server & Orchestration Lead)
# Launches: Flower Server + 3 Hospital Client Nodes + FastAPI Backend + React Dashboard

set -e

echo "================================================================="
echo "                FedMed Cross-Silo FL Demo Runner                 "
echo "================================================================="

# Trap cleanup on exit / Ctrl+C
PIDS=()
cleanup() {
    echo ""
    echo "[FedMed Runner] Shutting down all services..."
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    echo "[FedMed Runner] All processes terminated."
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 1. Start Flower Central Server
echo "[1/6] Launching Central Flower Orchestrator (port 8080)..."
python -m server.server --port 8080 --rounds 5 --encrypted &
PIDS+=($!)
sleep 2

# 2. Start FastAPI Backend & Telemetry WebSocket
echo "[2/6] Launching FastAPI Telemetry & Scan Service (port 8000)..."
uvicorn api.main:app --host 0.0.0.0 --port 8000 &
PIDS+=($!)
sleep 1

# 3. Start Hospital Silo 1 (St. Jude)
echo "[3/6] Launching Hospital Node 1 (St. Jude Medical - Aux Port 8081)..."
python -m client.client --node-id 1 --port 8081 --server-address 127.0.0.1:8080 &
PIDS+=($!)
sleep 1

# 4. Start Hospital Silo 2 (Charité)
echo "[4/6] Launching Hospital Node 2 (Charité Berlin - Aux Port 8082)..."
python -m client.client --node-id 2 --port 8082 --server-address 127.0.0.1:8080 &
PIDS+=($!)
sleep 1

# 5. Start Hospital Silo 3 (Mayo Clinic)
echo "[5/6] Launching Hospital Node 3 (Mayo Clinic Oncology - Aux Port 8083)..."
python -m client.client --node-id 3 --port 8083 --server-address 127.0.0.1:8080 &
PIDS+=($!)
sleep 1

# 6. Start React + Vite Frontend Dashboard
echo "[6/6] Launching Frontend Dashboard (port 3000)..."
(cd dashboard && npm run dev) &
PIDS+=($!)

echo ""
echo "================================================================="
echo "   All FedMed Services Running Successfully!                    "
echo "================================================================="
echo "   - Dashboard UI:       http://localhost:3000                  "
echo "   - API Documentation:  http://localhost:8000/docs             "
echo "   - WebSocket Stream:   ws://localhost:8000/ws/telemetry       "
echo "   - Flower Server:      localhost:8080                         "
echo "================================================================="
echo "Press Ctrl+C to stop all services."

# Wait indefinitely
wait
