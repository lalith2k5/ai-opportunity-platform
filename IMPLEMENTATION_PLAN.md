# AI Opportunity Platform — Implementation Plan v2.0

**Version 2.0 · 19 October 2026**
**Supersedes v1.0. Architecture pivot to evidence-first, topic-scoped, no hardcoded values.*

---

## STATUS TRACKER (As of 19 Oct 2026)

- [x] **Infrastructure**: 8 sources built, Groq LLM live, Admin panel key management.
- [x] **Database Wipe**: 387 contaminated opportunities and all derived tables erased. Backup safely stored.
- [ ] **Phase 1 — Migration**: Add `runs` table + `run_id` columns + verification columns.
- [ ] **Phase 2 — Pipeline**: EvidenceVerifier + TopicScoper + Evidence-first extraction.
- [ ] **Phase 3 — First Run**: Target "drone delivery system". Yield: 3-10 100% defensible cards.
- [ ] **Phase 4 — API/UI**: Update endpoints to `/api/runs/...` and add run selector to frontend.

---
*

## 1. What this plan produces

A system where every pipeline run is scoped to one topic query, every claim traces to a live source document, every field is populated from real evidence, every score recomputes, and every source clickthrough works. Realistic output per run: 3-10 verified opportunities.

## 2. The 6 governing requirements

**R1 — Topic scoping**: every pipeline invocation creates a run with a topic query. Every entity carries run_id. API and UI scoped by run.

**R2 — Evidence-first**: problems, technologies, gaps extracted FROM source content. LLM structures what is written; it does not invent claims.

**R3 — No empty fields**: every published card has every required field populated. Any missing field -> card discarded.

**R4 — Source clickthrough verified**: every evidence item fetched, parsed, verified before attach. URL returns 200, content hash matches, LLM confirms claim support.

**R5 — Every field has a verifiable source**: every displayed field traces to a source document, quote, or deterministic computation. Weekly audit re-runs field tests.

**R6 — No cross-run aggregation**: trend counts computed only from same-run documents.

## 3. Field-by-field source map

| Field | Real source | Rejection |
|---|---|---|
| Title | Noun phrases from quotes | Noun not in source |
| Description | 3 sentences, each cites evidence | No evidence ID |
| Confidence | compute_confidence(N, D, M, A, C) | Recomputed != stored |
| Score | compute_score(7 factors) | Recomputed != stored |
| Domain | Vocab match from source | "Other" / NULL / not in source |
| Problem type | Vocab match from source | Same |
| Industry | Org metadata or source | NULL / "Other" / not in source |
| Stakeholders | Named entities from problem.quote | Empty / generic / not in quote |
| Technologies | Co-mentioned in same source | Not in evidence / catch-all |
| Existing research | Papers with problem AND tech terms | Not containing both |
| Known limitations | Verbatim quotes from papers | Non-verbatim |
| Gap (CAPABILITY) | Limitation + unmet requirement | Unconnected limitations |
| Gap (COVERAGE) | Search scope + zero results | "No research" without scope |
| Emerging trend | Time-windowed mention count | State without counts |
| Trend signal | Actual 30d/90d/365d counts + growth | Missing / mismatched |
| Suggested research direction | LLM composing from quotes only | Phrase not in evidence |
| Suggested project direction | LLM composing from quotes only | Phrase not in evidence |
| Explanation | Structured from factors + evidence | Free text adds claims |
| Weights version | weight_configs.version | Nonexistent / wrong |
| Confidence version | confidence_configs.version | Nonexistent / wrong |
| Trend window | 30 / 90 / 365 | Value not matching signal |
| Status | UNDER_REVIEW / VALIDATED | PROPOSED / DRAFT / null |
| Last verified at | Timestamp of URL check | NULL / >7d old |
| Evidence sources | URL 200 + hash match + claim verified | Any item failing |

## 4. New architecture

**runs table**: run_id UUID PK, topic_query TEXT, topic_variants JSONB, created_at, completed_at, status ENUM(RUNNING/COMPLETED/FAILED/EMPTY), config_versions JSONB, source_ids JSONB, documents_fetched, documents_gated, candidates_generated, opportunities_published, failure_log JSONB.

**Foreign keys**: opportunities, opportunity_evidence, research_gaps, problem_clusters, problem_technologies, trends, limitations, problem_papers — all gain run_id UUID FK (indexed).

**Verification columns** on opportunity_evidence: verified_at, http_status, content_hash_at_attach, claim_match, claim_match_reason, topic_match.

**Display gate**: verified_at > now()-7d AND http_status=200 AND claim_match=true AND topic_match=true.

