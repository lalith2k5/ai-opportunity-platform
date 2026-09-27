#!/bin/bash
# Start the AI Opportunity Platform: Postgres + backend + frontend + caddy

ROOT="$HOME/ai-opportunity-platform"
PID_DIR="$ROOT/handoff/pids"
LOG_DIR="$ROOT/backend/logs"
mkdir -p "$PID_DIR" "$LOG_DIR"

GREEN="\033[0;32m"; YELLOW="\033[0;33m"; RED="\033[0;31m"; RESET="\033[0m"

is_running() {
  local pidfile="$1"
  [ -f "$pidfile" ] && kill -0 "$(cat "$pidfile")" 2>/dev/null
}

start_service() {
  local name="$1"
  local dir="$2"
  local cmd="$3"
  local pidfile="$PID_DIR/$name.pid"
  local logfile="$LOG_DIR/$name.log"
  if is_running "$pidfile"; then
    echo -e "${YELLOW}[skip]${RESET} $name already running (pid $(cat "$pidfile"))"
    return 0
  fi
  cd "$dir" || { echo -e "${RED}[fail]${RESET} cannot cd to $dir"; return 1; }
  nohup bash -c "$cmd" > "$logfile" 2>&1 &
  local child_pid=$!
  echo "$child_pid" > "$pidfile"
  echo -e "${GREEN}[start]${RESET} $name (pid $child_pid) — log: $logfile"
}

echo "=== Starting AI Opportunity Platform ==="
echo

# 1. Postgres
if ! pg_isready -q 2>/dev/null; then
  echo "[start] PostgreSQL…"
  brew services start postgresql@17 >/dev/null 2>&1 || true
  for i in {1..15}; do
    pg_isready -q 2>/dev/null && break
    sleep 1
  done
fi
pg_isready -q 2>/dev/null && echo -e "${GREEN}[ok]${RESET} PostgreSQL ready" || echo -e "${RED}[fail]${RESET} PostgreSQL not ready"

# 2. Backend
start_service "backend" "$ROOT/backend" "source venv/bin/activate && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"

# 3. Frontend
start_service "frontend" "$ROOT/frontend" "exec npm run dev"

# 4. Caddy
if command -v caddy >/dev/null 2>&1; then
  start_service "caddy" "$ROOT/caddy" "exec caddy run --config Caddyfile.local --adapter caddyfile"
else
  echo -e "${YELLOW}[skip]${RESET} caddy not installed — HTTPS at :8443 unavailable"
fi

echo
echo "Waiting for backend to respond…"
for i in {1..45}; do
  if curl -sf http://localhost:8000/api/health >/dev/null 2>&1; then
    echo -e "${GREEN}[ok]${RESET} Backend healthy after ${i}s"
    break
  fi
  sleep 1
  [ $i -eq 45 ] && echo -e "${RED}[fail]${RESET} Backend did not become healthy in 45s — check logs"
done

echo
echo "=== Ready ==="
echo "  Frontend:  http://localhost:5173"
echo "  HTTPS:     https://localhost:8443  (if caddy started)"
echo "  API docs:  http://localhost:8000/docs"
echo
echo "  Stop:      op-stop"
echo "  Status:    op-status"
echo "  Logs:      op-logs"
