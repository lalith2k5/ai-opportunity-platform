#!/bin/bash
ROOT="$HOME/ai-opportunity-platform"
PID_DIR="$ROOT/handoff/pids"

GREEN="\033[0;32m"; RED="\033[0;31m"; YELLOW="\033[0;33m"; RESET="\033[0m"

check_service() {
  local name="$1" pidfile="$PID_DIR/$1.pid"
  if [ -f "$pidfile" ] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
    echo -e "  ${GREEN}●${RESET} $name — running (pid $(cat "$pidfile"))"
  else
    echo -e "  ${RED}○${RESET} $name — stopped"
  fi
}

echo "=== AI Opportunity Platform status ==="
check_service backend
check_service frontend
check_service caddy

echo
echo "Ports:"
for entry in "8000:backend API" "5173:frontend" "8443:HTTPS (caddy)"; do
  port="${entry%%:*}"
  label="${entry#*:}"
  pid=$(lsof -ti :$port 2>/dev/null || true)
  if [ -n "$pid" ]; then
    echo -e "  ${GREEN}●${RESET} $port ($label) — pid $pid"
  else
    echo -e "  ${YELLOW}○${RESET} $port ($label) — free"
  fi
done

echo
echo "Backend health:"
if curl -sf http://localhost:8000/api/health 2>/dev/null | python3 -m json.tool 2>/dev/null; then
  :
else
  echo "  (backend not responding)"
fi

echo
echo "Postgres:"
pg_isready 2>/dev/null && echo -e "  ${GREEN}●${RESET} accepting connections" || echo -e "  ${RED}○${RESET} not running"
