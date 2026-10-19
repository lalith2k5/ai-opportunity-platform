"""Stack Exchange API v2.3 -- free, 300 req/day without key, 10k with free key."""
import requests
import time
from datetime import datetime, timezone
from app.config import settings
from app.logger import logger

BASE = "https://api.stackexchange.com/2.3"
DEFAULT_TIMEOUT = 20

class StackExchangeService:
    def __init__(self, site="stackoverflow", timeout=DEFAULT_TIMEOUT):
        self.site = site
        self.timeout = timeout
        self.api_key = getattr(settings, "STACKEXCHANGE_API_KEY", "")
        self._backoff_until = 0.0

    def _get(self, path, params):
        wait = self._backoff_until - time.time()
        if wait > 0:
            time.sleep(wait)
        p = dict(params)
        p["site"] = self.site
        if self.api_key:
            p["key"] = self.api_key
        r = requests.get(f"{BASE}{path}", params=p, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        bo = data.get("backoff")
        if isinstance(bo, (int, float)) and bo > 0:
            self._backoff_until = time.time() + float(bo)
            logger.info(f"[StackExchange] backoff {bo}s")
        return data

    def search(self, query, limit=20, tagged=None):
        params = {
            "order": "desc",
            "sort": "relevance",
            "pagesize": min(max(limit, 1), 100),
            "q": query,
        }
        if tagged:
            params["tagged"] = tagged
        try:
            data = self._get("/search/advanced", params)
        except Exception as e:
            logger.warning(f"[StackExchange] search failed: {e}")
            return []
        return [self._to_doc(it) for it in (data.get("items") or []) if self._to_doc(it)]

    def fetch_questions(self, tag, limit=20):
        params = {"order": "desc", "sort": "votes", "pagesize": min(max(limit, 1), 100), "tagged": tag}
        try:
            data = self._get("/questions", params)
        except Exception as e:
            logger.warning(f"[StackExchange] fetch failed: {e}")
            return []
        return [self._to_doc(it) for it in (data.get("items") or []) if self._to_doc(it)]

    def _to_doc(self, item):
        qid = item.get("question_id")
        if not qid:
            return None
        title = item.get("title") or ""
        body = item.get("body_markdown") or item.get("body") or ""
        return {
            "source": "stackexchange",
            "external_id": str(qid),
            "title": title[:500],
            "url": (item.get("link") or f"https://{self.site}.com/q/{qid}")[:500],
            "content": f"{title}\n\n{body}"[:8000],
            "author": (str((item.get("owner") or {}).get("user_id", "")) or "")[:100],
            "metadata_json": {
                "score": item.get("score"),
                "answer_count": item.get("answer_count"),
                "is_answered": item.get("is_answered"),
                "tags": item.get("tags"),
                "creation_date": item.get("creation_date"),
            },
            "collected_at": datetime.now(timezone.utc),
            "processed": False,
        }
