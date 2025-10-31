#!/bin/bash
set -e

# Start label-studio in the background
label-studio start --host 0.0.0.0 --port 8080 &
LS_PID=$!

# Wait for label-studio to be ready
echo "Waiting for Label Studio to start..."
until curl -fsS http://127.0.0.1:8080/ >/dev/null 2>&1; do
  sleep 1
done
echo "Label Studio is ready!"

# Install dependencies and run setup
echo "Running setup script..."
pip install label-studio-sdk >/dev/null 2>&1
python3 /app/setup.py

echo "Setup complete! Label Studio is running at http://127.0.0.1:8080"

# Keep the container alive
wait $LS_PID

