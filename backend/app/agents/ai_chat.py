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

    def _build_entity_summary(self, kind: str, entity_id: str) -> str:
        """Build a DB summary focused ONLY on one entity. Returns "" on failure.

        Never enumerates unrelated platform items -- the whole point of the
        contextual chat is that the answer is scoped.
        """
        from sqlalchemy import or_ as _or
        db = SessionLocal()
        try:
            lines = []
            lines.append(f"=== FOCUSED DATA: {kind} #{entity_id} ===")
            lines.append("This is the ONLY entity to discuss. Do NOT enumerate other top opportunities, "
                         "gaps, or trends from the platform.")

            if kind == "opportunity":
                try:
                    oid = int(entity_id)
                except Exception:
                    return ""
                o = db.query(models.Opportunity).filter(models.Opportunity.id == oid).first()
                if not o:
                    return ""
                lines.append("")
                lines.append(f"Title: {o.title}")
                lines.append(f"Description: {(o.description or '')[:1500]}")
                lines.append(f"Scores: overall={o.opportunity_score:.2f} demand={o.demand_score:.2f} "
                             f"research_gap={o.research_gap_score:.2f} trend={o.trend_score:.2f} "
                             f"feasibility={o.feasibility_score:.2f} market_readiness={o.market_readiness_score:.2f} "
                             f"confidence={o.confidence_score:.2f}")
                if o.domain: lines.append(f"Domain: {o.domain}")
                if o.industry: lines.append(f"Industry: {o.industry}")
                if o.related_technologies:
                    lines.append("Related technologies: " + ", ".join(str(t) for t in o.related_technologies[:12]))
                if o.existing_research:
                    lines.append("Existing research:")
                    for t in o.existing_research[:8]:
                        lines.append(f"  - {t}")
                if o.existing_approaches:
                    lines.append(f"Existing approaches: {o.existing_approaches[:1500]}")
                if o.known_limitations:
                    lines.append(f"Known limitations: {o.known_limitations[:1500]}")
                if o.suggested_research_direction:
                    lines.append(f"Suggested research direction: {o.suggested_research_direction}")
                if o.suggested_project_direction:
                    lines.append(f"Suggested project direction: {o.suggested_project_direction}")
                if o.explanation:
                    lines.append(f"Score explanation: {o.explanation}")
                if o.evidence_sources:
                    lines.append("Evidence sources:")
                    for e in list(o.evidence_sources)[:10]:
                        lines.append(f"  - [{e.get('source','?')}] {e.get('title','')[:120]} -- {e.get('url','')}")

            elif kind == "idea":
                try:
                    cid = int(entity_id)
                except Exception:
                    return ""
                c = db.query(models.ProblemCluster).filter(models.ProblemCluster.id == cid).first()
                if not c:
                    return ""
                lines.append("")
                lines.append(f"Title: {c.title}")
                lines.append(f"Description: {(c.description or '')[:1500]}")
                lines.append(f"Demand score: {c.demand_score:.2f} | Source count: {c.source_count}")
                kws = [str(k).lower() for k in (c.keywords or [])[:10] if k]
                if kws:
                    lines.append("Keywords: " + ", ".join(kws))

                # Best-matching problem profile
                best_p = None
                best_n = 0
                for p in db.query(models.ProblemProfile).all():
                    pk = set(str(k).lower() for k in (p.keywords or [])[:10] if k)
                    n = len(set(kws) & pk)
                    if n > best_n:
                        best_p, best_n = p, n
                if best_p:
                    lines.append("")
                    lines.append("Matched problem profile:")
                    lines.append(f"  Title: {best_p.problem_title}")
                    lines.append(f"  Description: {(best_p.problem_description or '')[:1200]}")
                    lines.append(f"  Industry: {best_p.industry_domain or 'Other'}")
                    if best_p.known_limitations:
                        lines.append(f"  Known limitations: {best_p.known_limitations[:1000]}")
                    if best_p.current_approach:
                        lines.append(f"  Current approach: {best_p.current_approach[:1000]}")

                    techs = db.query(models.ProblemTechnology).filter(
                        models.ProblemTechnology.problem_profile_id == best_p.id
                    ).all()
                    if techs:
                        lines.append("  Technologies:")
                        for t in techs[:10]:
                            lines.append(f"    - {t.technology_name} (stage={t.stage})")

                    papers = db.query(models.ProblemPaper).filter(
                        models.ProblemPaper.problem_profile_id == best_p.id
                    ).order_by(models.ProblemPaper.relevance_score.desc()).limit(6).all()
                    if papers:
                        lines.append("  Research papers:")
                        for p in papers:
                            lines.append(f"    - {p.title} (rel={p.relevance_score:.2f})")

                # Opportunities for this cluster
                opps = db.query(models.Opportunity).filter(
                    models.Opportunity.problem_cluster_id == cid
                ).order_by(models.Opportunity.opportunity_score.desc()).limit(5).all()
                if opps:
                    lines.append("")
                    lines.append("Opportunities linked to THIS cluster:")
                    for o in opps:
                        lines.append(f"  - id={o.id} | {o.title} | score={o.opportunity_score:.2f}")

                # Gaps matching keywords
                if kws:
                    kset = set(kws)
                    gap_lines = []
                    for g in db.query(models.ResearchGap).all():
                        gk = set(str(k).lower() for k in ((g.evidence or {}).get("keywords") or []) if k)
                        if len(gk & kset) >= 1:
                            gap_lines.append(f"  - {g.title} (gap={g.gap_score:.2f})")
                    if gap_lines:
                        lines.append("")
                        lines.append("Research gaps related to THIS cluster:")
                        lines.extend(gap_lines[:6])

            elif kind == "technology":
                tech_name = entity_id
                tech_rows = db.query(models.ProblemTechnology).filter(
                    models.ProblemTechnology.technology_name.ilike(tech_name)
                ).all()
                if not tech_rows:
                    return ""
                lines.append("")
                lines.append(f"Technology: {tech_name}")
                stages = {}
                for t in tech_rows:
                    stages.setdefault(t.stage or "potential", 0)
                    stages[t.stage or "potential"] += 1
                lines.append(f"Stage distribution: {stages}")
                lines.append(f"Linked problem profiles: {len({t.problem_profile_id for t in tech_rows})}")

                pids = list({t.problem_profile_id for t in tech_rows})
                profiles = db.query(models.ProblemProfile).filter(
                    models.ProblemProfile.id.in_(pids)
                ).limit(10).all()
                if profiles:
                    lines.append("Related problems:")
                    for p in profiles:
                        lines.append(f"  - {p.problem_title} ({p.industry_domain or 'Other'})")

                papers = db.query(models.ProblemPaper).filter(
                    models.ProblemPaper.problem_profile_id.in_(pids)
                ).order_by(models.ProblemPaper.relevance_score.desc()).limit(8).all()
                if papers:
                    lines.append("Related papers:")
                    for p in papers:
                        lines.append(f"  - {p.title} (rel={p.relevance_score:.2f})")

            elif kind == "research":
                aid = entity_id
                variants = {aid, "http://arxiv.org/abs/" + aid, "https://arxiv.org/abs/" + aid}
                rows = []
                for v in variants:
                    rows = db.query(models.ProblemPaper).filter(models.ProblemPaper.arxiv_id == v).all()
                    if rows:
                        break
                if not rows:
                    return ""
                p = rows[0]
                lines.append("")
                lines.append(f"Title: {p.title}")
                lines.append(f"Authors: {', '.join((p.authors or [])[:10])}")
                lines.append(f"Abstract: {(p.abstract or '')[:2000]}")
                if p.research_methods:
                    lines.append(f"Methods: {', '.join(p.research_methods)}")
                if p.results_summary:
                    lines.append(f"Key findings: {p.results_summary}")
                if p.limitations:
                    lines.append("Limitations:")
                    for L in p.limitations[:6]:
                        lines.append(f"  - {L}")
                if p.research_areas:
                    lines.append(f"Research areas: {', '.join(p.research_areas)}")

            elif kind == "rd":
                try:
                    pid = int(entity_id)
                except Exception:
                    return ""
                p = db.query(models.ProblemProfile).filter(models.ProblemProfile.id == pid).first()
                if not p:
                    return ""
                lines.append("")
                lines.append(f"Problem: {p.problem_title}")
                lines.append(f"Description: {(p.problem_description or '')[:1500]}")
                lines.append(f"Industry: {p.industry_domain or 'Other'}")
                lines.append(f"Organization: {p.organization or 'Unknown'}")
                if p.current_approach:
                    lines.append(f"Current approach: {p.current_approach[:1000]}")
                if p.known_limitations:
                    lines.append(f"Known limitations: {p.known_limitations[:1000]}")
                if p.expected_outcome:
                    lines.append(f"Expected outcome: {p.expected_outcome[:1000]}")
                if p.required_technology:
                    lines.append(f"Required technologies: {', '.join(p.required_technology[:10])}")
                techs = db.query(models.ProblemTechnology).filter(
                    models.ProblemTechnology.problem_profile_id == pid
                ).all()
                if techs:
                    lines.append("Technology landscape:")
                    for t in techs[:10]:
                        lines.append(f"  - {t.technology_name} (stage={t.stage}, conf={t.confidence})")
                papers = db.query(models.ProblemPaper).filter(
                    models.ProblemPaper.problem_profile_id == pid
                ).order_by(models.ProblemPaper.relevance_score.desc()).limit(8).all()
                if papers:
                    lines.append("Research landscape:")
                    for pp in papers:
                        lines.append(f"  - {pp.title} (rel={pp.relevance_score:.2f})")

            return "\n".join(lines)
        except Exception as e:
            logger.error(f"[AIChat] entity summary failed: {e}")
            return ""
        finally:
            db.close()

    def answer(self, question: str, entity_context: str = "",
               entity_kind: str = "", entity_id: str = "") -> dict:
        # Tier 1: structured DB summary -- FOCUSED on the entity if provided,
        # otherwise the generic platform-wide roll-up.
        if entity_kind and entity_id:
            data_summary = self._build_entity_summary(entity_kind, entity_id)
            if not data_summary:
                data_summary = self._build_data_summary(question)
        else:
            data_summary = self._build_data_summary(question)

        # Tier 2: semantic document snippets
        context_docs = []
        try:
            if self.embedding.count() > 0:
                results = self.embedding.search(question, n_results=8)
                context_docs = results.get("documents", [[]])[0]
        except Exception as e:
            logger.warning(f"[AIChat] Vector search error: {e}")

        # Combine
        parts = []
        if entity_context:
            parts.append(
                "=== ENTITY CONTEXT (what the user is currently looking at) ===\n"
                + entity_context
            )
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

        focus_note = ""
        if entity_context:
            focus_note = (
                "=== CRITICAL SCOPE RULE ===\n"
                "The user is asking about ONE specific entity. Every part of your answer "
                "must be about THAT entity. Do NOT enumerate other top opportunities, "
                "trends, or platform totals unless the user explicitly asks for comparison. "
                "If the focused data does not contain enough information, say so in a "
                "'Data limitations' section -- never fall back to platform-wide statistics.\n\n"
            )

        full_prompt = (
            "You are a senior innovation intelligence analyst. "
            "You have access to the platform's live data below -- use it.\n\n"
            + focus_note
            + "=== FORMAT RULES (follow exactly) ===\n"
            "- Start with a 1-2 sentence TL;DR (no header).\n"
            "- Then sections with '## ' headers. Typical section names: "
            "## Overview, ## Key Evidence, ## Recommendations, ## Risks and Limitations, ## Next Steps. "
            "Pick only the sections that fit the question.\n"
            "- Use '-' bullet lists and '1.' numbered lists for enumerable content.\n"
            "- Use **bold** for key terms and scores.\n"
            "- Target 300-700 words. Go longer only if the user asks for depth.\n\n"
            "=== CONTENT RULES ===\n"
            "- Cite concrete numbers, titles, and IDs from the STRUCTURED DATA section.\n"
            "- Distinguish data-backed claims from inferences.\n"
            "- If the data does not answer the question, say so in its own section.\n"
            "- Do not pad with disclaimers.\n"
            "- Do not say 'As an AI language model'.\n"
            "- Do not use emojis.\n\n"
            + context
            + "\n\n=== USER QUESTION ===\n"
            + question
            + "\n\nNow write a thorough, well-formatted answer following the format rules above."
        )

        response = self.llm.generate(full_prompt, "")
        return {"response": response, "sources": context_docs}
