"""Crossref connector -- keyless REST API. Source class: RESEARCH."""
import requests
from datetime import datetime, timezone
from app.logger import logger

CROSSREF_API = "https://api.crossref.org/works"
DEFAULT_TIMEOUT = 15


class CrossrefService:
    def __init__(self, timeout=DEFAULT_TIMEOUT, mailto=None):
        self.timeout = timeout
        self.mailto = mailto

    def search(self, query, rows=20, from_date=None):
        params = {
            "query": query,
            "rows": rows,
            "select": "DOI,title,abstract,author,published,URL,type,publisher",
        }
        if self.mailto:
            params["mailto"] = self.mailto
        if from_date:
            params["filter"] = f"from-pub-date:{from_date}"
        try:
            r = requests.get(CROSSREF_API, params=params, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            logger.warning(f"[Crossref] search failed: {e}")
            return []
        out = []
        for item in (data.get("message", {}).get("items") or []):
            doc = self._to_document(item)
            if doc:
                out.append(doc)
        return out

    def _to_document(self, item):
        doi = item.get("DOI")
        if not doi:
            return None
        title_raw = item.get("title")
        if isinstance(title_raw, list):
            title = (title_raw[0] if title_raw else "") or ""
        else:
            title = title_raw or ""
        abstract = item.get("abstract") or ""
        authors = []
        for a in (item.get("author") or []):
            name = f"{a.get('given', '')} {a.get('family', '')}".strip()
            if name:
                authors.append(name)
        published = item.get("published", {}).get("date-parts", [[None]])
        pub_parts = published[0] if published else [None]
        pub_str = "-".join(str(p) for p in pub_parts if p)
        return {
            "source": "crossref",
            "external_id": doi,
            "title": title[:500] or f"DOI {doi}",
            "url": f"https://doi.org/{doi}"[:500],
            "content": f"{title}\n\n{abstract}"[:8000],
            "author": ", ".join(authors)[:200],
            "metadata_json": {
                "doi": doi,
                "published": pub_str,
                "type": item.get("type"),
                "publisher": item.get("publisher"),
            },
            "collected_at": datetime.now(timezone.utc),
            "processed": False,
        }
