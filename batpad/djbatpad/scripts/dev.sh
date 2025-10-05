set -euxo pipefail

ROOT_DIR="$REPO_ROOT/batpad/djbatpad"
DJANGO_PORT="${DJANGO_PORT:-8000}"
VITE_PORT="${VITE_PORT:-5173}"

cd "$ROOT_DIR/frontend"

if [ ! -d node_modules ]; then
  echo "[frontend] installing dependencies..."
  yarn install --silent
fi

echo "[frontend] starting Vite on :$VITE_PORT"
yarn dev --port "$VITE_PORT" --strictPort --host localhost &
VITE_PID=$!

cleanup() {
  echo "[frontend] stopping Vite (pid $VITE_PID)"
  kill "$VITE_PID" 2>/dev/null || true
  wait "$VITE_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

cd "$ROOT_DIR"
echo "[django] starting Django on :$DJANGO_PORT"
PYTHON_BIN="${PYTHON:-python}"
"$PYTHON_BIN" manage.py runserver "$DJANGO_PORT"


