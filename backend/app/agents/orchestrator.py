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

    def _save_problem_profiles(self, profiles: list):
        """Persist extracted ProblemProfile rows. Dedup by source_url or title."""
        if not profiles:
            return 0
        from app.database import SessionLocal as _SL
        db = _SL()
        inserted = 0
        try:
            for pr in profiles:
                key_url = (pr.get("source_url") or "").strip()
                key_title = (pr.get("problem_title") or "").strip()[:200]
                exists = False
                if key_url:
                    exists = db.query(models.ProblemProfile.id).filter(
                        models.ProblemProfile.source_url == key_url
                    ).first() is not None
                if not exists and key_title:
                    exists = db.query(models.ProblemProfile.id).filter(
                        models.ProblemProfile.problem_title == key_title
                    ).first() is not None
                if exists:
                    continue
                db.add(models.ProblemProfile(
                    organization=pr.get("organization", "")[:500],
                    problem_title=pr.get("problem_title", "")[:500],
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
                    extracted_by=pr.get("extracted_by", "unknown"),
                ))
                inserted += 1
            db.commit()
            logger.info(f"Saved {inserted} new ProblemProfile rows")
            return inserted
        except Exception as e:
            db.rollback()
            logger.error(f"ProblemProfile save error: {e}")
            return 0
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
            if _s.ENABLE_CHALLENGE_PORTALS:
                challenge_items = self.challenge_portal.fetch_all(query, limit=_s.CHALLENGE_PORTAL_CAP)
                raw["challenge_portal"] = challenge_items
        except Exception as e:
            logger.warning(f"Challenge portal fetch failed: {e}")

        documents = []
        for repo in raw.get("github", [])[:200]:
            documents.append({"source": "github", "title": repo.get("name", ""), "content": repo.get("description", "") or ""})
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
        trends = self.innovation_monitor.monitor(processed)

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

        # ---- Extract structured Problem Profiles from challenge portals ----
        problem_profiles = []
        if challenge_items:
            try:
                from app.config import settings as _s
                problem_profiles = self.problem_extractor.extract_batch(
                    challenge_items, cap=_s.PROBLEM_EXTRACTION_CAP
                )
                if problem_profiles:
                    self._save_problem_profiles(problem_profiles)
            except Exception as e:
                logger.error(f"ProblemProfile extraction failed: {e}")

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
