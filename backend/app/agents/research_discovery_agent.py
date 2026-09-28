"""ResearchDiscoveryAgent — find arXiv papers per problem + extract limitations.

For each ProblemProfile:
  1. Build a focused arXiv query from the problem title + top keywords.
  2. Fetch top-N papers via the existing ArxivService.
  3. ONE LLM call for all N papers: score relevance to the problem and
     extract limitations each paper's approach has for this problem.

Design notes:
  - Single LLM call per problem (not per paper) — N abstracts go in, N
    assessments come out. Cuts token usage and quota burn dramatically.
  - Circuit breaker stops after 2 consecutive LLM failures, same pattern
    as ProblemExtractorAgent / TechnologyAgent.
  - KG wiring (STUDIED_BY / HAS_LIMITATION / HAS_POTENTIAL_GAP) is
    deferred to Phase 5 (KG schema alignment).
"""
import json
import re

from app.logger import logger
from app.services.arxiv_service import ArxivService
from app.services.llm_service import LLMService


_PROMPT = """You are analyzing research papers relative to a specific problem.

PROBLEM:
Title: {title}
Description: {description}
Industry: {domain}
Keywords: {keywords}

For each paper below, return:
  - relevance_score: 0.0 to 1.0 — how relevant is this paper to the problem?
  - limitations: array of 1 to 3 short strings describing limitations, gaps,
    or unaddressed aspects of the paper's approach relative to THIS problem.
    Only list limitations the paper itself mentions OR that are evident from
    the abstract. Do NOT invent.

Return ONLY valid JSON, no markdown, no preamble:
{{
  "assessments": [
    {{"paper_index": 0, "relevance_score": 0.0, "limitations": ["..."]}},
    {{"paper_index": 1, "relevance_score": 0.0, "limitations": ["..."]}}
  ]
}}

PAPERS:
{papers_block}
"""

_PAPER_BLOCK = """[{idx}] {title}
     Abstract: {abstract}
"""


def _extract_json(text: str) -> dict | None:
    if not text:
        return None
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)
    start = text.find("{"); end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except Exception:
        return None


class ResearchDiscoveryAgent:
    MAX_PAPERS_PER_PROBLEM = 5
    MAX_CONSECUTIVE_FAILURES = 2

    def __init__(self):
        self.arxiv = ArxivService()
        self.llm = LLMService()

    def _build_query(self, problem_row) -> str:
        title = (problem_row.problem_title or "").strip()
        kws = (problem_row.keywords or [])[:3]
        parts = [title] + [str(k) for k in kws if k]
        return " ".join(parts)[:300] or "artificial intelligence"

    def _assess_papers(self, problem_row, papers: list) -> dict:
        """Return {paper_idx: {relevance_score, limitations}} — {} on failure."""
        papers_block = "".join(
            _PAPER_BLOCK.format(
                idx=i,
                title=(p.get("title") or "")[:200],
                abstract=(p.get("summary") or "")[:600],
            )
            for i, p in enumerate(papers)
        )
        prompt = (
            _PROMPT
            .replace("{title}", (problem_row.problem_title or "")[:300])
            .replace("{description}", (problem_row.problem_description or "")[:1500])
            .replace("{domain}", problem_row.industry_domain or "Other")
            .replace("{keywords}", ", ".join((problem_row.keywords or [])[:10]))
            .replace("{papers_block}", papers_block)
        )
        try:
            response = self.llm.generate(prompt)
        except Exception as e:
            logger.warning(f"[ResearchDiscovery] LLM call failed: {e}")
            return {}
        if not response or response.startswith("All LLM providers failed") \
                or response.startswith("AI service not configured"):
            logger.warning(f"[ResearchDiscovery] LLM unavailable: {response[:120]}")
            return {}
        data = _extract_json(response)
        if not data or not isinstance(data.get("assessments"), list):
            logger.warning(
                f"[ResearchDiscovery] JSON parse failed for "
                f"'{problem_row.problem_title[:60]}'"
            )
            return {}
        out = {}
        for a in data["assessments"]:
            if not isinstance(a, dict):
                continue
            try:
                idx = int(a.get("paper_index", -1))
            except Exception:
                continue
            if idx < 0 or idx >= len(papers):
                continue
            try:
                score = float(a.get("relevance_score", 0.5))
            except Exception:
                score = 0.5
            score = max(0.0, min(1.0, score))
            lims_raw = a.get("limitations") or []
            if not isinstance(lims_raw, list):
                lims_raw = [str(lims_raw)]
            lims = []
            for L in lims_raw[:3]:
                s = str(L).strip()
                if s and len(s) <= 400:
                    lims.append(s)
            out[idx] = {"relevance_score": round(score, 3), "limitations": lims}
        return out

    def _process_one(self, problem_row) -> list:
        """Return list of paper dicts with limitations for one problem. [] on failure."""
        query = self._build_query(problem_row)
        papers = self.arxiv.search_papers(query, max_results=self.MAX_PAPERS_PER_PROBLEM)
        if not papers:
            logger.info(f"[ResearchDiscovery] No arXiv papers for '{query[:60]}'")
            return []
        assessments = self._assess_papers(problem_row, papers)
        if not assessments:
            return []
        out = []
        for i, p in enumerate(papers):
            a = assessments.get(i)
            if not a:
                continue
            # Skip clearly irrelevant hits
            if a["relevance_score"] < 0.3:
                continue
            out.append({
                "arxiv_id": str(p.get("id") or "").strip()[:200],
                "title": (p.get("title") or "").strip()[:500],
                "authors": (p.get("authors") or [])[:10],
                "abstract": (p.get("summary") or "").strip()[:5000],
                "url": (p.get("url") or "").strip()[:500],
                "published": "",
                "relevance_score": a["relevance_score"],
                "limitations": a["limitations"],
            })
        return out

    def extract_batch(self, profiles: list) -> list:
        """Return [(profile_row, [paper_dict, ...]), ...] for profiles with hits."""
        if not profiles:
            return []
        results = []
        consecutive_failures = 0
        for row in profiles:
            try:
                papers = self._process_one(row)
            except Exception as e:
                logger.warning(f"[ResearchDiscovery] process error for '{row.problem_title[:50]}': {e}")
                papers = []
            if papers:
                results.append((row, papers))
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                if consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES:
                    logger.warning(
                        f"[ResearchDiscovery] Circuit breaker tripped: "
                        f"{consecutive_failures} consecutive failures; "
                        f"abandoning remaining profiles"
                    )
                    break
        logger.info(
            f"[ResearchDiscovery] Found papers for {len(results)}/{len(profiles)} profiles"
        )
        return results
