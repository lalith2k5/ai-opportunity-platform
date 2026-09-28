"""TechnologyAgent — extract technologies associated with a problem profile.

For each ProblemProfile, asks the LLM to identify technologies used, proposed,
emerging, or potentially applicable to that problem. Categories follow SRS
Module 5 (§12) and roadmap Phase 2.1.

Stage vocabulary (matches SRS):
  - used                 : already deployed in this problem space
  - proposed             : under active investigation or planned
  - emerging             : recent/rising in this domain
  - potentially_applicable : plausible but not yet applied here
"""
import json
import re

from app.logger import logger
from app.services.llm_service import LLMService


_PROMPT = """You are identifying TECHNOLOGIES associated with a specific problem.

Return ONLY valid JSON. No markdown fences, no explanations, no preamble.
Use this exact schema:

{
  "technologies": [
    {
      "name": "short technology name (e.g. 'Computer Vision', 'Federated Learning')",
      "stage": "used|proposed|emerging|potentially_applicable",
      "confidence": 0.0,
      "evidence": "one short phrase explaining why, sourced from the text below"
    }
  ]
}

STRICT RULES:
- Return 2 to 6 technologies. Do NOT pad.
- Only return technologies that are plausibly connected to THIS problem.
- "stage" describes how the technology relates to solving this problem:
    used                     = the text says it is already in use here
    proposed                 = the text proposes or plans to use it
    emerging                 = it is gaining traction in this problem domain
                               (use this when the text describes recent
                               adoption, growing interest, or new research)
    potentially_applicable   = plausible but not yet mentioned as applied
- Do NOT default everything to "used". Aim for a realistic mix; use
  "emerging" whenever recent / rising adoption is implied.
- confidence is a float 0.0 to 1.0 reflecting how well the text supports it.
- If the text mentions no technologies, return {"technologies": []}.
- Do NOT invent specifics that are not in the text.

PROBLEM:
Title: {title}
Description: {description}
Industry domain: {domain}
Keywords: {keywords}
"""

_VALID_STAGES = {"used", "proposed", "emerging", "potentially_applicable"}


def _extract_json(text: str) -> dict | None:
    if not text:
        return None
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except Exception:
        return None


class TechnologyAgent:
    """LLM-based extraction of technologies per problem profile."""

    MAX_PER_PROBLEM = 6
    MAX_CONSECUTIVE_FAILURES = 2

    def __init__(self):
        self.llm = LLMService()

    def _extract_one(self, profile_row) -> list:
        """Return a list of normalized technology dicts for one ProblemProfile."""
        prompt = (
            _PROMPT
            .replace("{title}", (profile_row.problem_title or "")[:300])
            .replace("{description}", (profile_row.problem_description or "")[:2000])
            .replace("{domain}", (profile_row.industry_domain or "Other"))
            .replace("{keywords}", ", ".join((profile_row.keywords or [])[:10]))
        )
        try:
            response = self.llm.generate(prompt)
        except Exception as e:
            logger.warning(f"[TechnologyAgent] LLM call failed: {e}")
            return []

        if not response or response.startswith("All LLM providers failed") \
                or response.startswith("AI service not configured"):
            logger.warning(f"[TechnologyAgent] LLM unavailable: {response[:120]}")
            return []

        data = _extract_json(response)
        if not data or not isinstance(data.get("technologies"), list):
            logger.warning(
                f"[TechnologyAgent] JSON parse failed for "
                f"'{profile_row.problem_title[:60]}'"
            )
            return []

        out = []
        seen = set()
        for t in data["technologies"][: self.MAX_PER_PROBLEM]:
            if not isinstance(t, dict):
                continue
            name = (t.get("name") or "").strip()
            if not name or len(name) < 2 or len(name) > 120:
                continue
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            stage = (t.get("stage") or "").strip().lower()
            if stage not in _VALID_STAGES:
                stage = "potentially_applicable"
            try:
                conf = float(t.get("confidence", 0.5))
            except Exception:
                conf = 0.5
            conf = max(0.0, min(1.0, conf))
            evidence = (t.get("evidence") or "").strip()[:500]
            out.append({
                "name": name[:200],
                "stage": stage,
                "confidence": round(conf, 3),
                "evidence": evidence,
            })
        return out

    def extract_batch(self, profiles: list) -> list:
        """For each ProblemProfile row, extract techs. Returns
        [(profile_row, [tech_dict, ...]), ...] for rows where at least one
        tech was found. Circuit breaker stops after too many consecutive
        LLM failures."""
        if not profiles:
            return []
        results = []
        consecutive_failures = 0
        for row in profiles:
            techs = self._extract_one(row)
            if techs:
                results.append((row, techs))
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                if consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES:
                    logger.warning(
                        f"[TechnologyAgent] Circuit breaker tripped: "
                        f"{consecutive_failures} consecutive failures; "
                        f"abandoning remaining profiles"
                    )
                    break
        logger.info(
            f"[TechnologyAgent] Extracted techs for {len(results)}/{len(profiles)} profiles"
        )
        return results
