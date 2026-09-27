"""LLM-powered extraction of structured Problem Profiles from challenge text.

Turns a raw challenge document (SBIR solicitation, federal challenge, etc)
into an 11-field structured profile with technology-stage differentiation
and student-suitability scoring.
"""
import json
import re

from app.logger import logger
from app.services.llm_service import LLMService


_PROMPT = """You are extracting a structured problem profile from a public R&D/industry challenge.

Return ONLY valid JSON. No markdown fences, no explanations, no preamble. Use this exact schema:

{
  "organization": "string",
  "problem_title": "string — specific, non-generic, under 100 chars",
  "problem_description": "string — 2-4 sentences describing the actual technical challenge",
  "industry_domain": "Healthcare|Manufacturing|Education|Finance|Cybersecurity|Transportation|Energy|Agriculture|Software|Robotics|Aerospace|Environment|Defense|Other",
  "problem_type": "Performance|Accuracy|Security|Scalability|Cost|Automation|Reliability|Resource limitation|Data limitation|User experience|Other",
  "technology_stage": "used|exploring|potential",
  "required_technology": ["specific technology names mentioned"],
  "current_approach": "string — how it is currently being addressed, or '' if not stated",
  "known_limitations": "string — why current approaches fall short, or '' if not stated",
  "expected_outcome": "string — what a successful solution achieves",
  "problem_status": "active|solved|ongoing|unknown",
  "student_suitability": "high|medium|low",
  "keywords": ["normalized", "keywords"]
}

STRICT RULES:
- Do NOT invent facts. If a field is not in the source, use "" or [].
- problem_title must be specific (e.g. "Low-data industrial defect detection"), NOT generic (e.g. "AI improvement").
- required_technology: only technology actually mentioned in the source.
- technology_stage: "used" if deployed, "exploring" if under investigation, "potential" if only suggested.
- student_suitability: "high" if a solo student could plausibly deliver a prototype; "low" if it requires specialized hardware/clearance/enterprise data.

SOURCE:
Title: {title}
Organization: {org}
URL: {url}
Description:
{description}
"""


_VALID_DOMAINS = {
    "Healthcare","Manufacturing","Education","Finance","Cybersecurity",
    "Transportation","Energy","Agriculture","Software","Robotics",
    "Aerospace","Environment","Defense","Other",
}
_VALID_TYPES = {
    "Performance","Accuracy","Security","Scalability","Cost","Automation",
    "Reliability","Resource limitation","Data limitation","User experience","Other",
}
_VALID_STAGES = {"used", "exploring", "potential"}
_VALID_STATUSES = {"active", "solved", "ongoing", "unknown"}
_VALID_SUITABILITY = {"high", "medium", "low"}


def _extract_json(text: str) -> dict | None:
    if not text:
        return None
    # Strip markdown fences
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)
    # Find outer braces
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except Exception:
        return None


class ProblemExtractorAgent:
    def __init__(self):
        self.llm = LLMService()

    def _extract_one(self, item: dict) -> dict | None:
        # Use .replace() rather than .format() — the JSON schema example in
        # _PROMPT contains { } braces that .format() would misinterpret.
        prompt = (
            _PROMPT
            .replace("{title}", str(item.get("title", "")))
            .replace("{org}", str(item.get("organization", "")))
            .replace("{url}", str(item.get("url", "")))
            .replace("{description}",
                     str(item.get("raw_text") or item.get("description") or "")[:4000])
        )
        try:
            response = self.llm.generate(prompt)
        except Exception as e:
            logger.warning(f"[ProblemExtractor] LLM call failed: {e}")
            return None

        if not response or response.startswith("All LLM providers failed") or response.startswith("AI service not configured"):
            logger.warning(f"[ProblemExtractor] LLM unavailable: {response[:120]}")
            return None

        data = _extract_json(response)
        if not data:
            logger.warning(f"[ProblemExtractor] JSON parse failed for '{item.get('title','')[:60]}'")
            return None

        # Normalize + validate
        title = (data.get("problem_title") or "").strip()
        if not title or len(title) < 10:
            return None

        domain = data.get("industry_domain") or "Other"
        if domain not in _VALID_DOMAINS:
            domain = "Other"

        ptype = data.get("problem_type") or "Other"
        if ptype not in _VALID_TYPES:
            ptype = "Other"

        stage = (data.get("technology_stage") or "potential").lower()
        if stage not in _VALID_STAGES:
            stage = "potential"

        status = (data.get("problem_status") or "unknown").lower()
        if status not in _VALID_STATUSES:
            status = "unknown"

        suitability = (data.get("student_suitability") or "medium").lower()
        if suitability not in _VALID_SUITABILITY:
            suitability = "medium"

        techs = data.get("required_technology") or []
        if not isinstance(techs, list):
            techs = [str(techs)]
        techs = [str(t).strip() for t in techs if t and str(t).strip()][:10]

        kws = data.get("keywords") or []
        if not isinstance(kws, list):
            kws = [str(kws)]
        kws = [str(k).strip().lower() for k in kws if k and str(k).strip()][:15]

        return {
            "organization": (data.get("organization") or item.get("organization") or "").strip()[:200],
            "problem_title": title[:300],
            "problem_description": (data.get("problem_description") or item.get("description") or "").strip()[:5000],
            "industry_domain": domain,
            "problem_type": ptype,
            "technology_stage": stage,
            "required_technology": techs,
            "current_approach": (data.get("current_approach") or "").strip()[:3000],
            "known_limitations": (data.get("known_limitations") or "").strip()[:3000],
            "expected_outcome": (data.get("expected_outcome") or "").strip()[:3000],
            "problem_status": status,
            "student_suitability": suitability,
            "keywords": kws,
            "source": item.get("source", "unknown"),
            "source_url": item.get("url", ""),
            "extracted_by": self.llm.last_used or "unknown",
        }

    def extract_batch(self, items: list, cap: int = 8) -> list:
        """Extract up to `cap` structured profiles. Skips failures silently."""
        if not items or cap <= 0:
            return []
        out = []
        for item in items[:cap]:
            profile = self._extract_one(item)
            if profile:
                out.append(profile)
        logger.info(f"[ProblemExtractor] Extracted {len(out)}/{min(len(items), cap)} profiles")
        return out
