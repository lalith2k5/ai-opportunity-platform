"""Hacker News connector -- keyless Firebase API. Source class: COMMUNITY."""
import requests
from urllib.parse import quote
from datetime import datetime, timezone
from app.logger import logger

HN_BASE = "https://hacker-news.firebaseio.com/v0"
HN_SEARCH = "https://hn.algolia.com/api/v1/search"
DEFAULT_TIMEOUT = 12


class HackerNewsService:
    def __init__(self, timeout=DEFAULT_TIMEOUT):
        self.timeout = timeout

    def _get(self, url):
        r = requests.get(url, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def fetch_item(self, item_id):
        try:
            data = self._get(f"{HN_BASE}/item/{item_id}.json")
        except Exception as e:
            logger.warning(f"[HN] fetch {item_id} failed: {e}")
            return None
        if not data or data.get("deleted") or data.get("dead"):
            return None
        return self._to_document(data)

    def _to_document(self, item):
        item_id = item.get("id")
        title = (item.get("title") or "").strip()
        text = (item.get("text") or "").strip()
        url = item.get("url") or f"https://news.ycombinator.com/item?id={item_id}"
        content = f"{title}\n\n{text}".strip() or title
        return {
            "source": "hackernews",
            "external_id": str(item_id),
            "title": title[:500] or f"HN item {item_id}",
            "url": url[:500],
            "content": content[:8000],
            "author": (item.get("by") or "")[:100],
            "metadata_json": {
                "score": item.get("score"),
                "descendants": item.get("descendants"),
                "type": item.get("type"),
                "time": item.get("time"),
            },
            "collected_at": datetime.now(timezone.utc),
            "processed": False,
        }

    def fetch_top(self, limit=20):
        try:
            ids = self._get(f"{HN_BASE}/topstories.json") or []
        except Exception as e:
            logger.warning(f"[HN] topstories failed: {e}")
            return []
        out = []
        for item_id in ids[:limit]:
            doc = self.fetch_item(item_id)
            if doc:
                out.append(doc)
        return out

    def fetch_new(self, limit=20):
        try:
            ids = self._get(f"{HN_BASE}/newstories.json") or []
        except Exception as e:
            return []
        return [d for d in (self.fetch_item(i) for i in ids[:limit]) if d]

    def search(self, query, limit=20):
        try:
            data = self._get(f"{HN_SEARCH}?query={quote(query)}&hitsPerPage={limit}")
        except Exception:
            return []
        out = []
        for hit in (data.get("hits") or []):
            item_id = hit.get("objectID")
            title = hit.get("title") or hit.get("story_title") or ""
            url = hit.get("url") or f"https://news.ycombinator.com/item?id={item_id}"
            text = hit.get("comment_text") or hit.get("story_text") or ""
            out.append({
                "source": "hackernews",
                "external_id": str(item_id),
                "title": title[:500] or f"HN {item_id}",
                "url": url[:500],
                "content": f"{title}\n\n{text}"[:8000],
                "author": (hit.get("author") or "")[:100],
                "metadata_json": {"points": hit.get("points"), "num_comments": hit.get("num_comments")},
                "collected_at": datetime.now(timezone.utc),
                "processed": False,
            })
        return out
