# AI Opportunity Platform — Implementation Plan to National Deployment
**Version 1.0 · 19 October 2026 · Post-diagnostic baseline**

Scale target: 100 concurrent users / 100,000 documents
Source policy: 100% free sources only
Deployment target: National India launch (evidence-quality, compliance, security, and load-test gates)

---

## 1. Verified current state (as of 2026-10-19)

### Database contents
- opportunities: 378 rows
- opportunity_evidence: 3,163 rows (all now with doc_id, source_type, credibility_weight after Block 1.2b)
- trends: 546, research_gaps: 375, problem_clusters: 375
- raw_documents: 1,942 (URL-verified against all 3,163 evidence items)
- limitations: 0 (blocked gap analysis)
- conflict_flags: 0 (detector never fires)
- opportunity_score_history: 4,152
- weight_configs: 1 (v1.0.0), confidence_configs: 1 (v1.0.0), trend_configs: 1 (v1.0.0)

### What works
- Schema: 34 tables, spec-compliant, migrations clean
- Plumbing: 29/29 E2E tests pass, endpoints return 200
- Evidence storage: 3,163 items, 100% URL-matched to raw_documents
- Source connectors for 6 raw types: arxiv(808), github(768), github_issues(722), news(650), rd_cells(212), challenge_portal(3)

### What is broken (diagnosed, not fixed yet)
1. Orchestrator passes the wrong data to the confidence formula
   - source_type = raw string ("github" vs "github_issues") — counts one class as two
   - credibility_weight = relevance_score (mean 0.28) — that measures topical match, not trustworthiness
   - doc_id = oe.id (row id), not linked to raw_documents
   - RESULT: confidence_spec is inflated or wrong on the 263 opps that have evidence
2. 115 opportunities have ZERO evidence rows (score a hard 0 on confidence)
3. Titles are keyword bags ("Machine Learning, Signals & Measures")
4. Descriptions are templates ("Opportunity focused on X, Y, Z")
5. Three conflicting scores per card (0.54 / 48.0 / "0.56" in explanation)
6. limitations table empty — gap analysis is ungrounded
7. conflict_flags empty — CR-1..CR-6 never fires
8. All 378 cards are status=PROPOSED (spec §17 forbids publication in this state)
9. Controlled vocabularies leak free text (domain='Other', problem_type='Other')
10. No Reddit (dead API), no patents source active

### What was fixed today (Block 1.2b — PASSED)
- Added columns to opportunity_evidence: doc_id, source_type, credibility_weight
- Backfilled all 3,163 rows:
  - doc_id: 100% matched to raw_documents via URL
  - source_type: canonicalized (GITHUB / RESEARCH / NEWS / RND; patents/reddit dormant)
  - credibility_weight: source-based defaults (RESEARCH=0.90, RND=0.80, NEWS=0.60, GITHUB=0.50)
- Verification: 3163/3163/3163/3163 (total = doc_id = source_type = credibility_weight)

---

## 2. Decision log — resolved ambiguities

These are the 7 ambiguities the source spec leaves open. Each is resolved for this plan:

| # | Ambiguity | Resolution for this plan |
|---|---|---|
| 1 | Trend formula (§33.5 vs Appendix C.3) | Use §33.5: base × (0.5 + 0.5×growth) for EMERGING/GROWING; base × confidence otherwise |
| 2 | CR-5 penalty (fixed -25 vs multiplicative) | Use multiplicative 0.50 × severity (matches code) |
| 3 | Missing factor behavior | Cannot publish an opportunity if any of the 7 spec factors is NULL |
| 4 | N dedup semantics | Distinct doc_id (not row id) — updated in Block 1.2c |
| 5 | Source-type taxonomy | 6 canonical: GITHUB, REDDIT, RESEARCH, NEWS, RND, PATENT |
| 6 | Min-max normalization population | 365-day rolling window per domain |
| 7 | Credibility weights | Defaults above; override via SourceCredibilityProfile table in Phase 2 |

---

## 3. Phase 1 — Content correctness (blocks 1.2c – 1.13)

**Goal:** every card visible to a user is verifiable, useful, and honest.

