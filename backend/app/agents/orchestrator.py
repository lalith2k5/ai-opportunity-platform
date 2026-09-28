from app.agents.data_collection import DataCollectionAgent
from app.agents.nlp_agent import NLPAgent
from app.agents.knowledge_graph import KnowledgeGraphAgent
from app.agents.problem_discovery import ProblemDiscoveryAgent
from app.agents.research_gap import ResearchGapAgent
from app.agents.innovation_monitor import InnovationMonitorAgent
from app.agents.opportunity_intelligence import OpportunityIntelligenceAgent
from app.agents.explainable_ai import ExplainableAIAgent
from app.services.embedding_service import EmbeddingService
from app.database import SessionLocal
from app import models
from sqlalchemy import select
from app.logger import logger
from app.services.notification_service import generate_pipeline_notifications
from app.services.challenge_portal_service import ChallengePortalService
from app.agents.problem_extractor import ProblemExtractorAgent
from app.agents.problem_agent import ProblemAgent
from app.agents.technology_agent import TechnologyAgent
from app.agents.research_discovery_agent import ResearchDiscoveryAgent
from app.agents.evidence_agent import EvidenceAgent
from app.agents.research_direction_agent import ResearchDirectionAgent

from sqlalchemy import inspect as _sa_inspect

import threading

# Global lock — only one pipeline can run at a time, across all OrchestratorAgent instances.
# Prevents scheduler + user-triggered runs from colliding (ChromaDB writes, KG persists).
_PIPELINE_LOCK = threading.Lock()


