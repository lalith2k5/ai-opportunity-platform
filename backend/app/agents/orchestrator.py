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

    def _save_to_db(self, query, raw, processed, clusters, gaps, trends, opportunities, user_id=None):
        db = SessionLocal()
        try:
            # 1. Save raw documents with dedup
            inserted = 0
            for source_name, items in raw.items():
                for item in items:
                    ext_id = str(item.get("id", "") or "")
                    title = item.get("title") or item.get("name") or ""
                    content = item.get("summary") or item.get("selftext") or item.get("description") or ""

                    # Skip if already stored (dedup)
                    if ext_id:
                        exists = db.execute(
                            select(models.RawDocument.id).where(
                                models.RawDocument.source == source_name,
                                models.RawDocument.external_id == ext_id,
                            )
                        ).first()
                        if exists:
                            continue

                    raw_doc = models.RawDocument(
                        source=source_name,
                        external_id=ext_id,
                        title=title,
                        content=content[:5000],
                        url=item.get("url", item.get("html_url", "")),
                        metadata_json={"keys": list(item.keys())},
                    )
                    db.add(raw_doc)
                    inserted += 1
            logger.info(f"Inserted {inserted} new raw documents")

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

            # 4. Save trends
            for trend in trends:
                db.add(models.Trend(
                    name=trend.get("name", ""),
                    category=trend.get("category", "general"),
                    trend_score=trend.get("trend_score", 0.0),
                    source_data=trend.get("source_data", {}),
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

    def run_full_pipeline(self, query: str, user_id: int = None) -> dict:
        logger.info(f"Starting pipeline for: {query}")
        raw = self.data_collection.collect_all(query)

        documents = []
        for repo in raw.get("github", [])[:8]:
            documents.append({"source": "github", "title": repo.get("name", ""), "content": repo.get("description", "") or ""})
        for post in raw.get("reddit", [])[:8]:
            documents.append({"source": "reddit", "title": post.get("title", ""), "content": post.get("selftext", "")})
        for paper in raw.get("arxiv", [])[:8]:
            documents.append({"source": "arxiv", "title": paper.get("title", ""), "content": paper.get("summary", "")})
        for article in raw.get("news", [])[:8]:
            documents.append({"source": "news", "title": article.get("title", ""), "content": article.get("summary", "")})

        logger.info(f"Processing {len(documents)} documents")
        processed = []
        for doc in documents:
            nlp_result = self.nlp.process(doc.get("title", "") + " " + doc.get("content", ""))
            processed.append({**doc, **nlp_result})

        if processed:
            try:
                texts = [d.get("title", "") + " " + (d.get("content", "") or "")[:1000] for d in processed]
                metadatas = [{"source": d.get("source", "unknown")} for d in processed]
                self.embedding.add_documents(texts, metadatas=metadatas)
                logger.info(f"Stored {len(texts)} docs in vector DB")
            except Exception as e:
                logger.error(f"Embedding error: {e}")

        # Global topic modeling across all documents
        try:
            all_texts = [d.get("title", "") + " " + (d.get("content", "") or "")[:500] for d in processed]
            global_topics = self.nlp.extract_topics_nmf(all_texts, n_topics=5)
            logger.info(f"Topic modeling found {len(global_topics)} topics")
        except Exception as e:
            global_topics = []
            logger.error(f"Topic modeling error: {e}")

        kg_stats = self.kg.build_from_documents(processed)
        self.kg.persist()
        clusters = self.problem_discovery.discover(processed)
        gaps = self.research_gap.detect_gaps(clusters, raw.get("arxiv", []))
        trends = self.innovation_monitor.monitor(processed)

        opportunities = []
        for i, cluster in enumerate(clusters):
            gap = gaps[i] if i < len(gaps) else None
            trend = trends[i] if i < len(trends) else None
            opp = self.opportunity.score(
                cluster, gap, trend,
                github_items=raw.get("github", []),
                arxiv_items=raw.get("arxiv", []),
                news_items=raw.get("news", []),
            )
            opp["explanation"] = self.explainable.explain(opp)
            opportunities.append(opp)

        self._save_to_db(query, raw, processed, clusters, gaps, trends, opportunities, user_id=user_id)

        return {
            "query": query,
            "documents_count": len(documents),
            "clusters": clusters,
            "research_gaps": gaps,
            "trends": trends,
            "opportunities": opportunities,
            "knowledge_graph": kg_stats,
            "topics": global_topics,
        }