### Block 1.2c — Fix orchestrator to use the new columns
- Rewrite lines ~560-568 of app/agents/orchestrator.py
- _ev_items construction reads source_type, credibility_weight, doc_id from the new columns
- PASS: internal confidence formula receives correct inputs; recomputation on opp 1069 matches expected

### Block 1.2d — Recompute confidence for all 378 opportunities
- Single transactional run, backup first
- PASS: no card with evidence has confidence=0; no card displays 0.8 fake
- PASS: 5 sampled opportunities recompute to stored value ±1

### Block 1.2e — Handle the 115 zero-evidence opportunities
- Options: (a) fetch evidence for them in Phase 2, (b) hide from public until evidenced
- Decision: hide from public list, keep in admin queue
- PASS: public API returns only opps with ≥1 evidence item

### Block 1.2f — Score reconciliation
- Retire legacy opportunity_score (0-1) as display value; make opportunity_score_spec (0-100) canonical
- Rewrite explanation text from seven factor contributions
- PASS: every card shows one score; explanation matches stored value

### Block 1.2g — Limitation extraction backfill
- Parse existing_approaches and known_limitations text fields into limitations rows (INFERRED)
- Wire research agent to extract limitations from paper abstracts (EXPLICIT)
- PASS: ≥80% of research_gaps have ≥1 linked limitation

### Block 1.2h — Conflict detection verification
- Diagnose why conflict_flags=0 (never ran? never received conflicting evidence? exceptions swallowed?)
- Seeded test: two contradictory evidence items → flag must appear
- PASS: seeded conflict produces flag with correct severity, rule, evidence_ids

### Block 1.2i — Card title and description rewrite (pilot 5 first)
- New prompt: "Title names one specific problem-technology opportunity, ≤90 chars, no comma lists"
- New prompt: "Description states problem, technology, gap in prose, cites evidence IDs"
- Validate generated output: title mentions ≥1 linked technology; description references ≥1 evidence ID
- PASS on pilot: 5 cards reviewed by user, deemed useful

### Block 1.2j — Full regeneration (all 378)
- Only after 1.2i passes
- Transactional, backup, rollback
- Preserve IDs; write opportunity_score_history rows
- PASS: audit report shows 9/9 accuracy checks PASS on 30 sampled cards

### Block 1.2k — Status workflow
- Generation writes PROPOSED, auto-transitions to UNDER_REVIEW after evidence validation
- Public API filters status IN (UNDER_REVIEW, VALIDATED)
- PASS: zero PROPOSED cards visible publicly

### Block 1.2l — Controlled vocabularies
- Populate problem_types, domains, industries tables from spec §1.2
- Constrain generation to choose from controlled list
- PASS: zero cards with domain='Other' or problem_type='Other'

### Block 1.2m — Human spot-check (user's time, not a code block)
- User reviews 30 cards across domains
- PASS: user confirms all 30 are useful and accurate
- This is the Phase 1 exit criterion

**Phase 1 total: 11 blocks (1.2c through 1.2l, plus 1.2m is user review)**

---

## 4. Phase 2 — Source expansion (all free)

**Goal:** 6 canonical source classes fully active, patent class replaces dormant PatentsView, community class replaces dead Reddit.

Each new connector is its own block, must pass: license gate → evidence schema → dedup → accuracy audit re-run.

| Source | Key | Class | Block |
|---|---|---|---|
| Hacker News | none | Community | 2.1 |
| Stack Exchange | free key | Community | 2.2 |
| GDELT | none | News | 2.3 |
| OpenAlex | none | Research | 2.4 |
| Crossref | none | Research | 2.5 |
| USPTO PatentsView | none | Patents | 2.6 |
| EPO OPS | free account | Patents | 2.7 |
| Dev.to | free key | Community | 2.8 |

**Phase 2 total: 8 blocks**
**Exit criterion:** all 6 canonical classes active, all license-gated, Phase 1 accuracy checks still PASS on the expanded corpus

---

## 5. Phase 3 — Realtime and reliability (6-8 blocks)

### Block 3.1 — LLM primary provider fix
- Restore the Groq integration that was reverted (commit 4f84d1d) correctly
- Fallback chain: Groq → Gemini → freelm → openrouter → openai
- PASS: median chat latency <3s across 20 live queries

