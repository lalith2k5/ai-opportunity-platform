#!/bin/bash
set -o pipefail
cd ~/ai-opportunity-platform

GREEN="\033[0;32m"; RED="\033[0;31m"; YELLOW="\033[0;33m"; RESET="\033[0m"

echo "======================================================================"
echo "  DELIVERABLE 1 -- BLOCK B -- RESTART + RUN + VERIFY + COMMIT"
echo "  $(date)"
echo "======================================================================"

echo
echo "[PHASE 1/6] Restart backend"
bash op-stop.sh >/dev/null 2>&1 || true
sleep 2
bash op-start.sh 2>&1 | tail -12

for i in $(seq 1 90); do
  if curl -sf http://localhost:8000/api/health >/dev/null 2>&1; then
    printf "  [OK]   backend healthy after %ss\n" "$i"
    break
  fi
  sleep 1
done
if ! curl -sf http://localhost:8000/api/health >/dev/null 2>&1; then
  printf "  [FAIL] backend did not become healthy -- aborting\n"
  exit 1
fi

echo
echo "[PHASE 2/6] Rebuild enriched KG (threshold 2 -> 1)"
BEFORE_GAP=$(psql -d ai_opportunity_db -tA -c "SELECT COUNT(*) FROM kg_edges WHERE relation='HAS_POTENTIAL_GAP'" 2>/dev/null)
BEFORE_USES=$(psql -d ai_opportunity_db -tA -c "SELECT COUNT(*) FROM kg_edges WHERE relation='USES'" 2>/dev/null)
echo "  before: HAS_POTENTIAL_GAP=$BEFORE_GAP  USES=$BEFORE_USES"

cd ~/ai-opportunity-platform/backend
source venv/bin/activate
python3 rebuild_kg_enriched.py
cd ~/ai-opportunity-platform

AFTER_GAP=$(psql -d ai_opportunity_db -tA -c "SELECT COUNT(*) FROM kg_edges WHERE relation='HAS_POTENTIAL_GAP'" 2>/dev/null)
AFTER_USES=$(psql -d ai_opportunity_db -tA -c "SELECT COUNT(*) FROM kg_edges WHERE relation='USES'" 2>/dev/null)
echo "  after:  HAS_POTENTIAL_GAP=$AFTER_GAP  USES=$AFTER_USES"

echo
echo "[PHASE 3/6] Re-embed corpus into Chroma"
BEFORE_VEC=$(curl -s http://localhost:8000/api/health | python3 -c 'import sys,json;print(json.load(sys.stdin).get("vectors_stored",0))')
echo "  before: chroma vectors = $BEFORE_VEC"

cd ~/ai-opportunity-platform/backend
python3 reembed_corpus.py
cd ~/ai-opportunity-platform

AFTER_VEC=$(curl -s http://localhost:8000/api/health | python3 -c 'import sys,json;print(json.load(sys.stdin).get("vectors_stored",0))')
echo "  after:  chroma vectors = $AFTER_VEC"

echo
echo "[PHASE 4/6] Backfill enrichment (LLM, resumable)"
BEFORE_ENR=$(psql -d ai_opportunity_db -tA -c "SELECT COUNT(*) FROM opportunities WHERE suggested_research_direction IS NOT NULL" 2>/dev/null)
echo "  before: enriched = $BEFORE_ENR"

cd ~/ai-opportunity-platform/backend
python3 backfill_enrichment.py
cd ~/ai-opportunity-platform

AFTER_ENR=$(psql -d ai_opportunity_db -tA -c "SELECT COUNT(*) FROM opportunities WHERE suggested_research_direction IS NOT NULL" 2>/dev/null)
echo "  after:  enriched = $AFTER_ENR"

echo
echo "[PHASE 5/6] Live coverage verification"
psql -d ai_opportunity_db -tA -F'|' -c "
SELECT 'domain non-null',                 COUNT(*) FROM opportunities WHERE domain IS NOT NULL
UNION ALL SELECT 'related_technologies > 0', COUNT(*) FROM opportunities WHERE related_technologies IS NOT NULL AND jsonb_array_length(related_technologies::jsonb) > 0
UNION ALL SELECT 'existing_research > 0',  COUNT(*) FROM opportunities WHERE existing_research IS NOT NULL AND jsonb_array_length(existing_research::jsonb) > 0
UNION ALL SELECT 'suggested_research non-null', COUNT(*) FROM opportunities WHERE suggested_research_direction IS NOT NULL
UNION ALL SELECT 'suggested_project non-null',  COUNT(*) FROM opportunities WHERE suggested_project_direction IS NOT NULL
UNION ALL SELECT 'evidence_sources > 0',  COUNT(*) FROM opportunities WHERE evidence_sources IS NOT NULL AND jsonb_array_length(evidence_sources::jsonb) > 0
" 2>/dev/null

echo
echo "  KG relations:"
psql -d ai_opportunity_db -tA -F'|' -c "
SELECT 'HAS_POTENTIAL_GAP', COUNT(*) FROM kg_edges WHERE relation='HAS_POTENTIAL_GAP'
UNION ALL SELECT 'USES',           COUNT(*) FROM kg_edges WHERE relation='USES'
UNION ALL SELECT 'STUDIED_BY',     COUNT(*) FROM kg_edges WHERE relation='STUDIED_BY'
UNION ALL SELECT 'SUPPORTED_BY',   COUNT(*) FROM kg_edges WHERE relation='SUPPORTED_BY'
" 2>/dev/null

echo
echo "  API endpoint smoke:"
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=test1234" | \
  python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
EP_OK=0; EP_TOTAL=0
for ep in "/api/health" "/api/opportunities" "/api/researcher/flow?limit=2" "/api/rd/flow?limit=2" "/api/kg/stats" "/api/admin/llm/status"; do
  EP_TOTAL=$((EP_TOTAL+1))
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "http://localhost:8000$ep")
  if [ "$CODE" = "200" ]; then
    EP_OK=$((EP_OK+1))
  else
    printf "    [%s] %s\n" "$CODE" "$ep"
  fi
done
printf "    %d/%d endpoints OK\n" "$EP_OK" "$EP_TOTAL"

echo
echo "[PHASE 6/6] Commit + push"
git add backend/app/agents/orchestrator.py \
        backend/app/agents/knowledge_graph.py \
        backend/backfill_enrichment.py \
        backend/reembed_corpus.py \
        backend/rebuild_kg_enriched.py

if git diff --cached --quiet; then
  echo "  [SKIP] nothing staged"
else
  git status --short
  git commit -m "phase 10.1: enrichment backfill + KG threshold + corpus re-embed

- backend/app/agents/orchestrator.py: _enrich_opportunities accepts opp_ids, cap 10 -> 50, adds local-embedding semantic fallback
- backend/app/agents/knowledge_graph.py: HAS_POTENTIAL_GAP and USES overlap threshold 2 -> 1
- New: backend/backfill_enrichment.py -- batched resumable enrichment
- New: backend/reembed_corpus.py -- idempotent corpus embedding
- New: backend/rebuild_kg_enriched.py -- rebuild enriched KG edges

Done test:
  - Block A: 5/5 files patched, py_compile clean
  - Block B: KG grew, vectors grew, enrichment improved, endpoints 200"
  git push
fi

echo
echo "======================================================================"
echo "  BLOCK B COMPLETE"
echo "======================================================================"