## 5. Pipeline — 8 stages

1. **Topic resolution**: split query into 2-4 variants
2. **Source-scoped search**: query all sources, apply topic-relevance gate
3. **Problem extraction**: LLM extracts {problem, stakeholder, description, VERBATIM quote}. Non-verbatim -> discard
4. **Technology extraction**: LLM reads same source, extracts techs with own verbatim quotes. Problem quote + tech quote from same document
5. **Gap extraction**: search papers for stated limitations. CAPABILITY = problem+limitation quotes. COVERAGE = search-scope record
6. **Opportunity composition**: requires 1+ problem, 1+ tech, 1+ gap, 1+ stakeholder, 2+ evidence items, controlled vocab, trend state. Any missing -> discard
7. **Title/description**: spaCy extracts noun phrases from quotes -> LLM orders them (no invention) -> validate every noun traces to source. Description = 3 sentences citing evidence IDs
8. **5 verification gates**: topic match, completeness, source clickthrough, score reproducibility, no hardcoded values

## 6. Source coverage — 8 free sources

| Source | Status | Auth |
|---|---|---|
| Hacker News | Working | None |
| GDELT | Working | None |
| Crossref | Working | None (mailto polite) |
| OpenAlex | Working | Free key optional (100k/day) |
| Stack Exchange | Working | Keyless 300/day, key 10k/day |
| Dev.to | Working | None |
| USPTO ODP | Built | Free key needed |
| EPO OPS | Built | Free OAuth2 needed |

**Skipped**: Reddit (API closed).

**User action** (each 2 min):
- OpenAlex: openalex.org/action/register
- Stack Exchange: stackapps.com/apps/oauth/register
- USPTO: data.uspto.gov/myodp
- EPO OPS: developers.epo.org (non-paying tier)

## 7. Phase-by-phase implementation

| Phase | Blocks | Description | Exit |
|---|---|---|---|
| 0 Backup | 1 | pg_dump + verify restore | Restore works |
| 1 Migration | 2 | Alembic: runs table, run_id columns, verification columns | No data lost |
| 2 Erase | 1 | Truncate opportunities, evidence, gaps, trends, limitations, profiles, papers. Preserve raw_documents/users/configs | Counts verified |
| 3 Verification | 2 | EvidenceVerifier: fetch, hash, LLM claim match | 10/10 good PASS |
| 4 Topic search | 2 | TopicResolver + SourceScoper with gate | Returns 5-40 gated docs |
| 5 Extraction | 4-6 | Problem, tech, gap extraction with verbatim quotes | 5-15 problems from 20 docs |
| 6 Titles | 2 | PhraseExtractor + TitleComposer + provenance validator | 10/10 trace to source |
| 7 Gates | 2 | CardGatekeeper: 5 gates | Correct on test cases |
| 8 First run | 2 | Pipeline wired, run "drone delivery system" | 3-8 cards or honest EMPTY |
| 9 API scoping | 2 | /api/runs/*, deprecate /api/opportunities | Scoped return |
| 10 Frontend | 2 | Home shows runs, click scoped | Two runs isolated |
| 11 Human review | 1 | You read 3 cards, click evidence | Judge as 100% real |
| 12 Second topic | 1 | Run different topic | Isolation verified |
| 13 Corpus | 2 | New connectors at scale, re-run | Yield increases |

**Total: 30 blocks, 15 sessions, ~7 weeks at 2 sessions/week.**

## 8. What only the user can do

Legal review (DPDP, IT Rules, licensing) - Cloud account + India region + DNS + TLS - Free API registrations - Independent security audit - Support staffing - Budget - Legal sign-off on Terms/Privacy.

## 9. Success criteria

**Per run**: 5/5 gates PASS - every URL returns 200 with content matching claim - every field non-empty - every score recomputes - every title phrase traces to source - every description sentence cites evidence.

**Cross-runs**: zero shared opportunities - "drone" query returns 0 healthcare cards.

**Human**: 10 random cards per run, all judged real by user - every click works.

**System**: zero empty required fields - zero "Other" domain/type - zero score mismatches - zero cards with <2 verified evidence.

## 10. Honest yield expectations

- "drone delivery system": 3-8 cards
- "quantum computing": 5-10 cards
- "federated learning healthcare": 3-6 cards
- niche/emerging topic: 0-2 cards (honest EMPTY is valid)

**30-80 verified cards across 10 topics.** Every field traces to source. Every click works. That is the honest product.

---

*End of plan. Tonight: backup. Tomorrow: Phase 1 migration + Phase 2 erase + start Phase 3.*
