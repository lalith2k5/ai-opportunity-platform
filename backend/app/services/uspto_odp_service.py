"""USPTO Open Data Portal (ODP) -- free API key, 45 req/min. Replaces legacy PatentsView."""
import requests
from datetime import datetime, timezone
from app.config import settings
from app.services.api_keys import get_key
from app.logger import logger

BASE = "https://api.uspto.gov/api/v1"
DEFAULT_TIMEOUT = 25

class UsptoOdpService:
    def __init__(self, timeout=DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.api_key = get_key("USPTO_ODP_API_KEY")

    def is_configured(self):
        return bool(self.api_key)

    def search_patents(self, query, limit=20):
        if not self.is_configured():
            logger.warning("[USPTO] API key not configured -- set USPTO_ODP_API_KEY")
            return []
        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
        payload = {
            "q": query,
            "rangeFilters": [],
            "fields": ["patentApplicationNumber", "inventionTitle", "abstractText", "firstInventorName"],
            "pagination": {"offset": 0, "limit": min(max(limit, 1), 100)},
        }
        try:
            r = requests.post(f"{BASE}/patent/applications/search", json=payload, headers=headers, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            logger.warning(f"[USPTO] search failed: {e}")
            return []
        items = (data.get("data") or data.get("patentData") or [])
        return [self._to_doc(it) for it in items if self._to_doc(it)]

    def _to_doc(self, item):
        app_num = item.get("patentApplicationNumber") or item.get("applicationNumber")
        if not app_num:
            return None
        title = item.get("inventionTitle") or item.get("title") or ""
        abstract = item.get("abstractText") or item.get("abstract") or ""
        return {
            "source": "uspto",
            "external_id": str(app_num)[:200],
            "title": title[:500],
            "url": f"https://patents.google.com/patent/US{app_num}"[:500],
            "content": f"{title}\n\n{abstract}"[:8000],
            "author": str(item.get("firstInventorName") or "")[:200],
            "metadata_json": {
                "application_number": str(app_num),
                "filing_date": item.get("filingDate"),
                "status": item.get("applicationStatusDescriptionText"),
            },
            "collected_at": datetime.now(timezone.utc),
            "processed": False,
        }
