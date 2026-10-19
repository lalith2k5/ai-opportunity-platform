"""Dev.to (Forem) API v1 -- free, public articles endpoint."""
import requests
from datetime import datetime, timezone
from app.config import settings
from app.services.api_keys import get_key
from app.logger import logger

BASE = "https://dev.to/api"
DEFAULT_TIMEOUT = 20

class DevToService:
    def __init__(self, timeout=DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.api_key = get_key("DEVTO_API_KEY")

    def _headers(self):
        h = {"User-Agent": "AI-Opportunity-Platform/1.0"}
        if self.api_key:
            h["api-key"] = self.api_key
        return h

    def fetch_articles(self, tag, limit=20, top_days=30):
        params = {"tag": tag, "per_page": min(max(limit, 1), 1000)}
        if top_days:
            params["top"] = top_days
        try:
            r = requests.get(f"{BASE}/articles", params=params, headers=self._headers(), timeout=self.timeout)
            r.raise_for_status()
            items = r.json()
        except Exception as e:
            logger.warning(f"[DevTo] fetch failed tag={tag}: {e}")
            return []
        return [self._to_doc(it) for it in items if self._to_doc(it)]

    def search(self, query, limit=20):
        return self.fetch_articles(tag=query.lower().replace(" ", ""), limit=limit, top_days=None)

    def _to_doc(self, item):
        aid = item.get("id")
        if not aid:
            return None
        title = item.get("title") or ""
        body = item.get("description") or ""
        url = item.get("url") or f"https://dev.to/x/{aid}"
        return {
            "source": "devto",
            "external_id": str(aid),
            "title": title[:500],
            "url": url[:500],
            "content": f"{title}\n\n{body}"[:8000],
            "author": (item.get("user", {}).get("username") or "")[:100],
            "metadata_json": {
                "tags": item.get("tag_list"),
                "published_at": item.get("published_at"),
                "reactions": item.get("public_reactions_count"),
                "comments": item.get("comments_count"),
            },
            "collected_at": datetime.now(timezone.utc),
            "processed": False,
        }
