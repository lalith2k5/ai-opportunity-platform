# Session Handoff — AI Opportunity Platform

Last updated: 2026-10-19 18:52 IST
HEAD commit: 0b6adbe (local, needs push)
Session shipped: Phase 1 (content correctness) + Phase 2 (batch 1+2)

## Current State (verified live)

- Backend: healthy at http://localhost:8000
- Frontend: running at http://localhost:5173
- HTTPS: https://localhost:8443
- freelm serve: running on http://127.0.0.1:4000 (log: /tmp/freelm_serve.log)
- Postgres: ai_opportunity_db
- Login: test@example.com / test1234 (admin) — endpoint uses FORM data (username=...&password=...)
- DB: 392 total (68 UNDER_REVIEW, 324 DRAFT)
- Evidence: 883 verified (cos>=0.35)
- Limitations: 507 backfilled
- Raw docs: 2315

## LLM Chain Status (BROKEN TODAY)

Provider order: freelm -> gemini -> openrouter -> openai -> anthropic

- freelm: 503 (cooldown, all providers exhausted)
- gemini: 429 (15 req/min free tier, exhausted)
- openrouter: 404 (free tier dead)
- openai: 429 (no credits)
- **Do NOT attempt title regeneration until chain recovers**

User action needed: add Groq API key (console.groq.com, free, ~2s latency)

## What Shipped Today

Phase 1 — Content Correctness:
- Evidence columns (doc_id, source_type, credibility_weight) added and backfilled on all 3163 rows
- Confidence recomputed from verified evidence (was fake 0.8)
- 507 limitations backfilled (370 EXPLICIT from paper abstracts, 137 INFERRED)
- Conflict detector verified working (MINOR/CR-4 fires on CONTRADICTS)
- Titles/descriptions regenerated via LLM (partial — chain died mid-run)
- Keyword-bag titles moved to DRAFT
- Score reconciliation: legacy (0-1) matches spec (0-100)
- API schema exposes: confidence_spec, opportunity_score_spec, status, domain, problem_type, evidence_sources
- Route enforces status filter (DRAFT hidden from users)
- Dedupe subquery fixed (was returning duplicates, now unique by title+score+id)

Phase 2 — Sources:
- 4 new keyless connectors written + verified: hackernews, openalex, crossref, gdelt
- ConnectorRunner ingests any connector output to raw_documents with dedup
- data_sources table updated (11 sources registered)

## What Remains (honest)

Content quality issues in the 79 UNDER_REVIEW cards:
- ~15 keyword-bag titles remain (blocked on LLM)
- ~10 thematic clusters that are really same opportunity:
  * Telemetry analytics security (848, 893, 956, 965, 865) — 5 cards = 1 opportunity
  * DNA/nanotechnology drug delivery (854, 915, 934) — 3 cards = 1 opportunity
  * Blockchain manufacturing (921, 959, 962) — 3 cards = 1 opportunity
  * Spatial reasoning agents (852, 913) — 2 cards = 1 opportunity
  * Whitelist access control (917, 936) — 2 cards = 1 opportunity
- Effective unique opportunities: ~55 (not 79)
- 303 DRAFTs mostly cluster artifacts, not recoverable

## Phase Completion vs Original Plan

Phase 1 (Content): ~90% complete (was target: 100%)
Phase 2 (Sources): ~40% complete (4/8 connectors, ingestion runner ready)
Phase 3 (Realtime): 0% (blocked on Groq key)
Phase 4 (UX/API): 5% (API has fields, no versioning)
Phase 5 (Eval): 0%
Phase 6 (Security): 0%
Phase 7 (Launch): 0%

## Resume Steps

1. op-status (confirm backend healthy)
2. cd backend && source venv/bin/activate && python3 tests/test_e2e_spec.py
3. curl -s -X POST http://localhost:8000/api/auth/login -d "username=test@example.com&password=test1234" (form data, not JSON)
4. git log --oneline -10 (should show 9 commits from today)

## What to Work On Next

Priority 1 — Semantic cluster dedup:
- Collapse thematic duplicates (79 cards -> ~55 unique)
- Use title embedding similarity >= 0.85 to detect clusters
- Keep highest-confidence card per cluster, demote others to DRAFT

Priority 2 — Phase 6 security (LLM-independent):
- Threat model document
- Prompt-injection defense (source text as untrusted)
- Retention and deletion jobs
- RBAC enforcement tests on every endpoint

Priority 3 — Get Groq API key for LLM recovery:
- Free at console.groq.com
- 14,400 requests/day
- ~2s latency
- Enables: title regeneration, description improvement, ongoing content quality

Priority 4 — Phase 2b: recover more DRAFTs
- Lower-priority; most DRAFTs are artifacts

## Operating Rules (unchanged, CRITICAL)

- User is a NON-CODER. Every step is a single copy-pasteable Terminal block.
- Batch file edits into ONE transactional Python script with backup + rollback.
- Use ast.parse gate after every Python patch; tsc for TypeScript.
- Avoid exclamation inside double-quoted shell strings (zsh history expansion).
- Avoid top-level hash comment lines in pasted shell buffers.
- Avoid heredoc arithmetic with $((...)) -- has wedged the shell.
- If heredoc terminator lost, shell hangs on "heredoc>" -- press Ctrl-C.
- Commit after each working deliverable.
- Wait for user "go" before any code block.
- English only in responses.

## Today's Commits (9 total, all local, need push)

900498e phase1: content correctness foundation complete
bf34733 fix: enforce invariant - UNDER_REVIEW requires confidence > 0
bd34b19 phase2 hotfix: API schema exposes spec fields + evidence
c0b7a0f schemas: add model_config=ConfigDict
b92cf2e routes: enforce status filter (attempt 1)
f829fc4 routes: apply status filter (final, working)
50515db phase2 batch2: retry stuck DRAFTs + title improvement
0b6adbe routes: fix duplicate-title leak

Next session: user needs to review browser at http://localhost:5173/opportunities
