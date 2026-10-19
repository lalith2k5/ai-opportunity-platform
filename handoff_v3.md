# HANDOFF v3 — AI Opportunity Platform (post Session 3)

Session ended: 2026-09-28
Last commit on origin/main: 841c66e
Status: ALL 9 ROADMAP PHASES SHIPPED

## 1. Project Goal & Overview

**What it does:** AI-powered decision-support platform that discovers
startup and research opportunities by continuously collecting signals
from GitHub (repos + issues), arXiv, News RSS, R&D lab feeds, government
challenge portals (SBIR / challenge.gov / NASA / NIST / NSF / DARPA / NIH
/ DOE), and patents — running them through a multi-agent AI pipeline,
and scoring them with an explainable multi-factor model.

**Users:** Students, researchers, entrepreneurs, investors, admins.

**Stack:**
- Frontend: React 19 + TypeScript + Tailwind + Vite + react-force-graph-2d
  + recharts, port 5173
- Backend: FastAPI + Python 3.12 + SQLAlchemy, port 8000
- Data: PostgreSQL (ai_opportunity_db), ChromaDB (vector store)
- AI: Gemini `gemini-3.5-flash-lite` (500 RPD free tier — switched from
  gemini-3.8-flash which is only 20 RPD), Sentence Transformers all-MiniLM-L6-v2
- HTTPS in dev: Caddy local CA on port 8443
- Process management: MANUAL — op-start / op-stop / op-status / op-logs
  shell functions in ~/.zshrc. launchd auto-start DISABLED.

**Repo:** https://github.com/lalith2k5/ai-opportunity-platform
**Local root:** ~/ai-opportunity-platform
**Test credentials:** test@example.com / test1234 (admin)

**Operational commands:**
- op-start — Postgres check + backend + frontend + caddy (waits up to 90s)
- op-stop — stops all 3, frees ports 8000/5173/8443
- op-status — running state + health + Postgres
- op-logs — tails all logs (or op-logs backend)

## 2. Current state (Session 3 completed)

### Commits shipped this session (all on origin/main)

| Commit    | Phase   | What                                                 |
|-----------|---------|------------------------------------------------------|
| 6028abc   | 0.1     | PatentsView service (opt-in, dormant without key)    |
| 83ade4e   | 0.2     | GitHub Issues wiring + autoflush bug fix             |
| 4fec766   | 1.1     | Universal ProblemExtractorAgent + circuit breaker    |
| 1e6306f   | 1.2     | ProblemAgent canonical_hash dedup                    |
| 0eb57f9   | 1.3     | Cross-source provenance merge                        |
| 07f97d1   | 2.1     | TechnologyAgent + problem_technologies table         |
| 179bd89   | 3.1     | ResearchDiscoveryAgent + problem_papers table        |
| 0043bef   | 4.1     | EvidenceAgent + opportunity_evidence table           |
| 80d4828   | 5       | Canonical KG schema (SRS §31) + 5,954 relations      |
| 563fec7   | 6.1/6.2 | Opportunity 10-col enrichment + ResearchDirection    |
| cecea23   | 6.3     | Frontend OpportunityDetail 16-field rewrite          |
| 0cf6333   | 6.4     | TS fix + loosened cluster<->profile keyword match    |
| 015c679   | 7.1     | Backend flow endpoints (researcher + rd)             |
| d1467a1   | 7.2     | 3 workflow pages (student, researcher, rd)           |
| e4a70a9   | 8.2/8.3 | Score history + rank-change alerts                   |
| 30fe54d   | 9.4/9.6 | Error boundary + score chart + loading skeletons     |
| bf20318   | 9.6     | Backend pytest suite (14 tests) + CI collect-only    |
| 841c66e   | fix     | op-start.sh health-check window 45s -> 90s           |

### Key session wins

1. **Autoflush bug fixed.** SessionLocal is autoflush=False, so
   _save_to_db's db.query(RawDocument).all() couldn't see freshly-added
   rows. Every brand-new source silently dropped its processed documents.
   Added db.flush() before the linkage query. Fix also repaired
   challenge_portal linkage (3 -> 15 processed docs).

2. **Gemini model swapped.** gemini-3.8-flash free tier is only 20 RPD
   (exhausted repeatedly). gemini-2.5-flash was discontinued (404 for
   new users). Switched to gemini-3.5-flash-lite (500 RPD). 25x quota.

