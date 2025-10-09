#!/usr/bin/env bash
set -e

cd "$REPO_ROOT/batpad/djbatpad/frontend"
echo "Starting Vite server..."
yarn dev &
VITE_PID=$!

cd "$REPO_ROOT/batpad/djbatpad"
echo "Starting Django server..."
uv run manage.py runserver &
DJANGO_PID=$!

cd "$REPO_ROOT/thirdman/simgen/app"
echo "Starting FastAPI server..."
uv run fastapi dev main.py --reload --port 8010 &
FASTAPI_PID=$!

cleanup() {
  echo "Shutting down servers..."
  kill $VITE_PID 2>/dev/null || true
  kill $DJANGO_PID 2>/dev/null || true
  kill $FASTAPI_PID 2>/dev/null || true
  wait $VITE_PID 2>/dev/null || true
  wait $DJANGO_PID 2>/dev/null || true
  wait $FASTAPI_PID 2>/dev/null || true
}

trap cleanup EXIT INT TERM

wait

