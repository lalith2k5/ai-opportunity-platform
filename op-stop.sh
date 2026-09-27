#!/bin/bash
# Stop backend, frontend, caddy (Postgres keeps running)

ROOT="$HOME/ai-opportunity-platform"
PID_DIR="$ROOT/handoff/pids"

GREEN="\033[0;32m"; YELLOW="\033[0;33m"; RESET="\033[0m"

stop_service() {
  local name="$1" pidfile="$PID_DIR/$1.pid"
  if [ ! -f "$pidfile" ]; then
    echo -e "${YELLOW}[skip]${RESET} $name — no pidfile"
    return
  fi
  local pid=$(cat "$pidfile")
  if kill -0 "$pid" 2>/dev/null; then
    # Kill the process group so child procs die too
    kill -TERM -"$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null
    sleep 1
    kill -KILL "$pid" 2>/dev/null || true
    echo -e "${GREEN}[stop]${RESET} $name (pid $pid)"
  else
    echo -e "${YELLOW}[skip]${RESET} $name — not running"
  fi
  rm -f "$pidfile"
}

echo "=== Stopping AI Opportunity Platform ==="
stop_service "frontend"
stop_service "caddy"
stop_service "backend"

# Safety net: kill anything still on the ports
for port in 8000 5173 8443; do
  pid=$(lsof -ti :$port 2>/dev/null || true)
  if [ -n "$pid" ]; then
    echo -e "${YELLOW}[clean]${RESET} killing stray process on port $port (pid $pid)"
    kill -KILL "$pid" 2>/dev/null || true
  fi
done

echo
echo "Postgres still running. Stop it with:  brew services stop postgresql@17"