class OrchestratorAgent:
    def __init__(self):
        self.data_collection = DataCollectionAgent()
        self.nlp = NLPAgent()
        self.kg = KnowledgeGraphAgent()
        self.problem_discovery = ProblemDiscoveryAgent()
        self.research_gap = ResearchGapAgent()
        self.innovation_monitor = InnovationMonitorAgent()
        self.opportunity = OpportunityIntelligenceAgent()
        self.explainable = ExplainableAIAgent()
        self.embedding = EmbeddingService()
        self.challenge_portal = ChallengePortalService()
        self.problem_extractor = ProblemExtractorAgent()
        self.problem_agent = ProblemAgent()
        self.technology_agent = TechnologyAgent()
        self.research_discovery_agent = ResearchDiscoveryAgent()
        self.evidence_agent = EvidenceAgent()
        self.research_direction_agent = ResearchDirectionAgent()

    def _save_problem_profiles(self, profiles: list):
        """Persist extracted ProblemProfile rows.

        Dedup layers (first match short-circuits):
          1. Intra-batch: ProblemAgent.dedup() collapses near-dupes by
             canonical_hash before any DB lookups.
          2. Exact source_url match (strongest provenance signal).
          3. canonical_hash match (catches title variants across runs/sources).
          4. Exact problem_title fallback (for legacy rows without a hash).
        """
        if not profiles:
            return 0
        from app.database import SessionLocal as _SL
        db = _SL()
        inserted = 0
        skipped = 0
        merged = 0
        try:
            # Layer 1: intra-batch dedup
            before = len(profiles)
            profiles = self.problem_agent.dedup(profiles)
            intra_batch_skipped = before - len(profiles)

            for pr in profiles:
                key_url = (pr.get("source_url") or "").strip()
                key_title = (pr.get("problem_title") or "").strip()[:200]
                canonical_hash = pr.get("_canonical_hash") or self.problem_agent.compute_hash(key_title)

                # Look up the existing row (if any) via the four-layer chain
                existing_row = None
                # Layer 2: exact source_url
                if key_url:
                    existing_row = db.query(models.ProblemProfile).filter(
                        models.ProblemProfile.source_url == key_url
                    ).first()
                # Layer 3: canonical_hash
                if not existing_row and canonical_hash:
                    existing_row = db.query(models.ProblemProfile).filter(
                        models.ProblemProfile.canonical_hash == canonical_hash
                    ).first()
                # Layer 4: exact title (legacy fallback)
                if not existing_row and key_title:
                    existing_row = db.query(models.ProblemProfile).filter(
                        models.ProblemProfile.problem_title == key_title
                    ).first()

                if existing_row:
                    # Cross-source merge: enrich the existing row with the
                    # new source's provenance, keywords, and technologies.
                    if self.problem_agent.merge_provenance(existing_row, pr):
                        merged += 1
                    else:
                        skipped += 1
                    continue

                db.add(models.ProblemProfile(
                    organization=pr.get("organization", "")[:500],
                    problem_title=pr.get("problem_title", "")[:500],
                    canonical_hash=canonical_hash or None,
                    problem_description=pr.get("problem_description", ""),
                    industry_domain=pr.get("industry_domain", "Other"),
                    problem_type=pr.get("problem_type", "Other"),
                    technology_stage=pr.get("technology_stage", "potential"),
                    required_technology=pr.get("required_technology", []),
                    current_approach=pr.get("current_approach", ""),
                    known_limitations=pr.get("known_limitations", ""),
                    expected_outcome=pr.get("expected_outcome", ""),
                    source=pr.get("source", "unknown"),
                    source_url=pr.get("source_url", ""),
                    keywords=pr.get("keywords", []),
                    problem_status=pr.get("problem_status", "unknown"),
                    student_suitability=pr.get("student_suitability", "medium"),
                    affected_stakeholders=pr.get("affected_stakeholders") or [],
                    evidence=pr.get("evidence") or [],
                    confidence=float(pr.get("confidence") or 0.5),
                    extracted_by=pr.get("extracted_by", "unknown"),
                ))
                inserted += 1
            db.commit()
            logger.info(
                f"Saved {inserted} new ProblemProfile rows "
                f"({merged} cross-source merged, {skipped} exact dupes, "
                f"{intra_batch_skipped} intra-batch dupes skipped)"
            )
            return inserted
        except Exception as e:
            db.rollback()
            logger.error(f"ProblemProfile save error: {e}")
            return 0
        finally:
            db.close()

    @staticmethod
    def _row_id(obj):
        """Return the PK of a possibly-detached ORM instance without
        triggering a lazy refresh. Falls back to __dict__ lookup."""
        ident = _sa_inspect(obj).identity
        if ident:
            return ident[0]
        return obj.__dict__.get("id")

    def _save_technologies(self, profile_rows_with_techs: list):
        """Persist problem_technologies rows. Skips exact (profile, name) dups."""
        if not profile_rows_with_techs:
            return 0
        from app.database import SessionLocal as _SL
        db = _SL()
        inserted = 0
        try:
            # Collect existing (profile_id, lower(name)) to avoid dup inserts
            existing = set()
            for pid, name in db.query(
                models.ProblemTechnology.problem_profile_id,
                models.ProblemTechnology.technology_name,
            ).all():
                existing.add((pid, (name or "").lower()))

            for row, techs in profile_rows_with_techs:
                pid = self._row_id(row)
                if pid is None:
                    continue
                for t in techs:
                    key = (pid, (t["name"] or "").lower())
                    if key in existing:
                        continue
                    db.add(models.ProblemTechnology(
                        problem_profile_id=pid,
                        technology_name=t["name"],
                        stage=t["stage"],
                        confidence=t["confidence"],
                        evidence=t.get("evidence") or "",
                    ))
                    existing.add(key)
                    inserted += 1
            db.commit()
            logger.info(f"Saved {inserted} new ProblemTechnology rows")
            return inserted
        except Exception as e:
            db.rollback()
            logger.error(f"ProblemTechnology save error: {e}")
            return 0
        finally:
            db.close()

    def _save_problem_papers(self, profile_rows_with_papers: list):
        """Persist problem_papers rows. Skips exact (profile_id, arxiv_id) dups."""
        if not profile_rows_with_papers:
            return 0
        from app.database import SessionLocal as _SL
        db = _SL()
        inserted = 0
        try:
            existing = set()
            for pid, ax in db.query(
                models.ProblemPaper.problem_profile_id,
                models.ProblemPaper.arxiv_id,
            ).all():
                existing.add((pid, ax or ""))

            for row, papers in profile_rows_with_papers:
                pid = self._row_id(row)
                if pid is None:
                    continue
                for p in papers:
                    key = (pid, p.get("arxiv_id") or "")
                    if not key[1] or key in existing:
                        continue
                    db.add(models.ProblemPaper(
                        problem_profile_id=pid,
                        arxiv_id=p["arxiv_id"],
                        title=p.get("title") or "",
                        authors=p.get("authors") or [],
                        abstract=p.get("abstract") or "",
                        url=p.get("url") or "",
                        relevance_score=p.get("relevance_score") or 0.5,
                        limitations=p.get("limitations") or [],
                        research_methods=p.get("research_methods") or [],
                        results_summary=p.get("results_summary") or "",
                        research_areas=p.get("research_areas") or [],
                        published=p.get("published") or "",
                    ))
                    existing.add(key)
                    inserted += 1
            db.commit()
            logger.info(f"Saved {inserted} new ProblemPaper rows")
            return inserted
        except Exception as e:
            db.rollback()
            logger.error(f"ProblemPaper save error: {e}")
            return 0
        finally:
            db.close()

    def _save_evidence(self, opportunity_rows_with_evidence: list):
        """Persist opportunity_evidence rows. Skips exact (opp_id, url) dups."""
        if not opportunity_rows_with_evidence:
            return 0
        from app.database import SessionLocal as _SL
        db = _SL()
        inserted = 0
        try:
            existing = set()
            for oid, url in db.query(
                models.OpportunityEvidence.opportunity_id,
                models.OpportunityEvidence.url,
            ).all():
                existing.add((oid, url or ""))

            for opp, items in opportunity_rows_with_evidence:
                opp_id = self._row_id(opp)
                if opp_id is None:
                    continue
                for e in items:
                    key = (opp_id, e.get("url") or "")
                    if not key[1] or key in existing:
                        continue
                    db.add(models.OpportunityEvidence(
                        opportunity_id=opp_id,
                        source=e["source"],
                        title=e.get("title") or "",
                        url=key[1],
                        relevance_score=e.get("relevance_score") or 0.0,
                        snippet=e.get("snippet") or "",
                    ))
                    existing.add(key)
                    inserted += 1
            db.commit()
            logger.info(f"Saved {inserted} new OpportunityEvidence rows")
            return inserted
        except Exception as e:
            db.rollback()
            logger.error(f"OpportunityEvidence save error: {e}")
            return 0
        finally:
            db.close()

    def _enrich_opportunities(self, opp_ids=None):
        """Populate the 10 Phase-6 enrichment columns for recent opportunities.

        Data-derived fields (technologies, papers, approaches, limitations,
        trend, evidence sources, domain, industry) come from Phase 2/3/4
        tables. Two LLM-derived fields (suggested_research_direction and
        suggested_project_direction) are generated by ResearchDirectionAgent.
        Idempotent — recomputes values each run.
        """
        from app.database import SessionLocal as _SL

        db = _SL()
        try:
            if opp_ids:
                opps = (
                    db.query(models.Opportunity)
                    .filter(models.Opportunity.id.in_(opp_ids))
                    .all()
                )
            else:
                opps = (
                    db.query(models.Opportunity)
                    .order_by(models.Opportunity.id.desc())
                    .limit(50)
                    .all()
                )
            if not opps:
                return {"updated": 0}

            # Preload tables we need
            all_profiles = db.query(models.ProblemProfile).all()
            all_techs = db.query(models.ProblemTechnology).all()
            all_papers = db.query(models.ProblemPaper).all()
            all_evidence = db.query(models.OpportunityEvidence).all()
            all_trends = db.query(models.Trend).all()
            clusters_by_id = {c.id: c for c in db.query(models.ProblemCluster).all()}

            techs_by_profile = {}
            for t in all_techs:
                techs_by_profile.setdefault(t.problem_profile_id, []).append(t)
            papers_by_profile = {}
            for p in all_papers:
                papers_by_profile.setdefault(p.problem_profile_id, []).append(p)
            evidence_by_opp = {}
            for e in all_evidence:
                evidence_by_opp.setdefault(e.opportunity_id, []).append(e)

            # Map cluster -> best matching profile (via keyword overlap).
            # Threshold lowered to >= 1 after observing that many real
            # clusters share only one meaningful keyword with any profile.
            # Fallback: if no profile clears the threshold, use the
            # best-scoring one as long as it has at least one keyword.
            # Pre-compute profile embeddings once for semantic fallback.
            # Local SentenceTransformer only -- no LLM, no quota burn.
            profile_embs = None
            if all_profiles:
                try:
                    _ptexts = [
                        ((p.problem_title or "") + " " + " ".join(
                            str(k) for k in (p.keywords or [])[:10]
                        ))[:500]
                        for p in all_profiles
                    ]
                    profile_embs = self.embedding.model.encode(
                        _ptexts, normalize_embeddings=True, batch_size=32
                    )
                    logger.info(
                        f"[Enrichment] precomputed {len(_ptexts)} profile embeddings"
                    )
                except Exception as _e:
                    logger.warning(f"[Enrichment] profile embedding failed: {_e}")
                    profile_embs = None

            def best_profile_for_cluster(cluster):
                if not cluster or not cluster.keywords:
                    return None
                ck = {str(k).lower() for k in cluster.keywords[:10] if k}
                if not ck:
                    return None
                # Pass 1: exact keyword overlap
                best, best_n = None, 0
                for p in all_profiles:
                    pk = {str(k).lower() for k in (p.keywords or [])[:10] if k}
                    n = len(ck & pk)
                    if n > best_n:
                        best, best_n = p, n
                if best is not None:
                    return best
                # Pass 2: semantic fallback (cosine on local embeddings)
                if profile_embs is None:
                    return None
                try:
                    ctext = ((cluster.title or "") + " " + " ".join(
                        str(k) for k in (cluster.keywords or [])[:10]
                    ))[:500]
                    c_emb = self.embedding.model.encode(
                        [ctext], normalize_embeddings=True
                    )[0]
                    sims = profile_embs @ c_emb
                    idx = int(sims.argmax())
                    if float(sims[idx]) >= 0.30:
                        logger.debug(
                            f"[Enrichment] semantic match cluster->profile "
                            f"(sim={float(sims[idx]):.3f})"
                        )
                        return all_profiles[idx]
                except Exception as _e:
                    logger.warning(f"[Enrichment] semantic match failed: {_e}")
                return None

            snapshots = []
            for opp in opps:
                cluster = clusters_by_id.get(opp.problem_cluster_id)
                profile = best_profile_for_cluster(cluster)
                techs = techs_by_profile.get(profile.id, []) if profile else []
                papers = papers_by_profile.get(profile.id, []) if profile else []
                evs = evidence_by_opp.get(opp.id, [])

                # Data-derived
                opp.domain = (profile.industry_domain if profile else None) or opp.domain
                opp.industry = opp.domain
                opp.related_technologies = [t.technology_name for t in techs][:12]
                opp.existing_research = [p.title for p in papers][:10]
                approaches = " | ".join(
                    (p.abstract or "")[:220] for p in papers[:3] if p.abstract
                )
                opp.existing_approaches = approaches[:2000]
                # Limitations: union of all papers' limitations
                lims = []
                for p in papers:
                    for L in (p.limitations or []):
                        s = str(L).strip()
                        if s and s not in lims:
                            lims.append(s)
                opp.known_limitations = " | ".join(lims[:10])[:2000]
                # Emerging trend: pick best matching trend by name keyword
                tnames = [t.technology_name.lower() for t in techs]
                best_trend = None
                for tr in all_trends:
                    trn = (tr.name or "").lower()
                    if not trn:
                        continue
                    if any(trn in t or t in trn for t in tnames):
                        if best_trend is None or (tr.trend_score or 0) > (best_trend.trend_score or 0):
                            best_trend = tr
                opp.emerging_trend = (best_trend.name if best_trend else None) or opp.emerging_trend
                opp.evidence_sources = [
                    {"source": e.source, "url": e.url, "title": e.title}
                    for e in evs[:12]
                ]

                # ---- Phase 10.3: recompute 3 new SRS 21 scoring factors ----
                try:
                    _profile_techs = [
                        {
                            "name": t.technology_name,
                            "stage": t.stage,
                            "confidence": t.confidence,
                        }
                        for t in (techs or [])
                    ]
                    opp.technology_suitability_score = (
                        self.opportunity._derive_technology_suitability_score(
                            _profile_techs, []
                        )
                    )
                    opp.evidence_strength_score = (
                        self.opportunity._derive_evidence_strength_score(len(evs))
                    )
                    opp.recency_score = self.opportunity._derive_recency_score(
                        opp.created_at
                    )
                except Exception as _e:
                    logger.warning(f"[Enrichment] new-score calc failed: {_e}")

                snapshots.append({
                    "opportunity_row": opp,
                    "title": opp.title,
                    "description": opp.description,
                    "domain": opp.domain,
                    "technologies": opp.related_technologies,
                    "papers": opp.existing_research,
                    "limitations": lims[:5],
                    "trend": opp.emerging_trend,
                })

            # LLM-derived directions
            direction_results = self.research_direction_agent.generate_batch(snapshots)
            for row, out in direction_results:
                if out.get("suggested_research_direction"):
                    row.suggested_research_direction = out["suggested_research_direction"][:1500]
                if out.get("suggested_project_direction"):
                    row.suggested_project_direction = out["suggested_project_direction"][:1500]

            db.commit()
            logger.info(
                f"Enriched {len(opps)} opportunities "
                f"({len(direction_results)} with LLM directions)"
            )
            return {"updated": len(opps), "llm_directions": len(direction_results)}
        except Exception as e:
            db.rollback()
            logger.error(f"Opportunity enrichment error: {e}")
            return {"updated": 0, "error": str(e)}
        finally:
            db.close()

    def _snapshot_and_notify(self):
        """Phase 8.2/8.3: snapshot top-N opportunity scores + emit rank alerts.

        For the top 100 opportunities by current score:
          - Insert a new row into opportunity_score_history.
          - Compare to the previous snapshot; if the rank jumped by
            RANK_DELTA_THRESHOLD or more places, create a Notification
            for the user's attention.
        Returns a small stats dict.
        """
        from app.database import SessionLocal as _SL
        from app.services.notification_service import create_notification

        RANK_DELTA_THRESHOLD = 5
        TOP_N = 100

        db = _SL()
        try:
            opps = (
                db.query(models.Opportunity)
                .order_by(models.Opportunity.opportunity_score.desc())
                .limit(TOP_N)
                .all()
            )
            if not opps:
                return {"snapshots": 0, "rank_changes": 0}

            # Fetch previous snapshot ranks (latest per opportunity)
            opp_ids = [o.id for o in opps]
            prev_ranks = {}
            prev_rows = (
                db.query(models.OpportunityScoreHistory)
                .filter(models.OpportunityScoreHistory.opportunity_id.in_(opp_ids))
                .order_by(models.OpportunityScoreHistory.recorded_at.desc())
                .all()
            )
            for r in prev_rows:
                if r.opportunity_id not in prev_ranks:
                    prev_ranks[r.opportunity_id] = r.rank

            snapshots = 0
            rank_changes = 0
            for i, o in enumerate(opps, start=1):
                db.add(models.OpportunityScoreHistory(
                    opportunity_id=o.id,
                    opportunity_score=o.opportunity_score or 0.0,
                    rank=i,
                ))
                snapshots += 1

                prev = prev_ranks.get(o.id)
                if prev is None:
                    continue
                delta = prev - i   # positive = moved up
                if abs(delta) >= RANK_DELTA_THRESHOLD:
                    direction = "up" if delta > 0 else "down"
                    try:
                        create_notification(
                            "rank_change",
                            f"Opportunity {direction} {abs(delta)} places: {(o.title or '')[:80]}",
                            f"Now ranked #{i} (was #{prev}). Score {o.opportunity_score:.2f}.",
                            link=f"/opportunities/{o.id}",
                            severity="success" if direction == "up" else "warning",
                        )
                        rank_changes += 1
                    except Exception as e:
                        logger.warning(f"[ScoreSnapshot] notification failed: {e}")

            db.commit()
            logger.info(
                f"[ScoreSnapshot] snapshots={snapshots} rank_changes={rank_changes}"
            )
            return {"snapshots": snapshots, "rank_changes": rank_changes}
        except Exception as e:
            db.rollback()
            logger.error(f"[ScoreSnapshot] error: {e}")
            return {"snapshots": 0, "rank_changes": 0, "error": str(e)}
        finally:
            db.close()

    def _save_to_db(self, query, raw, processed, clusters, gaps, trends, opportunities, user_id=None):
        db = SessionLocal()
        try:
            # 1. Save raw documents with dedup — track new docs for embedding
            inserted = 0
            newly_inserted_docs = []
            for source_name, items in raw.items():
                for item in items:
                    title = item.get("title") or item.get("name") or ""
                    content = item.get("summary") or item.get("selftext") or item.get("description") or ""

                    # Stable external_id: prefer source id, fall back to URL, then title hash.
                    # This makes dedup work for every source (news/RSS has no id field).
                    ext_id = str(item.get("id", "") or "")
                    if not ext_id:
                        ext_id = str(item.get("url", "") or item.get("html_url", "") or "")
                    if not ext_id:
                        import hashlib as _hl
                        ext_id = "title:" + _hl.sha1(title.encode("utf-8")).hexdigest()[:16]

                    exists = db.execute(
                        select(models.RawDocument.id).where(
                            models.RawDocument.source == source_name,
                            models.RawDocument.external_id == ext_id,
                        )
                    ).first()
                    if exists:
                        continue

                    url = item.get("url", item.get("html_url", ""))
                    metadata = {"keys": list(item.keys())}
                    if source_name == "rd_cells":
                        metadata["lab"] = item.get("lab", "unknown")
                    raw_doc = models.RawDocument(
                        source=source_name,
                        external_id=ext_id,
                        title=title,
                        content=content[:5000],
                        url=url,
                        metadata_json=metadata,
                    )
                    db.add(raw_doc)
                    inserted += 1

                    text = (title + " " + content)[:1000]
                    if text.strip():
                        newly_inserted_docs.append((text, {"source": source_name}))
            logger.info(f"Inserted {inserted} new raw documents")

            if newly_inserted_docs:
                try:
                    texts = [t for t, _ in newly_inserted_docs]
                    metas = [m for _, m in newly_inserted_docs]
                    self.embedding.add_documents(texts, metadatas=metas)
                    logger.info(f"Embedded {len(texts)} NEW docs (skipped duplicates)")
                except Exception as e:
                    logger.error(f"Embedding error: {e}")
            else:
                logger.info("No new documents to embed")

            # 1b. Save ProcessedDocument rows linked to their RawDocument
            processed_inserted = 0
            if processed:
                # Force pending raw_doc inserts into the transaction's view before
                # querying them back. SessionLocal is configured with autoflush=False,
                # so without this the query below cannot see raw documents added
                # earlier in this same call — the result is that processed documents
                # for brand-new sources are silently dropped.
                db.flush()
                all_raw = db.query(models.RawDocument).all()
                raw_index = {}
                for rd in all_raw:
                    key = (rd.source or "", (rd.title or "").strip()[:200])
                    if key not in raw_index:
                        raw_index[key] = rd.id

                existing_pd_raw_ids = {
                    row[0] for row in db.query(models.ProcessedDocument.raw_document_id).all()
                }

                for pdoc in processed:
                    src_name = pdoc.get("source") or "unknown"
                    title = (pdoc.get("title") or "").strip()[:200]
                    raw_id = raw_index.get((src_name, title))
                    if raw_id is None:
                        continue
                    if raw_id in existing_pd_raw_ids:
                        continue

                    db.add(models.ProcessedDocument(
                        raw_document_id=raw_id,
                        cleaned_text=(pdoc.get("cleaned_text") or "")[:10000],
                        keywords=pdoc.get("keywords") or [],
                        entities=pdoc.get("entities") or [],
                        topics=pdoc.get("topics") or [],
                        sentiment_score=float(pdoc.get("sentiment_score") or 0.0),
                        embedding_id=None,
                    ))
                    processed_inserted += 1

                logger.info(f"Inserted {processed_inserted} new processed documents")

            # 2. Save problem clusters
            cluster_ids = []
            for cluster in clusters:
                pc = models.ProblemCluster(
                    title=cluster.get("title", ""),
                    description=cluster.get("description", ""),
                    keywords=cluster.get("keywords", []),
                    source_count=cluster.get("source_count", 0),
                    demand_score=cluster.get("demand_score", 0.0),
                )
                db.add(pc)
                db.flush()
                cluster_ids.append(pc.id)

            # 3. Save research gaps
            gap_ids = []
            for i, gap in enumerate(gaps):
                rg = models.ResearchGap(
                    title=gap.get("title", ""),
                    description=gap.get("description", ""),
                    problem_cluster_id=cluster_ids[i] if i < len(cluster_ids) else None,
                    gap_score=gap.get("gap_score", 0.0),
                    evidence=gap.get("evidence", {}),
                )
                db.add(rg)
                db.flush()
                gap_ids.append(rg.id)

            # 4. Save trends + snapshot them for time-series analysis
            for trend in trends:
                name = trend.get("name", "")
                if not name:
                    continue
                source_data = trend.get("source_data", {}) or {}
                db.add(models.Trend(
                    name=name,
                    category=trend.get("category", "general"),
                    trend_score=trend.get("trend_score", 0.0),
                    source_data=source_data,
                ))
                # Snapshot for growth-rate computation
                db.add(models.TrendSnapshot(
                    trend_name=name[:200],
                    mention_count=int(source_data.get("mentions", 0) or 0),
                    source_count=len(source_data.get("sources", {}) or {}),
                ))

            # 5. Save opportunities
            for i, opp in enumerate(opportunities):
                db.add(models.Opportunity(
                    title=opp.get("title", ""),
                    description=opp.get("description", ""),
                    problem_cluster_id=cluster_ids[i] if i < len(cluster_ids) else None,
                    research_gap_id=gap_ids[i] if i < len(gap_ids) else None,
                    demand_score=opp.get("demand_score", 0.0),
                    research_gap_score=opp.get("research_gap_score", 0.0),
                    trend_score=opp.get("trend_score", 0.0),
                    innovation_score=opp.get("innovation_score", 0.0),
                    competition_score=opp.get("competition_score", 0.0),
                    feasibility_score=opp.get("feasibility_score", 0.0),
                    market_readiness_score=opp.get("market_readiness_score", 0.0),
                    confidence_score=opp.get("confidence_score", 0.0),
                    opportunity_score=opp.get("opportunity_score", 0.0),
                    explanation=opp.get("explanation", ""),
                ))

            # 6. Log search history
            logger.debug(f"DB operation: insert_search_history query={query[:40]}")
            db.add(models.SearchHistory(
                user_id=user_id,
                query=query,
                results_count=len(opportunities),
            ))

            import time as _t
            _t0 = _t.time()
            db.commit()
            _ms = int((_t.time() - _t0) * 1000)
            logger.info(f"DB operation: commit_pipeline ({_ms}ms)")

            generate_pipeline_notifications(opportunities, gaps, trends, query)
            logger.info(f"Saved: {len(clusters)} clusters, {len(gaps)} gaps, {len(trends)} trends, {len(opportunities)} opps")
        except Exception as e:
            db.rollback()
            logger.error(f"DB save error: {e}")
        finally:
            db.close()

    def run_full_pipeline(self, query: str, user_id: int = None, mode: str = "quick") -> dict:
        # Refuse to start if another pipeline is already running
        acquired = _PIPELINE_LOCK.acquire(blocking=False)
        if not acquired:
            logger.warning(f"[Orchestrator] Pipeline already running — refusing concurrent run for '{query}'")
            raise RuntimeError("Another pipeline is already running. Please wait for it to finish.")

        try:
            return self._run_full_pipeline_inner(query, user_id=user_id, mode=mode)
        finally:
            _PIPELINE_LOCK.release()

    def _run_full_pipeline_inner(self, query: str, user_id: int = None, mode: str = "quick") -> dict:
        logger.info(f"Starting pipeline for: {query} (mode={mode})")
        raw = self.data_collection.collect_all(query, mode=mode)

        # ---- Challenge portals (industry/gov problem statements) ----
        challenge_items = []
        try:
            from app.config import settings as _s
            from app.database import SessionLocal as _SLcp
            from app import models as _mcp
            _cp_active = True
            _dbcp = _SLcp()
            try:
                _row = _dbcp.query(_mcp.DataSource).filter(
                    _mcp.DataSource.name == "challenge_portal"
                ).first()
                if _row is not None and not _row.is_active:
                    _cp_active = False
            finally:
                _dbcp.close()
            if _s.ENABLE_CHALLENGE_PORTALS and _cp_active:
                challenge_items = self.challenge_portal.fetch_all(query, limit=_s.CHALLENGE_PORTAL_CAP)
                raw["challenge_portal"] = challenge_items
            elif not _cp_active:
                logger.info("[Pipeline] challenge_portal DataSource is disabled -- skipping")
        except Exception as e:
            logger.warning(f"Challenge portal fetch failed: {e}")

        documents = []
        for repo in raw.get("github", [])[:200]:
            documents.append({"source": "github", "title": repo.get("name", ""), "content": repo.get("description", "") or ""})
        for issue in raw.get("github_issues", [])[:200]:
            documents.append({"source": "github_issues", "title": issue.get("title", ""), "content": issue.get("summary", "")})
        for post in raw.get("reddit", [])[:200]:
            documents.append({"source": "reddit", "title": post.get("title", ""), "content": post.get("selftext", "")})
        for paper in raw.get("arxiv", [])[:200]:
            documents.append({"source": "arxiv", "title": paper.get("title", ""), "content": paper.get("summary", "")})
        for article in raw.get("news", [])[:200]:
            documents.append({"source": "news", "title": article.get("title", ""), "content": article.get("summary", "")})
        for post in raw.get("rd_cells", [])[:200]:
            documents.append({"source": "rd_cells", "title": post.get("title", ""), "content": post.get("summary", "")})
        for patent in raw.get("patents", [])[:200]:
            documents.append({"source": "patents", "title": patent.get("title", ""), "content": patent.get("summary", "")})
        for post in raw.get("challenge_portal", [])[:200]:
            documents.append({"source": "challenge_portal", "title": post.get("title", ""), "content": post.get("raw_text", "") or post.get("description", "")})

        logger.info(f"Processing {len(documents)} documents")
        processed = []
        for doc in documents:
            nlp_result = self.nlp.process(doc.get("title", "") + " " + doc.get("content", ""))
            processed.append({**doc, **nlp_result})

        # Global topic modeling across all documents
        try:
            all_texts = [d.get("title", "") + " " + (d.get("content", "") or "")[:500] for d in processed]
            global_topics = self.nlp.extract_topics_nmf(all_texts, n_topics=5)
            logger.info(f"Topic modeling found {len(global_topics)} topics")
        except Exception as e:
            global_topics = []
            logger.error(f"Topic modeling error: {e}")

        # Assign each document to its closest global NMF topic by keyword overlap.
        # This turns the fake per-doc `topics` (which used to duplicate keywords)
        # into a real topic label from the corpus-wide model.
        if global_topics:
            topic_keyword_sets = [
                set(k.lower() for k in (t.get("keywords") or []))
                for t in global_topics
            ]
            for doc in processed:
                doc_kws = set(k.lower() for k in (doc.get("keywords") or []))
                best_idx, best_overlap = -1, 0
                for idx, tset in enumerate(topic_keyword_sets):
                    overlap = len(doc_kws & tset)
                    if overlap > best_overlap:
                        best_overlap = overlap
                        best_idx = idx
                if best_idx >= 0 and best_overlap > 0:
                    topic = global_topics[best_idx]
                    label = topic.get("label") or ", ".join(topic.get("keywords", [])[:2])
                    if label:
                        doc["primary_topic"] = label
                        doc["topics"] = [label]
            assigned = sum(1 for d in processed if d.get("primary_topic"))
            logger.info(f"Assigned {assigned}/{len(processed)} docs to NMF topics")

        clusters = self.problem_discovery.discover(processed)
        gaps = self.research_gap.detect_gaps(clusters, raw.get("arxiv", []))
        trends = self.innovation_monitor.monitor(processed, clusters=clusters)

        # Per-cluster average sentiment (VADER compound in [-1, 1])
        for cluster in clusters:
            doc_indices = cluster.get("_doc_indices", [])
            sents = [
                float(processed[i].get("sentiment_score") or 0.0)
                for i in doc_indices if 0 <= i < len(processed)
            ]
            cluster["_avg_sentiment"] = (sum(sents) / len(sents)) if sents else 0.0

        opportunities = []
        for i, cluster in enumerate(clusters):
            gap = gaps[i] if i < len(gaps) else None
            trend = trends[i] if i < len(trends) else None
            opp = self.opportunity.score(
                cluster, gap, trend,
                github_items=raw.get("github", []),
                arxiv_items=raw.get("arxiv", []),
                news_items=raw.get("news", []),
                raw_items=raw,
                avg_sentiment=cluster.get("_avg_sentiment"),
            )
            opp["explanation"] = self.explainable.explain(opp)
            opp["_cluster_title"] = (cluster.get("title") or "").replace("Problem Cluster:", "").strip()
            opp["_gap_title"] = gap.get("title") if gap else None
            opportunities.append(opp)

        # Build + persist knowledge graph (Document + NER + Topic + semantic layers)
        self.kg.build_from_documents(processed)
        kg_stats = self.kg.build_semantic_graph(raw, clusters, gaps, opportunities, global_topics)
        self.kg.persist()

        self._save_to_db(query, raw, processed, clusters, gaps, trends, opportunities, user_id=user_id)

        # ---- Extract structured Problem Profiles from ALL sources ----
        # Each extraction = 1 LLM call. Caps are per-source so one noisy
        # source cannot monopolize the extraction budget. Sources with
        # empty results, or disabled sources (patents with no key), skip.
        problem_profiles = []
        try:
            from app.config import settings as _s
            extraction_targets = [
                ("challenge_portal", challenge_items,               _s.PROBLEM_EXTRACTION_CAP),
                ("github_issues",    raw.get("github_issues", []), _s.PROBLEM_EXTRACTION_CAP_GITHUB),
                ("arxiv",            raw.get("arxiv", []),         _s.PROBLEM_EXTRACTION_CAP_ARXIV),
                ("news",             raw.get("news", []),          _s.PROBLEM_EXTRACTION_CAP_NEWS),
                ("patents",          raw.get("patents", []),       _s.PROBLEM_EXTRACTION_CAP_PATENTS),
            ]
            for src_name, items, cap in extraction_targets:
                if not items or cap <= 0:
                    continue
                try:
                    profiles = self.problem_extractor.extract_batch(
                        items, cap=cap, source_type=src_name
                    )
                    if profiles:
                        self._save_problem_profiles(profiles)
                        problem_profiles.extend(profiles)
                except Exception as e:
                    logger.warning(f"ProblemProfile extraction failed for {src_name}: {e}")
        except Exception as e:
            logger.error(f"ProblemProfile extraction setup failed: {e}")

        # ---- Phase 2.1: technology extraction for the profiles just saved ----
        try:
            from app.database import SessionLocal as _SL2
            db2 = _SL2()
            try:
                rows = (
                    db2.query(models.ProblemProfile)
                    .order_by(models.ProblemProfile.id.desc())
                    .limit(10)
                    .all()
                )
            finally:
                db2.close()
            if rows:
                tech_results = self.technology_agent.extract_batch(rows)
                if tech_results:
                    self._save_technologies(tech_results)
        except Exception as e:
            logger.error(f"Technology extraction failed: {e}")

        # ---- Phase 3.1: research discovery for the same recent profiles ----
        try:
            from app.database import SessionLocal as _SL3
            db3 = _SL3()
            try:
                rows = (
                    db3.query(models.ProblemProfile)
                    .order_by(models.ProblemProfile.id.desc())
                    .limit(10)
                    .all()
                )
            finally:
                db3.close()
            if rows:
                paper_results = self.research_discovery_agent.extract_batch(rows)
                if paper_results:
                    self._save_problem_papers(paper_results)
        except Exception as e:
            logger.error(f"Research discovery failed: {e}")

        # ---- Phase 4.1: evidence aggregation for recent opportunities ----
        # CPU-only (keyword match against raw_documents). No LLM calls.
        try:
            from app.database import SessionLocal as _SL4
            db4 = _SL4()
            try:
                opp_rows = (
                    db4.query(models.Opportunity)
                    .order_by(models.Opportunity.id.desc())
                    .limit(15)
                    .all()
                )
            finally:
                db4.close()
            if opp_rows:
                evidence_results = self.evidence_agent.aggregate_batch(opp_rows)
                if evidence_results:
                    self._save_evidence(evidence_results)
        except Exception as e:
            logger.error(f"Evidence aggregation failed: {e}")

        # ---- Phase 5.1/5.2: build canonical KG edges from Phase 2/3/4 tables ----
        try:
            kg_enriched = self.kg.build_enriched_graph()
            self.kg.persist()
            logger.info(f"KG enriched: {kg_enriched}")
        except Exception as e:
            logger.error(f"Enriched KG build failed: {e}")

        # ---- Phase 6.1/6.2: enrichment of recent opportunities ----
        try:
            enriched_stats = self._enrich_opportunities()
            logger.info(f"Opportunity enrichment: {enriched_stats}")
        except Exception as e:
            logger.error(f"Opportunity enrichment block failed: {e}")

        # ---- Phase 8.2/8.3: score snapshots + rank-change alerts ----
        try:
            snap_stats = self._snapshot_and_notify()
            logger.info(f"Score snapshot: {snap_stats}")
        except Exception as e:
            logger.error(f"Score snapshot block failed: {e}")

        # Strip private helper keys before returning to API
        for c in clusters:
            c.pop("_doc_indices", None)
            c.pop("_avg_sentiment", None)

        return {
            "query": query,
            "documents_count": len(documents),
            "clusters": clusters,
            "research_gaps": gaps,
            "trends": trends,
            "opportunities": opportunities,
            "knowledge_graph": kg_stats,
            "topics": global_topics,
            "problem_profiles": problem_profiles,
        }
