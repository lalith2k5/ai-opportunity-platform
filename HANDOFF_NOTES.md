# Session Handoff — AI Opportunity Platform

Last updated: 2026-10-19 19:30 IST
HEAD commit: 8851dc3 (local, needs push)
Session outcome: ARCHITECTURE PIVOT DECIDED. Full rebuild scheduled.

## CRITICAL — Architecture decision

User rejected incremental improvement after reviewing current content quality.
The 387 existing opportunities, all evidence, trends, gaps WILL BE ERASED.
raw_documents (2,315), code, users, auth, configs WILL BE PRESERVED.

New architecture documented in IMPLEMENTATION_PLAN.md v2.0 (6 requirements R1-R6):
- R1 Topic-scoped runs (every pipeline invocation is a topic query)
- R2 Evidence-first extraction (no LLM invention)
- R3 No empty fields / no fallbacks / no "Other"
- R4 Source clickthrough verified (URL 200, content supports claim)
- R5 Every field has verifiable source
- R6 No cross-run data aggregation

Honest yield after rebuild: 3-10 cards per topic (not 387 in one pool).

## Current state (verified live)

- Backend healthy at http://localhost:8000
- Frontend at http://localhost:5173
- Login: test@example.com / test1234 (FORM data endpoint: username=...&password=...)
- DB: 387 opportunities (68 UNDER_REVIEW, 319 DRAFT), 883 verified evidence, 507 limitations
- 8 source connectors in code, 6 working keyless, 2 awaiting keys

## Sources status

| Source | Status | Action |
|---|---|---|
| Hacker News | Working | None |
| GDELT | Working | None |
| Crossref | Working | None |
| OpenAlex | Working (keyless) | Add free key: openalex.org/action/register |
| Stack Exchange | Working (keyless 300/day) | Add free key: stackapps.com/apps/oauth/register |
| Dev.to | Working | None |
| USPTO ODP | Built, needs key | Free: data.uspto.gov/myodp |
| EPO OPS | Built, needs OAuth2 | Free: developers.epo.org (non-paying) |

Permanent skip: Reddit (API closed to new applicants Nov 2026).

## LLM chain

Order: groq -> freelm -> gemini -> openrouter -> openai -> anthropic

- groq: WORKING, 2s latency, model `openai/gpt-oss-20b` (8000 TPM free)
- freelm: local :4000, ~20s, fallback (working)
- gemini: 429 daily exhausted
- openrouter: 404 free tier dead
- openai: 429 no credits
- anthropic: empty

Groq key in `.env` as `GROQ_API_KEY`. Model configurable via `GROQ_MODEL`.

## What shipped today (11 commits pushed to origin/main)

Code:
- Groq provider (fastest LLM, working)
- 4 new source connectors: StackExchange, DevTo, USPTO ODP, EPO OPS
- ConnectorRunner with dedupe
- API schema exposes spec fields (was silently stripping them)
- Status filter on /opportunities (DRAFT no longer leaks)
- Dedupe subquery fixed (no duplicate titles in API)

Data:
- evidence columns backfilled (source_type, credibility_weight, doc_id) on all 3,527 rows
- 507 limitations extracted (370 EXPLICIT, 137 INFERRED)
- Conflict detector verified (MINOR/CR-4 fires on seeded CONTRADICTS)
- 15 keyword-bag titles regenerated via Groq (partial - will be erased in rebuild)

Data sources registered: 11 total (github, arxiv, news, rd_cells, challenge_portal, patents, reddit, hackernews, openalex, crossref, gdelt, stackexchange, devto, uspto, epo)

## What gets erased in Phase 2 (tomorrow)

- opportunities (387 rows)
- opportunity_evidence (3,527 rows)
- research_gaps (375)
- problem_clusters (375)
- problem_technologies (396)
- trends (546)
- limitations (507)
- problem_profiles (106)
- problem_papers (200)

Preserved: raw_documents (2,315), processed_documents, users, auth, data_sources, license_records, weight_configs, confidence_configs, trend_configs, code.

Backup taken before Phase 2 with full pg_dump + restore verification.

## Tomorrow — Session 1 plan

1. Verify backup exists and restores cleanly
2. Alembic migration: create `runs` table, add run_id columns to 8 tables, add verification columns to opportunity_evidence
3. Verify migration: no data lost, all tables present, API still works
4. Truncate contaminated tables per Phase 2 list above
5. Verify counts: preserved tables unchanged, truncated tables = 0
6. Commit migration
7. STOP. Do not start Phase 3 in same session.

## Tomorrow — Session 2 onwards

Session 2: EvidenceVerifier (fetch, hash, LLM claim match) + tests
Session 3: TopicResolver + SourceScoper with topic-relevance gate
Session 4-5: Evidence-first extraction (problem, tech, gap) with verbatim quote requirements
Session 6: Title/description composition (phrase extraction + LLM ordering + provenance)
Session 7: CardGatekeeper (5 verification gates)
Session 8: First run on "drone delivery system"
Session 9: API run-scoping (/api/runs/*)
Session 10: Frontend run selector
Session 11: Human review of 3 cards
Session 12: Second topic isolation test
Session 13: Expanded corpus run

See IMPLEMENTATION_PLAN.md v2.0 for full detail (141 lines, 30 blocks).

## Operating rules (unchanged, CRITICAL)

- User is NON-CODER. Every step is a single copy-pasteable Terminal block.
- Batch file edits into ONE transactional Python script with backup + rollback.
- ast.parse gate after every Python patch; tsc for TypeScript.
- Avoid `!` inside double-quoted shell strings (zsh history expansion).
- Avoid top-level `#` lines in pasted shell buffers.
- Avoid `$((...))` heredoc arithmetic.
- Avoid `$!` in heredoc blocks (killed the previous attempt today).
- If heredoc terminator lost, press Ctrl-C and paste a smaller chunk.
- **Prefer 4 chunks of <60 lines over 1 paste of 200+ lines.**
- Commit after each working deliverable.
- Wait for user "go" before any code block.
- English only in responses.
- Do not paste secrets into chat - use `read -s` in Terminal.

## Today's commits (12 pushed to origin/main)

8851dc3 plan v2.0: evidence-first architecture
e1349b8 sources: add 4 free connectors
db69140 llm: add Groq provider as primary
2279a2d handoff update
0b6adbe routes: fix duplicate-title leak
aa0285e phase1 batch3: scheduler cleanup
50515db phase2 batch2: retry stuck DRAFTs
f829fc4 routes: apply status filter (final)
b92cf2e routes: enforce status filter (attempt)
c0b7a0f schemas: add model_config=ConfigDict
bd34b19 phase2 hotfix: API schema exposes fields
bf34733 fix: enforce invariant
900498e phase1: content correctness foundation

## User action items before next session (each 2 min)

1. OpenAlex key: https://openalex.org/action/register
2. Stack Exchange key: https://stackapps.com/apps/oauth/register
3. USPTO ODP key: https://data.uspto.gov/myodp
4. EPO OPS OAuth2: https://developers.epo.org (Non-paying access)

After registration, ask for the safe `.env` write block (uses read -s).

## Reference: current system (about to be replaced)

- 68 UNDER_REVIEW cards, 319 DRAFT
- API serves confidence_spec, opportunity_score_spec, evidence_sources, status, domain, problem_type
- /api/opportunities defaults to status=UNDER_REVIEW
- 6 working sources, 2 awaiting keys
- 883 verified evidence items (cos>=0.35)

This state is the best it has been, but it is NOT what the user asked for.
The rebuild is the fix.
