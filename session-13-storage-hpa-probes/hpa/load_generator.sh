#!/usr/bin/env bash
# ==============================================================================
# Script: load_generator.sh
# Purpose: Spawns high-concurrency background curl requests to trigger HPA scaling
# ==============================================================================

set -euo pipefail

# Local port for the port-forward. Defaults to 5000 as in the course; override it
# when 5000 is busy, e.g. LOCAL_PORT=18101 ./load_generator.sh
LOCAL_PORT="${LOCAL_PORT:-5000}"
TARGET_URL="${1:-http://localhost:${LOCAL_PORT}/healthz}"

echo "=================================================="
echo "      KUBERNETES HPA TRAFFIC LOAD GENERATOR       "
echo "=================================================="
echo "Pounding target endpoint: $TARGET_URL"
echo "Simulating traffic spike. Press Ctrl+C to stop."
echo ""

# Stop the port-forward and every worker loop when the script exits or is stopped.
# (The original trap only killed the port-forward, so the curl loops kept running
# when the script was terminated with kill instead of Ctrl+C.)
trap 'kill $(jobs -p) 2>/dev/null || true' EXIT INT TERM

# Forward local port if needed
if ! curl -s -f "$TARGET_URL" > /dev/null 2>&1; then
    echo "Starting port-forward to yatri-backend-service on port ${LOCAL_PORT}..."
    kubectl port-forward svc/yatri-backend-service "${LOCAL_PORT}:80" > /dev/null 2>&1 &
    sleep 2
fi

# Run 10 parallel background workers firing requests in an infinite loop
for i in {1..10}; do
    while true; do
        curl -s "$TARGET_URL" > /dev/null || true
    done &
done

echo "Traffic load active! In another terminal, run: kubectl get hpa -w"
wait
