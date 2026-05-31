#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$PROJECT_DIR/backend"
FRONTEND="$PROJECT_DIR/frontend"

echo "=== WorldPress Setup ==="

# ── Backend ────────────────────────────────────────────────────────────────
echo "[1/4] Installing Python dependencies..."
cd "$BACKEND"
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate
pip install -q -r requirements.txt

echo "[2/4] Initialising database..."
python init_db.py

echo "[3/4] Starting backend on http://localhost:5000 ..."
python app.py &
BACKEND_PID=$!

# ── Frontend ───────────────────────────────────────────────────────────────
cd "$FRONTEND"
if [ ! -d node_modules ]; then
  echo "[4/4] Installing npm packages (first run)..."
  npm install
fi

echo "[4/4] Starting frontend on http://localhost:3000 ..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "==================================="
echo "  WorldPress is running!"
echo "  Frontend : http://localhost:3000"
echo "  Backend  : http://localhost:5000"
echo "  Admin    : check env vars WP_ADMIN_USER / WP_ADMIN_PASS for credentials"
echo "==================================="

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