3. **Universal extraction.** ProblemExtractorAgent now runs on
   github_issues, arxiv, news, patents, challenge_portal with
   per-source caps in config.py.

4. **Canonical KG.** All relation names uppercased per SRS §31.
   build_enriched_graph() reads Phase 2/3/4 tables and emits canonical
   edges every pipeline run.

5. **Detached-instance helper.** OrchestratorAgent._row_id(obj) reads a
   PK via sqlalchemy.inspect().identity without triggering a refresh.
   Used by _save_technologies, _save_problem_papers, _save_evidence.

### Current DB row counts (approx)

- users: 1
- raw_documents: 1,548
- problem_clusters: 266
- opportunities: 266
- problem_profiles: 57
- problem_technologies: 126
- problem_papers: 68
- opportunity_evidence: 491
- kg_nodes: 4,110
- kg_edges: 7,441
- opportunity_score_history: 300
- trends: ~40

### Known remaining issues

- PatentsView API key not set (new key grants temporarily suspended by
  PatentsView as of 2024). Path B ready: Admin -> Config -> paste key.
- Reddit unconfigured (user explicitly deferred).
- SBIR API returns 403 from datacenter IPs. RSS fallback works.
- OpenAI / Anthropic not configured (Gemini only).

## 3. Roadmap status — ALL 9 PHASES SHIPPED

| Phase | Status |
|-------|--------|
| 0 — Data source completeness | DONE (0.2 shipped; 0.1 shipped, key deferred) |
| 1 — Per-problem extraction | DONE |
| 2 — Technology identification | DONE |
| 3 — Research discovery per problem | DONE |
| 4 — Evidence aggregation | DONE |
| 5 — KG schema alignment | DONE |
| 6 — Opportunity card enrichment | DONE |
| 7 — Workflows | DONE |
| 8 — Continuous update & scoring | DONE |
| 9 — Quality/security/polish | DONE (9.1 Redis, 9.2 Linux skipped) |

**Optional polish remaining:**
- Loading skeletons exist but not wired into pages
- Lighthouse a11y audit not yet run
- Redis rate limiting (skipped — in-memory limiter works)

## 4. File layout (post-Session-3)

### Backend — backend/app/

Core:
- config.py — adds PATENTSVIEW_API_KEY,
  PROBLEM_EXTRACTION_CAP_{GITHUB,ARXIV,NEWS,PATENTS}
- database.py, logger.py, main.py (8 routers), middleware.py,
  rate_limit.py, scheduler.py
- models.py — 22 tables. New: ProblemTechnology, ProblemPaper,
  OpportunityEvidence, OpportunityScoreHistory. Altered: ProblemProfile
  (canonical_hash, additional_sources), Opportunity (10 enrichment cols).
- schemas.py

Agents — backend/app/agents/:
- orchestrator.py — full pipeline + Phase 1-8 hooks + _row_id
- data_collection.py — parallel fetch (7 sources)
- nlp_agent.py, knowledge_graph.py, problem_discovery.py,
  research_gap.py, innovation_monitor.py, opportunity_intelligence.py,
  explainable_ai.py, ai_chat.py
- problem_extractor.py — universal, source-agnostic
- problem_agent.py — canonicalize, compute_hash, dedup, merge_provenance
- technology_agent.py — LLM, stage in used/proposed/emerging/potentially_applicable
- research_discovery_agent.py — arXiv + LLM limitation extraction
- evidence_agent.py — CPU-only keyword match
- research_direction_agent.py — LLM research + project direction

Services — backend/app/services/:
- llm_service.py (singleton), embedding_service.py, github_service.py
  (+ _normalize_issue), arxiv_service.py, news_service.py,
  reddit_service.py, rd_cells_service.py, challenge_portal_service.py,
  patents_service.py, notification_service.py, pdf_service.py,
  retry_helper.py

API — backend/app/api/:
- routes.py, auth_routes.py, admin_routes.py, admin_config_routes.py,
  notification_routes.py, kg_routes.py, export_routes.py,
  problem_profile_routes.py, flow_routes.py (NEW)

Schema helpers:
- app/kg_schema.py — CANONICAL_RELATIONS, LEGACY_RELATION_MAP,
  normalize_relation()

