# Session Handoff — AI Opportunity Platform

Last updated: 2026-10-19 21:07 IST
HEAD commit: (will be updated after this commit)
Session outcome: **DATABASE WIPED. FOUNDATION PRESERVED. READY FOR REBUILD.**

## CRITICAL — Current System State

The system has been completely wiped of contaminated content. This was intentional and confirmed.

**ERASED (now 0 rows):**
- opportunities, opportunity_evidence, opportunity_score_history
- research_gaps, problem_technologies, problem_profiles, problem_papers, problem_clusters
- limitations, trends, trend_snapshots
- recommendations, kg_nodes, kg_edges, conflict_flags
- notifications, chat_messages, chat_sessions, search_history, feedback, change_events

**PRESERVED (safe and intact):**
- raw_documents: 2,315 real source documents
- processed_documents: 768
- users: 2 (test@example.com)
- data_sources: 15
- license_records: 7
- weight_configs, confidence_configs, trend_configs: 1 each
- system_config: 4 (encrypted API keys)
- organizations: 27

**BACKUP EXISTS:** `backups/pre_wipe_20261019_204526.pgdump` (3.19 MB)

## What Was Fixed Today (Infrastructure)

1. **Groq LLM Added**: Working perfectly at ~2s latency. Provider order is now `groq -> freelm -> gemini -> openrouter -> openai -> anthropic`. Groq is primary.
2. **8 Source Connectors**: Hacker News, GDELT, Crossref, OpenAlex, Stack Exchange, Dev.to are working keyless. USPTO ODP and EPO OPS are built but waiting for your free API keys.
3. **Admin Panel API Keys**: New "Configuration" tab in Admin panel. You can paste API keys, test them live, and they take effect within 60 seconds without restarting. No more editing `.env`.
4. **Architecture Pivot Documented**: `IMPLEMENTATION_PLAN.md` v2.0 is written. It defines the 6 governing requirements (topic-scoped runs, evidence-first extraction, no empty fields, source clickthrough, no hardcoding).

## Tomorrow — Session 1 Plan

The UI will look empty right now. **This is correct.** Tomorrow we start the rebuild:

1. **Phase 1 — Migration**: Run Alembic to create the new `runs` table and add `run_id` foreign keys to the target tables. Add evidence verification columns.
2. **Phase 2 — Pipeline Code**: Write the `EvidenceVerifier` (fetches URL, hashes content, LLM confirms claim) and the `TopicScoper` (ensures query "drone delivery" only pulls drone documents).
3. **Phase 3 — Extraction**: Write the new evidence-first extraction logic. No LLM invention; only verbatim quotes from sources.
4. **Phase 4 — First Run**: Run the first topic query against the 2,315 raw documents and verify the 3-10 cards it produces are 100% defensible.

## LLM & Sources Status

- **Groq**: WORKING (Primary)
- **Freelm**: WORKING (Fallback)
- **Sources**: 6 working keyless, 2 awaiting keys (USPTO, EPO).
- **Action Items**: Register the free keys (OpenAlex, Stack Exchange, USPTO, EPO) and paste them into the Admin -> Configuration tab.

## Operating Rules (CRITICAL)
- User is a NON-CODER. Every step is a single copy-pasteable Terminal block.
- Batch edits into ONE transactional Python script.
- Use ast.parse gate after every Python patch; tsc for TypeScript.
- Avoid `!` inside double-quoted shell strings.
- Avoid top-level `#` lines in pasted shell buffers.
- Avoid `$!` in heredocs.
- **Prefer 4 chunks of <60 lines over 1 paste of 200+ lines.**
- Commit after each working deliverable.
- Wait for user "go" before any code block.
