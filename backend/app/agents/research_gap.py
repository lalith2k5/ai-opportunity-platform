import re
import numpy as np
from app.logger import logger
from app.agents import opportunity_intelligence as _oi
from app.agents.problem_discovery import _EXTRA_NOISE  # ensures mutation on import
from app.agents.opportunity_intelligence import _clean_keywords, _title_case

_oi.NOISE_WORDS.update(_EXTRA_NOISE)


class ResearchGapAgent:
    FUTURE_WORK_PATTERNS = [
        r"future work (?:will|should|may|could|might|must|is|includes?|involves?)",
        r"future research (?:will|should|may|could|might|is|includes?|directions?)",
        r"remains? (?:an? )?open (?:problem|question|challenge|issue)",
        r"not (?:yet )?(?:been )?(?:addressed|explored|studied|solved)",
        r"open (?:problem|question|challenge|issue)",
        r"worth (?:investigating|exploring|studying)",
        r"calls? for further",
        r"promising (?:direction|avenue|future)",
        r"unexplored",
        r"needs? (?:to be )?(?:further )?(?:studied|explored|investigated|addressed)",
    ]

    MIN_KEYWORDS_TO_KEEP = 2

    def extract_future_work(self, text: str, max_snippets: int = 3) -> list:
        if not text:
            return []
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        snippets = []
        for sent in sentences:
            lower = sent.lower()
            for pattern in self.FUTURE_WORK_PATTERNS:
                if re.search(pattern, lower):
                    clean = sent.strip()
                    if 20 < len(clean) < 400:
                        snippets.append(clean)
                    break
            if len(snippets) >= max_snippets:
                break
        return snippets

    def _semantic_coverage(self, paper_embeddings, embedder, cluster, keywords) -> float:
        if paper_embeddings is None or embedder is None or len(paper_embeddings) == 0:
            return None
        try:
            cluster_text = ((cluster.get("title") or "") + " " + " ".join(str(k) for k in keywords[:8]))[:1000]
            cluster_emb = embedder.model.encode([cluster_text], normalize_embeddings=True)[0]
            sims = paper_embeddings @ cluster_emb
            top_k = min(5, len(sims))
            if top_k == 0:
                return None
            mean_top = float(np.sort(sims)[::-1][:top_k].mean())
            return max(0.0, min(1.0, (mean_top - 0.25) / 0.5))
        except Exception as e:
            logger.warning(f"[ResearchGap] Semantic coverage failed: {e}")
            return None

    def _clean_flat(self, raw: list) -> list:
        cleaned = _clean_keywords(raw or [])
        return cleaned["phrases"] + cleaned["singles"]

    def detect_gaps(self, problem_clusters: list, arxiv_papers: list) -> list:
        gaps = []

        paper_texts = [
            ((p.get("title") or "") + " " + (p.get("summary") or ""))[:2000]
            for p in arxiv_papers
        ]
        paper_embeddings = None
        embedder = None
        if paper_texts:
            try:
                from app.services.embedding_service import EmbeddingService
                embedder = EmbeddingService()
                paper_embeddings = embedder.model.encode(paper_texts, normalize_embeddings=True, batch_size=32)
                logger.info(f"[ResearchGap] Embedded {len(paper_texts)} papers")
            except Exception as e:
                logger.error(f"[ResearchGap] Embedding failed, falling back to keyword-only: {e}")
                paper_embeddings = None

        paper_text = " ".join(paper_texts).lower()

        all_future_work = []
        for paper in arxiv_papers:
            fw = self.extract_future_work(paper.get("summary", ""), max_snippets=2)
            if fw:
                all_future_work.append({"paper_title": paper.get("title", ""), "snippets": fw})

        for cluster in problem_clusters:
            raw_keywords = cluster.get("keywords", [])
            if not raw_keywords:
                continue
            keywords = self._clean_flat(raw_keywords)
            if len(keywords) < self.MIN_KEYWORDS_TO_KEEP:
                continue  # skip noise clusters entirely

            kw_matches = sum(1 for kw in keywords if kw.lower() in paper_text)
            keyword_coverage = kw_matches / max(len(keywords), 1)

            semantic_coverage = self._semantic_coverage(paper_embeddings, embedder, cluster, keywords)
            if semantic_coverage is None:
                semantic_coverage = keyword_coverage

            coverage = max(0.0, min(1.0, 0.7 * semantic_coverage + 0.3 * keyword_coverage))
            gap_score = 1.0 - coverage

            relevant_future_work = []
            for fw in all_future_work:
                for snippet in fw["snippets"]:
                    if any(kw.lower() in snippet.lower() for kw in keywords[:5]):
                        relevant_future_work.append({"paper": fw["paper_title"], "snippet": snippet})
                        break

            label = ", ".join(_title_case(k) for k in keywords[:3])

            gaps.append({
                "title": f"Research Gap: {label}",
                "description": f"Limited research coverage ({coverage:.0%}) for problems related to: {', '.join(keywords[:5])}",
                "gap_score": round(gap_score, 2),
                "evidence": {
                    "coverage": round(coverage, 3),
                    "semantic_coverage": round(semantic_coverage, 3),
                    "keyword_coverage": round(keyword_coverage, 3),
                    "keywords": keywords,
                    "future_work_snippets": relevant_future_work[:3],
                },
            })

        return gaps
