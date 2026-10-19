#!/bin/bash
# Polls Gemini quota every 10 min. When available, runs all 3 backfills in order.
# Logs everything to /tmp/watcher.log

cd ~/ai-opportunity-platform/backend
source venv/bin/activate

LOG=/tmp/watcher.log
echo "[$(date)] watcher started" >> "$LOG"

probe_quota() {
  python3 - <<'PYEOF' 2>/dev/null
from app.services.llm_service import LLMService
r = LLMService().generate("ok")
ok = not (r.startswith("All LLM providers failed") or r.startswith("AI service not configured"))
print("YES" if ok else "NO")
PYEOF
}

attempt=0
while true; do
  attempt=$((attempt + 1))
  result=$(probe_quota)
  echo "[$(date)] attempt $attempt -> $result" >> "$LOG"
  if [ "$result" = "YES" ]; then
    echo "[$(date)] QUOTA AVAILABLE -- launching backfills" >> "$LOG"
    nohup python3 -u backfill_d1_fields.py > /tmp/backfill_d1.log 2>&1 &
    echo $! > /tmp/backfill_d1.pid
    nohup python3 -u backfill_d3b_organizations.py > /tmp/backfill_d3b.log 2>&1 &
    echo $! > /tmp/backfill_d3b.pid
    nohup python3 -u backfill_enrichment.py > /tmp/backfill.log 2>&1 &
    echo $! > /tmp/backfill.pid
    echo "[$(date)] all 3 backfills launched -- watcher exiting" >> "$LOG"
    exit 0
  fi
  sleep 600
done
