#!/usr/bin/env bash

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT=8080

echo "=========================================================="
echo " Starting Autoscaling (HPA) Live Load Test"
echo "=========================================================="

# Kill any stale port-forward on port 8080
lsof -ti :$PORT | xargs kill -9 2>/dev/null || true

# Start clean port-forward directly to the Kubernetes service
kubectl port-forward svc/flask-service $PORT:5000 >/dev/null 2>&1 &
PF_PID=$!
trap "kill -9 $PF_PID 2>/dev/null || true" EXIT

# Give port-forward 2 seconds to bind
sleep 2

echo -e "\n>>> 1. Initial State (Before Load):"
kubectl get hpa flask-hpa 2>/dev/null || true
kubectl get pods -l app=flask-app 2>/dev/null || true

echo -e "\n>>> 2. Launching connection-pooled load test..."
python3 "$DIR/scripts/load_test.py" "http://127.0.0.1:$PORT/" 60 120 &
LOAD_PID=$!

echo -e "\n>>> 3. Watching HPA & Pods scale out live..."
for i in $(seq 1 20); do
    sleep 6
    echo -e "\n--- [T + $((i*6))s] ---"
    kubectl get hpa flask-hpa 2>/dev/null || true
    kubectl get pods -l app=flask-app 2>/dev/null || true
done

wait $LOAD_PID
echo -e "\n=========================================================="
echo " Load test complete! Final cluster scaling state:"
echo "=========================================================="
kubectl get hpa flask-hpa 2>/dev/null || true
kubectl get pods -l app=flask-app 2>/dev/null || true
