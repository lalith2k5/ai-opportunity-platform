# Session Handoff — AI Opportunity Platform

Last updated: 2026-10-19 ~17:00 IST
HEAD commit: a119548
Session shipped: 19 blocks — all spec compliance + LLM resilience complete

## Current State (verified)

- Backend: healthy at http://localhost:8000
- Frontend: running at http://localhost:5173
- HTTPS: https://localhost:8443
- freelm serve: running on http://127.0.0.1:4000 (log: /tmp/freelm_serve.log)
- Postgres: ai_opportunity_db
- Login: test@example.com / test1234 (admin)
- DB: 374 opportunities, 536 trends, 343 gaps
- E2E test: 29/29 passing at backend/tests/test_e2e_spec.py
- git status: clean of build artifacts

## LLM Chain (current)

Provider order: freelm (primary) -> gemini -> openrouter -> openai -> anthropic

- freelm: local gateway on :4000, keyless OVH/kilo endpoints, ~20s latency, never exhausts
- gemini: gemini-3.5-flash-lite, 500 RPD free, ~1s latency, exhausts daily
- openrouter: free tier is dead (all :free models return 404), needs 5 USD credits
- openai: needs credits, currently empty

backend/.env has:
  LLM_PRIMARY_PROVIDER="freelm"

To switch back to gemini primary (fast when fresh):
  sed -i "" "s/LLM_PRIMARY_PROVIDER=.freelm./LLM_PRIMARY_PROVIDER=.gemini./" backend/.env
  bash op-stop.sh && sleep 2 && bash op-start.sh

## What Shipped This Session (19 commits)

Spec compliance:
- 7-factor scoring formula (spec 33.2) + N/D/M/A confidence (spec 33.3)
- Versioned configs (weight_configs, confidence_configs, trend_configs)
- Gap honesty: kind (CAPABILITY/COVERAGE), gap_status, supporting_limitations
- Expert review queue at /review (spec 25, FR-22)
- Conflict detection CR-1..CR-6 + evaluation metrics endpoint (spec 28.3, 38)
- Auto-sweep every 15 min + ChangeEvent emission (spec 35.2)
- License gate enforcement (spec 6.7, FR-27)
- Notification delivery (spec 35.4, FR-24)
- Reproducibility manifest (spec 38.5, FR-32)

Polish:
- Loading skeletons on 5 pages
- README rewrite (spec-compliant documentation)
- E2E test suite (29 checks)

LLM resilience:
- Fast-fail on 429 + circuit breaker (was retrying 3x with 2s sleeps)
- freelm local gateway as primary provider
- Graceful UX fallback in ai_chat.py

## Operating Rules (CRITICAL)

- User is a NON-CODER. Every step is a single copy-pasteable Terminal block.
- Batch file edits into ONE transactional Python script with backup + rollback.
- Use ast.parse gate after every Python patch; tsc for TypeScript.
- Avoid exclamation inside double-quoted shell strings (zsh history expansion).
- Avoid top-level hash comment lines in pasted shell buffers (zsh command-not-found).
- Avoid heredoc arithmetic with double-paren syntax -- it has wedged the shell.
- If a heredoc terminator line is lost, shell hangs on "heredoc>" prompt -- press Ctrl-C to escape.
- Commit after each working deliverable.
- Wait for the user to say go before starting any code block.
- English only in responses.
- Do not force push without asking.
- Do not paste secrets into chat -- use read -s in Terminal.

## Preferred Workflow (2 blocks per deliverable)

Block A: patch + migrate + smoke test. Single paste. Transactional. Prints PASS/FAIL.
Block B: restart + live verify + commit + push. Commit gated on verification.

## Operational Commands

- op-start (start backend + frontend + caddy)
- op-stop (stop all)
- op-status (check health)
- op-logs (tail logs)
- op-show (display a specific file — ask user to run this when full fidelity needed)

## Known Limitations (all optional)

- PatentsView key unavailable — patents source dormant
- Reddit unconfigured — credentials deferred
- SBIR API returns 403 from datacenter IPs — RSS fallback covers
- License gate is warn-only by default (rows seeded as PENDING)
- freelm uses keyless endpoints (~20s latency)
- Adding a free Groq key would give ~2s latency
- Reproducibility manifest endpoint exists but no file export writer

## Files Attached to This Chat

- HANDOFF_NOTES.md (this file)
- codebase_index.txt
- git_log.txt
- git_status.txt
- env_and_deps.txt
- System Specification PDF (32 FR + 20 modules)
- Optional: phase3.1.docx

## Resume Steps

1. op-status (confirm backend healthy)
2. cd backend && source venv/bin/activate && python3 tests/test_e2e_spec.py
3. tail -20 /tmp/freelm_serve.log (if chat is slow/down)
4. git status (should be clean)

## What to Work On Next (if user asks)

- Speed: add Groq free key (14400 RPD, ~2s latency)
- ProvenanceRecord entity (spec 31 has a column, no dedicated table)
- Reproducibility export writer
- Per-user notification subscriptions (currently broadcast)
- Lighthouse a11y audit
