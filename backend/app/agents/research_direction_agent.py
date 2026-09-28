"""ResearchDirectionAgent — LLM-generated research + project directions.

Given an enriched view of an opportunity (problem, technologies, papers,
trends, evidence sources), generates:

  - suggested_research_direction: one research-oriented sentence
  - suggested_project_direction:  one concrete student/team project

Both fields are populated per SRS §34 (Opportunity Card).
Single LLM call per opportunity — low quota cost.
"""
import json
import re

from app.logger import logger
from app.services.llm_service import LLMService


_PROMPT = """You are advising on a problem-technology opportunity.

Given the details below, produce ONLY valid JSON (no markdown, no preamble):

{
  "suggested_research_direction": "1-2 sentences on the research angle worth pursuing",
  "suggested_project_direction":  "1-2 sentences on a concrete buildable project"
}

RULES:
- Be specific to the technologies and limitations provided.
- Do NOT invent facts not present in the input.
- If information is thin, keep both answers short and generic.
- Max 300 characters each.

OPPORTUNITY:
Title: {title}
Description: {description}
Domain: {domain}
Related technologies: {technologies}
Existing research (titles): {papers}
Known limitations: {limitations}
Emerging trend: {trend}
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


class ResearchDirectionAgent:
    MAX_CONSECUTIVE_FAILURES = 2

    def __init__(self):
        self.llm = LLMService()

    def _generate_one(self, snapshot: dict) -> dict:
        prompt = (
            _PROMPT
            .replace("{title}",        (snapshot.get("title") or "")[:200])
            .replace("{description}",  (snapshot.get("description") or "")[:800])
            .replace("{domain}",       (snapshot.get("domain") or "Other")[:60])
            .replace("{technologies}", ", ".join((snapshot.get("technologies") or [])[:8]))
            .replace("{papers}",       " | ".join((snapshot.get("papers") or [])[:5]))
            .replace("{limitations}",  " | ".join((snapshot.get("limitations") or [])[:5])[:500])
            .replace("{trend}",        (snapshot.get("trend") or "")[:120])
        )
        try:
            response = self.llm.generate(prompt)
        except Exception as e:
            logger.warning(f"[ResearchDirection] LLM call failed: {e}")
            return {}
        if not response or response.startswith("All LLM providers failed") \
                or response.startswith("AI service not configured"):
            logger.warning(f"[ResearchDirection] LLM unavailable: {response[:120]}")
            return {}
        data = _extract_json(response)
        if not data:
            return {}
        out = {}
        for key in ("suggested_research_direction", "suggested_project_direction"):
            v = data.get(key)
            if isinstance(v, str):
                s = v.strip()
                if s:
                    out[key] = s[:500]
        return out

    def generate_batch(self, snapshots: list) -> list:
        """snapshots: [{"opportunity_row": row, **enrichment_context}, ...]
        Returns [(row, {directions_dict}), ...] for rows that produced output."""
        if not snapshots:
            return []
        results = []
        consecutive_failures = 0
        for snap in snapshots:
            row = snap["opportunity_row"]
            out = self._generate_one(snap)
            if out:
                results.append((row, out))
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                if consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES:
                    logger.warning(
                        f"[ResearchDirection] Circuit breaker tripped: "
                        f"{consecutive_failures} consecutive failures; abandoning remaining"
                    )
                    break
        logger.info(
            f"[ResearchDirection] Generated directions for {len(results)}/{len(snapshots)} opportunities"
        )
        return results
