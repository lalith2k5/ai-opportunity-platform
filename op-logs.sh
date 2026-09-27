#!/bin/bash
ROOT="$HOME/ai-opportunity-platform"
LOG_DIR="$ROOT/backend/logs"

which_log="${1:-all}"

case "$which_log" in
  backend)  tail -f "$LOG_DIR/backend.log" ;;
  frontend) tail -f "$LOG_DIR/frontend.log" ;;
  caddy)    tail -f "$LOG_DIR/caddy.log" ;;
  all)
    echo "Tailing all logs (Ctrl+C to exit)"
    tail -f "$LOG_DIR/backend.log" "$LOG_DIR/frontend.log" "$LOG_DIR/caddy.log" 2>/dev/null
    ;;
  *)
    echo "Usage: op-logs [backend|frontend|caddy|all]"
    exit 1
    ;;
esac
