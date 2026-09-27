"""LLM-powered extraction of structured Problem Profiles from challenge text.

Turns a raw challenge document (SBIR solicitation, federal challenge, etc)
into an 11-field structured profile with technology-stage differentiation
and student-suitability scoring.
"""
import json
import re

from app.logger import logger
from app.services.llm_service import LLMService


_PROMPT = """You are extracting a structured problem profile from a source document.

The source type is: {source_type}
The document may be a GitHub issue, a research paper abstract, a news article,
a patent abstract, or a public R&D/industry challenge. Extract the underlying
real-world problem the document is describing, discussing, or addressing.

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

    def _extract_one(self, item: dict, source_type: str = "unknown") -> dict | None:
        # Universal content field — sources name content differently:
        #   challenge_portal: raw_text / description
        #   github / news / arxiv / patents: summary
        #   reddit: selftext
        description = (
            item.get("raw_text")
            or item.get("description")
            or item.get("summary")
            or item.get("selftext")
            or ""
        )
        # Organization inference for sources that do not supply one
        org = item.get("organization") or ""
        if not org:
            repo_url = item.get("repository_url") or ""
            if "/repos/" in repo_url:
                # e.g. "https://api.github.com/repos/owner/name" -> "owner"
                parts = repo_url.rstrip("/").split("/")
                if len(parts) >= 2:
                    org = parts[-2]
            if not org:
                org = item.get("source") or item.get("lab") or "Unknown"

        # Use .replace() rather than .format() — the JSON schema example in
        # _PROMPT contains { } braces that .format() would misinterpret.
        prompt = (
            _PROMPT
            .replace("{source_type}", str(source_type))
            .replace("{title}", str(item.get("title", "")))
            .replace("{org}", str(org))
            .replace("{url}", str(item.get("url") or item.get("html_url") or ""))
            .replace("{description}", str(description)[:4000])
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
            "organization": (data.get("organization") or org or "").strip()[:200],
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
            "source": item.get("source") or source_type,
            "source_url": item.get("url") or item.get("html_url") or "",
            "extracted_by": self.llm.last_used or "unknown",
        }

    # If this many calls in a row fail, assume the LLM provider is down
    # (quota exhausted, 429, network) and stop burning the remaining cap.
    MAX_CONSECUTIVE_FAILURES = 2

    def extract_batch(self, items: list, cap: int = 8, source_type: str = "unknown") -> list:
        """Extract up to `cap` structured profiles. Skips failures silently.

        Circuit breaker: after MAX_CONSECUTIVE_FAILURES failures in a row
        for this source, stops trying — avoids hammering a rate-limited or
        down provider and wasting the remaining extraction budget.
        """
        if not items or cap <= 0:
            return []
        out = []
        attempted = 0
        consecutive_failures = 0
        for item in items[:cap]:
            attempted += 1
            profile = self._extract_one(item, source_type=source_type)
            if profile:
                out.append(profile)
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                if consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES:
                    remaining = cap - attempted
                    logger.warning(
                        f"[ProblemExtractor] Circuit breaker tripped: "
                        f"{consecutive_failures} consecutive failures for "
                        f"source={source_type}; abandoning {remaining} remaining candidate(s)"
                    )
                    break
        logger.info(
            f"[ProblemExtractor] Extracted {len(out)}/{attempted} "
            f"profiles (source={source_type})"
        )
        return out