### Block 3.2 — Streaming chat responses
- First-token <500ms; full response complete within 5s
- PASS: measured on 20 queries

### Block 3.3 — Durable job execution
- Wrap APScheduler with crash-safe mechanism (Redis-backed queue or equivalent)
- PASS: forced crash loses no queued jobs

### Block 3.4 — Reproducibility manifest file writer
- Every published score gets downloadable JSON that replays to the same number
- PASS: re-run on 10 sampled scores yields identical output

### Block 3.5 — Per-user notification subscriptions
- Currently broadcast; make subscriptions per-user
- PASS: two test users receive different notification sets for same change

### Block 3.6 — Observability
- Structured logs (partly done), metrics, alerts on error rate, queue depth, cost
- PASS: alert fires when error rate exceeds threshold in staged test

**Phase 3 total: 6 blocks**

---

## 6. Phase 4 — UX and API (6-8 blocks)

### Block 4.1 — API versioning (/api/v1 with backward-compatible alias)
### Block 4.2 — Export (JSON + PDF, preserving citations)
### Block 4.3 — Review UX polish (keyboard, no double-submit, before/after diff)
### Block 4.4 — Search UX (zero-result explanation, safe suggestions)
### Block 4.5 — WCAG 2.2 AA audit on 5 primary screens
### Block 4.6 — Mobile-first layout verification

**Phase 4 total: 6 blocks**
**Exit criterion:** external user completes 5 core workflows on desktop and mobile without assistance

---

## 7. Phase 5 — Evaluation harness (4-6 blocks)

### Block 5.1 — Gold sets (start small: 100 problems, 50 problem-tech pairs, 100 search queries, 50 gaps)
### Block 5.2 — Metrics runner (precision/recall, nDCG@10, MRR, gap acceptance, conflict recall, grounded-citation correctness, unsupported-claim rate)
### Block 5.3 — CI integration (metrics run on every release)
### Block 5.4 — Evaluation dashboard surfaced

**Phase 5 total: 4 blocks**
**Exit criterion:** every metric has a number, confidence interval, and dataset version

---

## 8. Phase 6 — Security and compliance (6-8 blocks)

### Block 6.1 — Threat model document
### Block 6.2 — Prompt-injection defense (untrusted source text, tool allow-listing, network restriction, adversarial tests)
### Block 6.3 — Auth hardening (email verification, MFA scaffolding, session revocation)
### Block 6.4 — RBAC enforcement tests on every sensitive endpoint
### Block 6.5 — Retention and deletion jobs (per source, tested)
### Block 6.6 — Source compliance matrix (terms, retention, display, review dates)

**Phase 6 total: 6 blocks**
**Exit criterion:** blueprint Gates A and F claimable

---

## 9. Phase 7 — Launch gates (4-6 blocks)

### Block 7.1 — Load test at 100 concurrent users / 100k documents (k6 or Locust)
### Block 7.2 — Restore drill (backup, restore, integrity check)
### Block 7.3 — Incident exercise (source outage, model-provider outage)
### Block 7.4 — Status page wiring
### Block 7.5 — Go/no-go checklist populated with real results

**Phase 7 total: 5 blocks**
**Exit criterion:** blueprint Gates B, D, E passed

---

## 10. Timeline summary

| Phase | Blocks | Sessions (2 blocks each) | Calendar (at 2/session/week) |
|---|---|---|---|
| 1 — Content correctness | 11 | 5-6 | 5-6 weeks |
| 2 — Source expansion | 8 | 4 | 4 weeks |
| 3 — Realtime | 6 | 3 | 3 weeks |
| 4 — UX/API | 6 | 3 | 3 weeks |
| 5 — Evaluation | 4 | 2 | 2 weeks |
| 6 — Security/compliance | 6 | 3 | 3 weeks |
| 7 — Launch gates | 5 | 2-3 | 2-3 weeks |
| **Total** | **46** | **22-24** | **22-24 weeks** |

At 2 blocks per week, honest estimate is **6 months of code work** to national-deployment-ready. At 4 blocks per week, ~3 months. Some phases will run faster (source connectors are mechanical), some slower (regeneration depends on LLM quality).

---

## 11. What only the user can do (I cannot deliver these from chat)