Migration scripts (idempotent, in backend/):
- migrate_problem_profiles_canonical_hash.py
- migrate_problem_profiles_additional_sources.py
- migrate_problem_technologies.py
- migrate_problem_papers.py
- migrate_opportunity_evidence.py
- migrate_kg_relations_uppercase.py (already run: 5,954 rows)
- migrate_opportunity_enrichment.py
- migrate_opportunity_score_history.py

Tests — backend/tests/:
- conftest.py, test_health.py, test_auth.py, test_opportunities.py,
  test_flows.py — 14 tests, all passing in <1s

Dev dependencies: backend/requirements-dev.txt
CI: .github/workflows/test.yml (collect-only)

### Frontend — frontend/src/

Pages (new this session):
- StudentWorkflow.tsx, ResearcherWorkflow.tsx, RDWorkflow.tsx
- OpportunityDetail.tsx — full 16-field rewrite

Components (new):
- ErrorBoundary.tsx, LoadingSkeleton.tsx, ScoreHistoryChart.tsx

Routes in App.tsx:
- /workflows/student, /workflows/researcher, /workflows/rd

Sidebar: 3 new entries under Workspace.

API service (services/api.ts): added getResearcherFlow, getRDFlow,
getProblemProfileStats, getOpportunityHistory. Opportunity interface
extended with 10 enrichment fields.

## 5. Operating Rules (CRITICAL)

- User is a NON-CODER. Every step is a copy-paste-able Terminal block.
- DO NOT describe manual file edits. Write patching Python/bash.
- One paste, one block. But user prefers BATCHED TRANSACTIONAL blocks:
  multiple file patches in one script, all-or-nothing rollback.
- DO NOT paste secrets into chat. Use read -s in Terminal.
- DO NOT force push without asking.
- Avoid '!' characters inside double-quoted shell strings — zsh history
  expansion kills the paste. Use single-quoted python3 -c or heredocs.
- Avoid top-level '#' comment lines in pasted buffers — zsh tries to
  execute them ('command not found: #').
- set -o pipefail when piping tsc through tee.
- If a patch string-match fails, ROLLBACK and retry.
- Commit after each working deliverable.

### Preferred workflow (2 blocks per deliverable)

Block A — patch + migrate + smoke test: single paste, transactional,
all-or-nothing, prints PASS/FAIL banner.

Block B — restart + live verify + commit + push: single paste, gates
commit on live verification passing.

### Commit template

phase X.Y: <short title>

- file1.py: <what changed>
- file2.py: <what changed>
- New: <new file> — <purpose>

Done test:
  - Block A: <what verified>
  - Block B: <what verified live>

## 6. Getting started in the new chat

1. Read this handoff fully.
2. Read the codebase dump (clean_codebase_v6.txt).
3. Confirm understanding with a short summary:
   - All 9 phases shipped, 841c66e is HEAD
   - What user wants next (likely: optional polish, or new feature)
4. Do NOT start blocks until user confirms.

## 7. Test credentials & ports

- test@example.com / test1234 (admin)
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- HTTPS (Caddy): https://localhost:8443
- API docs: http://localhost:8000/docs
- Postgres: localhost:5432, DB ai_opportunity_db
- ChromaDB: backend/chroma_db/

## 8. Known good behaviors & gotchas

- Backend cold-start takes 50-60s on first boot after op-stop
  (SentenceTransformer load). op-start.sh waits up to 90s.
- LLMService.generate() never raises. Returns sentinel string
  "All LLM providers failed..." on total failure.
- Circuit breakers: ProblemExtractorAgent, TechnologyAgent,
  ResearchDiscoveryAgent, ResearchDirectionAgent all stop after 2
  consecutive LLM failures per batch.
- _PIPELINE_LOCK — only one pipeline runs at a time.
- Scheduler fires ~60s after backend boot.
- Gemini free-tier quota is per-model.
- Detached-instance pattern: use OrchestratorAgent._row_id(obj) when
  passing ORM rows across session boundaries.

## 9. Environment reset (destructive — not recommended)

cd ~/ai-opportunity-platform
bash op-stop.sh
dropdb ai_opportunity_db && createdb ai_opportunity_db
bash op-start.sh

Current DB has ~1,500 raw docs + full enrichment output.

END OF HANDOFF
