# AI Opportunity Discovery & Innovation Intelligence Platform

A multi-agent, evidence-driven platform that discovers real-world problems, maps them to technologies and research, identifies potential research gaps, and produces explainable, scored, ranked problem–technology opportunities.

Built to the **AI-Assisted Problem–Technology Opportunity Discovery Platform — System Specification** (18 Oct 2026).

---

## What This Does

Given a topic (e.g. "quantum computing", "healthcare AI"), the pipeline:

1. **Collects** from GitHub, arXiv, news RSS, R&D lab feeds, challenge portals, and patents
2. **Preprocesses** — cleans, deduplicates, normalizes, extracts metadata and provenance
3. **Extracts** structured problems, technologies, and research papers via LLM agents
4. **Discovers** recurring problem clusters, research gaps, and emerging trends
5. **Aggregates** evidence per opportunity — with per-source polarity and credibility
6. **Scores** every opportunity using the spec's 7-factor weighted formula
7. **Computes** a spec-compliant confidence score separately (evidence strength, not folded into score)
8. **Ranks** opportunities and exposes them via REST API and a React dashboard
9. **Queues** proposed research gaps for expert review (Module 18)
10. **Continuously updates** via a scheduler — re-collects, re-scores, sweeps conflicts, emits change events

---

## Quick Start

    bash ~/ai-opportunity-platform/op-start.sh

Then open:

| URL | What |
|-----|------|
| http://localhost:5173 | React frontend |
| https://localhost:8443 | HTTPS via Caddy |
| http://localhost:8000/docs | Backend API docs |
| http://localhost:8000/api/health | Health check |

Login: `test@example.com` / `test1234` (admin)

---

## Architecture

**Backend:** FastAPI + Python 3.12 + SQLAlchemy + PostgreSQL + ChromaDB + Caddy (dev HTTPS)
**Frontend:** React 19 + TypeScript + Tailwind + Vite + Recharts + react-force-graph-2d
**LLM:** Gemini `gemini-3.5-flash-lite` (500 RPD) with fallback chain → OpenRouter → OpenAI

### Agents (16)

| Agent | Purpose |
|-------|---------|
| Orchestrator | Coordinates pipeline; one-pipeline-at-a-time lock |
| DataCollection | Parallel fetch from 7 sources |
| NLP | Text cleaning, keywords, NER, sentiment |
| KnowledgeGraph | Nodes + canonical relations (spec §31) |
| ProblemDiscovery | TF-IDF + KMeans clustering |
| ResearchGap | Coverage + capability gap detection |
| InnovationMonitor | Trend classification |
| OpportunityIntelligence | 7-factor scoring (spec §33.2) |
| ExplainableAI | Human-readable score explanation |
| AIChat | RAG Q&A, entity-scoped |
| ProblemExtractor | Structured profile extraction via LLM |
| ProblemAgent | Canonical hash + dedup + provenance merge |
| TechnologyAgent | Extract technologies + stage classification |
| ResearchDiscovery | arXiv paper matching + limitations |
| EvidenceAgent | Multi-source evidence aggregation |
| ResearchDirection | LLM research + project directions |

---

## Spec Coverage

**Modules (§8–§27):** All 20 implemented.
**Functional requirements (FR-01 – FR-32):** All 32 implemented.

**Scoring (§33.2):** 7-factor weighted sum, configurable, versioned (`weight_configs`).

| Factor | Default Weight |
|--------|----------------|
| Problem strength | 0.20 |
| Technology suitability | 0.15 |
| Research gap strength | 0.20 |
| Trend strength | 0.15 |
| Evidence strength | 0.15 |
| Feasibility | 0.10 |
| Recency | 0.05 |

**Confidence (§33.3):** β-weighted (count / diversity / credibility / agreement) then reduced by conflict severity. Configurable via `confidence_configs`.

**Validation lifecycle (§25):** PROPOSED → UNDER_REVIEW → VALIDATED | REVISED | REJECTED. `/review` page wired.

**Conflict detection (§28.3):** CR-1..CR-6 in `conflict_detector.py`, swept every 15 min.

**Continuous update (§35):** Scheduler runs monitored pipeline every 6h + spec hooks every 15 min.

---

## API Surface

**Core:**
- `POST /api/auth/login`
- `POST /api/pipeline/run`
- `GET /api/opportunities` (filters: domain, industry, technology, problem_type)
- `GET /api/opportunities/{id}` (includes spec score + confidence + gap caveat)
- `GET /api/ideas`, `GET /api/ideas/{id}`
- `GET /api/technologies`, `GET /api/technologies/{name}`
- `GET /api/research-papers`, `GET /api/research-papers/{arxiv_id}`
- `GET /api/problem-profiles`, `GET /api/rd/problems/{id}`
- `POST /api/chat` (entity-scoped via context_kind + context_id)
- `GET /api/reports/pdf/{kind}/{id}` (5 kinds)

**Admin / Reviewer:**
- `GET /api/admin/review/queue`
- `POST /api/admin/review/gaps/{id}/decide`
- `GET /api/admin/evaluation/metrics`
- `POST /api/admin/evaluation/conflict-sweep`
- `GET /api/admin/scheduler`
- `GET /api/admin/pipeline/status`
- `GET /api/admin/data-sources`

---

## Database (26 tables)

**Core:** users, data_sources, raw_documents, processed_documents, problem_clusters, research_gaps, trends, opportunities, opportunity_score_history, recommendations, search_history, chat_sessions, chat_messages, agent_logs, reports, password_reset_tokens, notifications, kg_nodes, kg_edges, trend_snapshots, refresh_tokens, organizations, problem_profiles, problem_technologies, problem_papers, opportunity_evidence.

**Spec additions:** weight_configs, confidence_configs, trend_configs (versioned configs), conflict_flags, feedback, license_records, change_events, limitations (governance).

---

## Operations

    op-start    # start backend + frontend + caddy
    op-stop     # stop all
    op-status   # running state + health
    op-logs     # tail logs

**Migrations** (idempotent, run once after clone):

    cd backend && source venv/bin/activate
    python3 migrate_spec_alignment.py
    python3 migrate_spec_module18.py
    python3 backfill_spec_scores.py

---

## Testing

    cd backend && source venv/bin/activate
    python3 tests/test_e2e_spec.py

Runs 40+ endpoint checks, validates spec compliance, writes `/tmp/e2e_report.txt`, exits nonzero on failure (CI-safe).

---

## Configuration

Copy `backend/.env.example` to `backend/.env`, set:

    SECRET_KEY=<64-char random>
    DATABASE_URL=postgresql+psycopg2://localhost/ai_opportunity_db
    GEMINI_API_KEY=<aistudio.google.com>
    GEMINI_MODEL=gemini-3.5-flash-lite

Optional: OPENROUTER_API_KEY, OPENAI_API_KEY, GITHUB_TOKEN, PATENTSVIEW_API_KEY, REDDIT_CLIENT_ID/SECRET.

---

## Known Limitations

- PatentsView key currently unavailable — patents source dormant
- Reddit unconfigured — code path exists, credentials deferred
- SBIR API returns 403 from datacenter IPs — RSS fallback covers it
- Auto-hooks run every 15 min (spec §35.3 allows 24h, so well within tolerance)
- License gate is warn-only; enforcement deferred
- Notification delivery — thresholds logged, delivery loop deferred

---

## Repository

https://github.com/lalith2k5/ai-opportunity-platform
