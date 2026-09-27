"""Fetch patent data from PatentsView API.

PatentsView requires a free API key (as of 2024). Set PATENTSVIEW_API_KEY in
backend/.env. If unset, the service logs a warning once at construction and
returns [] on every search — the pipeline continues unaffected.

Request a key: https://patentsview.org/apis/keyrequest
API base:      https://search.patentsview.org/api/v1/patent/
"""
import requests

from app.config import settings
from app.logger import logger
from app.services.retry_helper import api_retry


class PatentsService:
    BASE_URL = "https://search.patentsview.org/api/v1/patent/"
    HARD_CAP = 100

    # Fields requested from PatentsView. Keep in sync with _normalize().
    FIELDS = [
        "patent_id",
        "patent_title",
        "patent_abstract",
        "patent_date",
        "assignees.assignee_organization",
        "inventors.inventor_name_first",
        "inventors.inventor_name_last",
        "cpc_current.cpc_group_id",
    ]

    def __init__(self):
        self.api_key = (settings.PATENTSVIEW_API_KEY or "").strip()
        if not self.api_key:
            logger.warning(
                "[Patents] PATENTSVIEW_API_KEY not configured — patents source disabled. "
                "Request a key at https://patentsview.org/apis/keyrequest"
            )
        else:
            logger.info("[Patents] PatentsView API configured")

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------
    @api_retry(max_attempts=3)
    def _post(self, payload: dict) -> requests.Response:
        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        return requests.post(self.BASE_URL, headers=headers, json=payload, timeout=30)

    # ------------------------------------------------------------------
    # Normalization
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_orgs(assignees: list) -> list:
        out = []
        for a in assignees or []:
            org = (a or {}).get("assignee_organization")
            if org and org not in out:
                out.append(org)
        return out

    @staticmethod
    def _extract_inventors(inventors: list) -> list:
        out = []
        for i in inventors or []:
            first = (i or {}).get("inventor_name_first") or ""
            last = (i or {}).get("inventor_name_last") or ""
            name = (first + " " + last).strip()
            if name and name not in out:
                out.append(name)
        return out

    @staticmethod
    def _extract_cpc(cpc_list: list) -> list:
        out = []
        for c in cpc_list or []:
            code = (c or {}).get("cpc_group_id")
            if code and code not in out:
                out.append(code)
        return out

    def _normalize(self, raw: dict) -> dict:
        pid = str(raw.get("patent_id") or "").strip()
        title = (raw.get("patent_title") or "").strip()
        abstract = (raw.get("patent_abstract") or "").strip()
        date = (raw.get("patent_date") or "").strip()

        return {
            "id": f"patentsview:{pid}" if pid else "",
            "title": title,
            "summary": abstract,
            "url": f"https://patents.google.com/patent/US{pid}" if pid else "",
            "published": date,
            "source": "patents",
            "assignees": self._extract_orgs(raw.get("assignees") or []),
            "inventors": self._extract_inventors(raw.get("inventors") or []),
            "cpc_codes": self._extract_cpc(raw.get("cpc_current") or []),
        }

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------
    def search_patents(self, query: str, limit: int = 10) -> list:
        """Return patents matching the query. [] if no API key is configured."""
        if not self.api_key:
            return []
        if not query or not query.strip():
            return []

        limit = max(1, min(limit, self.HARD_CAP))
        payload = {
            "q": {
                "_text_any": {
                    "patent_title": query,
                    "patent_abstract": query,
                }
            },
            "f": self.FIELDS,
            "s": [{"patent_date": "desc"}],
            "o": {"per_page": limit},
        }

        try:
            response = self._post(payload)
            if response.status_code != 200:
                logger.warning(
                    f"[Patents] PatentsView status {response.status_code}: "
                    f"{response.text[:200]}"
                )
                return []
            data = response.json()
        except Exception as e:
            logger.error(f"[Patents] request failed: {e}")
            return []

        rows = data.get("patents") or []
        results = []
        for raw in rows:
            if not isinstance(raw, dict):
                continue
            norm = self._normalize(raw)
            if not norm["title"]:
                continue
            results.append(norm)
            if len(results) >= limit:
                break

        logger.info(f"[Patents] Fetched {len(results)} patents for '{query}'")
        return results


# TODO: EPO OPS fallback (phase-N) — OAuth2 client-credentials flow.
# Requires EPO_OPS_KEY + EPO_OPS_SECRET in settings; out of scope for Phase 0.1.
