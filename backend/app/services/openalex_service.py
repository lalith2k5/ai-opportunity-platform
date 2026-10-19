"""OpenAlex connector -- keyless REST API. Source class: RESEARCH."""
import requests
from datetime import datetime, timezone
from app.logger import logger

OPENALEX_API = "https://api.openalex.org/works"
DEFAULT_TIMEOUT = 15


class OpenAlexService:
    def __init__(self, timeout=DEFAULT_TIMEOUT, mailto=None):
        self.timeout = timeout
        self.mailto = mailto

    def search(self, query, rows=20, from_date=None):
        params = {
            "search": query,
            "per-page": min(rows, 200),
            "select": "id,doi,title,abstract_inverted_index,publication_year,authorships,cited_by_count,type,concepts",
        }
        if self.mailto:
            params["mailto"] = self.mailto
        if from_date:
            params["filter"] = f"from_publication_date:{from_date}"
        try:
            r = requests.get(OPENALEX_API, params=params, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            logger.warning(f"[OpenAlex] search failed: {e}")
            return []
        out = []
        for item in (data.get("results") or []):
            doc = self._to_document(item)
            if doc:
                out.append(doc)
        return out

    def _reconstruct_abstract(self, inverted_index):
        if not inverted_index or not isinstance(inverted_index, dict):
            return ""
        positions = []
        for word, idxs in inverted_index.items():
            for p in idxs:
                positions.append((p, word))
        positions.sort()
        return " ".join(w for _, w in positions)[:2000]

    def _to_document(self, item):
        oa_id = item.get("id") or ""
        doi = item.get("doi") or ""
        ext_id = doi or oa_id
        if not ext_id:
            return None
        title = item.get("title") or ""
        abstract = self._reconstruct_abstract(item.get("abstract_inverted_index"))
        authors = []
        for a in (item.get("authorships") or []):
            auth = a.get("author") or {}
            name = auth.get("display_name")
            if name:
                authors.append(name)
        url = doi or oa_id
        if url and not url.startswith("http"):
            url = "https://openalex.org/" + url.lstrip("/")
        concepts = [c.get("display_name") for c in (item.get("concepts") or [])[:5]]
        return {
            "source": "openalex",
            "external_id": ext_id[:200],
            "title": title[:500],
            "url": url[:500],
            "content": f"{title}\n\n{abstract}"[:8000],
            "author": ", ".join(authors)[:200],
            "metadata_json": {
                "publication_year": item.get("publication_year"),
                "cited_by_count": item.get("cited_by_count"),
                "type": item.get("type"),
                "concepts": concepts,
            },
            "collected_at": datetime.now(timezone.utc),
            "processed": False,
        }
