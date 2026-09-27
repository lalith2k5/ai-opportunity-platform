from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.database import SessionLocal
from app import models
from app.logger import logger


class AIChatAgent:
    def __init__(self):
        self.embedding = EmbeddingService()
        self.llm = LLMService()

    def _build_data_summary(self, question: str) -> str:
        """Query top opportunities / gaps / trends / totals from the DB."""
        db = SessionLocal()
        try:
            lines = []

            opps = (
                db.query(models.Opportunity)
                .order_by(models.Opportunity.opportunity_score.desc())
                .limit(8)
                .all()
            )
            if opps:
                lines.append("TOP OPPORTUNITIES (highest opportunity_score):")
                for o in opps:
                    lines.append(
                        f"  - id={o.id} | {o.title} | "
                        f"score={o.opportunity_score:.2f} | "
                        f"demand={o.demand_score:.2f} | "
                        f"gap={o.research_gap_score:.2f} | "
                        f"feasibility={o.feasibility_score:.2f}"
                    )

            gaps = (
                db.query(models.ResearchGap)
                .order_by(models.ResearchGap.gap_score.desc())
                .limit(5)
                .all()
            )
            if gaps:
                lines.append("")
                lines.append("TOP RESEARCH GAPS (highest gap_score):")
                for g in gaps:
                    lines.append(f"  - {g.title} (gap {g.gap_score:.2f})")

            trends = (
                db.query(models.Trend)
                .order_by(models.Trend.trend_score.desc())
                .limit(10)
                .all()
            )
            if trends:
                seen = set()
                lines.append("")
                lines.append("TOP TRENDS:")
                for t in trends:
                    if t.name in seen:
                        continue
                    seen.add(t.name)
                    lines.append(f"  - {t.name} (score {t.trend_score:.2f}, category {t.category})")
                    if len(seen) >= 5:
                        break

            lines.append("")
            lines.append("PLATFORM TOTALS:")
            lines.append(f"  - Opportunities: {db.query(models.Opportunity).count()}")
            lines.append(f"  - Problem clusters: {db.query(models.ProblemCluster).count()}")
            lines.append(f"  - Research gaps: {db.query(models.ResearchGap).count()}")
            lines.append(f"  - Trends: {db.query(models.Trend).count()}")
            lines.append(f"  - Raw documents: {db.query(models.RawDocument).count()}")
            lines.append(f"  - KG nodes: {db.query(models.KnowledgeGraphNode).count()}")
            lines.append(f"  - KG edges: {db.query(models.KnowledgeGraphEdge).count()}")

            return "\n".join(lines)
        except Exception as e:
            logger.error(f"[AIChat] Data summary failed: {e}")
            return ""
        finally:
            db.close()

    def answer(self, question: str) -> dict:
        # Tier 1: structured DB summary
        data_summary = self._build_data_summary(question)

        # Tier 2: semantic document snippets
        context_docs = []
        try:
            if self.embedding.count() > 0:
                results = self.embedding.search(question, n_results=5)
                context_docs = results.get("documents", [[]])[0]
        except Exception as e:
            logger.warning(f"[AIChat] Vector search error: {e}")

        # Combine
        parts = []
        if data_summary:
            parts.append(
                "=== STRUCTURED DATA (from the platform database) ===\n"
                + data_summary
            )
        if context_docs:
            parts.append(
                "=== RELEVANT DOCUMENT EXCERPTS (semantic search) ===\n"
                + "\n\n---\n\n".join(context_docs)
            )
        context = "\n\n".join(parts)

        response = self.llm.generate(question, context)
        return {"response": response, "sources": context_docs}
