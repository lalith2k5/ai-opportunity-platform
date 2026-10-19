"""GDELT connector -- keyless real-time news API. Source class: NEWS."""
import requests
from datetime import datetime, timezone
from app.logger import logger

GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"
DEFAULT_TIMEOUT = 15


class GDELTService:
    def __init__(self, timeout=DEFAULT_TIMEOUT):
        self.timeout = timeout


    def search(self, query, limit=20, timespan="1week"):
        import time as _t
        params = {"query": query, "mode": "artlist", "format": "json",
                  "maxrecords": min(limit, 250), "timespan": timespan}
        headers = {"User-Agent": "AI-Opportunity-Platform/1.0 (research; contact: test@example.com)"}
        for attempt in range(3):
            try:
                r = requests.get(GDELT_DOC_API, params=params, headers=headers, timeout=self.timeout)
                if r.status_code == 429:
                    _t.sleep(3 + attempt * 2)
                    continue
                r.raise_for_status()
                text = r.text.strip()
                if not text or text.startswith("<"):
                    return []
                data = r.json()
                out = []
                for a in (data.get("articles") or []):
                    d = self._to_document(a)
                    if d: out.append(d)
                return out
            except Exception as e:
                logger.warning(f"[GDELT] attempt {attempt+1} failed: {e}")
                _t.sleep(2)
        return []

    def _to_document(self, item):
        url = item.get("url") or ""
        if not url:
            return None
        title = (item.get("title") or "").strip()
        ext_id = url
        domain = item.get("domain") or ""
        return {
            "source": "gdelt",
            "external_id": ext_id[:500],
            "title": title[:500] or f"News item from {domain}",
            "url": url[:500],
            "content": f"{title}\n\nSource: {domain}"[:8000],
            "author": "",
            "metadata_json": {
                "domain": domain,
                "language": item.get("language"),
                "seendate": item.get("seendate"),
                "sourcecountry": item.get("sourcecountry"),
                "socialimage": item.get("socialimage"),
            },
            "collected_at": datetime.now(timezone.utc),
            "processed": False,
        }