These must be in motion in parallel with the code work:

1. **Legal review (India)** — DPDP Act applicability, IT Rules, intermediary obligations, licensing terms. Requires a lawyer.
2. **Cloud account + India region + DNS + TLS** — commercial vendor selection.
3. **Free source registrations** — Stack Exchange, EPO OPS, Dev.to need ~5 minutes each to register.
4. **Independent security audit / penetration test** — before public launch.
5. **Support staffing** — someone must answer user reports and reviewer questions.
6. **On-call rotation and incident response team.**
7. **Budget** — LLM API spend, hosting, support.

The code can be national-ready; the service cannot launch without these seven.

---

## 12. Success criteria (measurable, testable)

### Content correctness (Phase 1)
- [ ] Every published opportunity has ≥1 evidence item with live URL, hash, license
- [ ] Every published score recomputes bit-identically from stored factor values and config version
- [ ] Every published confidence recomputes bit-identically from stored N, D, M, A components
- [ ] Every published gap stores search scope + retrieval limitations
- [ ] Every trend state stores the signals JSON that produced it
- [ ] Zero cards in PROPOSED status visible publicly
- [ ] Zero cards with domain='Other' or problem_type='Other'
- [ ] Zero duplicate opportunities in the public list
- [ ] User personally reviews 30 cards and confirms all are useful

### Source coverage (Phase 2)
- [ ] All 6 canonical source classes active
- [ ] Every source has an approved, current license record
- [ ] Zero fetch attempts against unapproved sources

### Realtime (Phase 3)
- [ ] Median chat latency <3s across 20 queries
- [ ] First token rendered within 500ms
- [ ] Forced crash loses no queued jobs

### UX (Phase 4)
- [ ] External user completes 5 core workflows without assistance
- [ ] WCAG 2.2 AA passed on 5 primary screens
- [ ] Mobile layout verified on mid-range device viewport

### Evaluation (Phase 5)
- [ ] Every metric has a number, CI, and dataset version
- [ ] CI runs metrics on every release

### Security/compliance (Phase 6)
- [ ] Threat model documented
- [ ] Prompt-injection adversarial tests pass
- [ ] RBAC verified on every sensitive endpoint

### Launch gates (Phase 7)
- [ ] Load test passes at 100 concurrent / 100k documents
- [ ] Restore drill passes
- [ ] Incident exercise passes
- [ ] Go/no-go checklist complete

### Honest definition of "100% accurate"
Not "every AI sentence is perfect." Yes:
Every claim on every card traces to a Document with a live URL, valid hash, and approved LicenseRecord. Every score and confidence recomputes bit-identically from stored inputs and a named config version. Every gap records what was searched and what was not found. Every trend state stores the signals that produced it. No card is shown with a validation status it has not earned. Every suggested direction is grounded in retrieved evidence.

---

## 13. Immediate next block

**Block 1.2c — Fix orchestrator to use the new columns (Block 1.2b added)**

File: `backend/app/agents/orchestrator.py`, lines ~560-568

Change:
- `"source_type": _ev.source or "unknown"` → `"source_type": _ev.source_type or "UNKNOWN"`
- `"credibility_weight": float(_ev.relevance_score or 0.5)` → `"credibility_weight": float(_ev.credibility_weight or 0.5)`
- `"doc_id": str(_ev.id)` → `"doc_id": str(_ev.doc_id) if _ev.doc_id else str(_ev.id)`

PASS: after patch, run a manual recompute on opportunity 1069 and confirm the confidence matches the formula's expected output. If yes, proceed to Block 1.2d (recompute all 378).

---

## 14. How to use this document

- This is the reference plan. Every block referenced here will be executed as a transactional patch with backup, ast.parse gate, and PASS criterion.
- No block is complete until it prints RESULT: PASS.
- No phase is complete until its exit criterion is met.
- No launch happens until Phase 7 passes.
- The user reviews each block's output before the next begins.

Every conversation going forward starts from this file. If a block is added, removed, or resequenced, this file is edited.

---

*End of plan. Written 2026-10-19, after diagnostic session confirmed the evidence pipeline was disconnected from the confidence formula and Block 1.2b fixed the evidence columns.*
