"""EPO Open Patent Services (OPS) v3.2 -- OAuth2 client credentials, 4GB/week free."""
import requests
import time
from datetime import datetime, timezone
from app.config import settings
from app.services.api_keys import get_key
from app.logger import logger

AUTH_URL = "https://ops.epo.org/3.2/auth/accesstoken"
BASE = "https://ops.epo.org/3.2/rest-services"
DEFAULT_TIMEOUT = 30

class EpoOpsService:
    def __init__(self, timeout=DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.consumer_key = get_key("EPO_OPS_CONSUMER_KEY")
        self.consumer_secret = get_key("EPO_OPS_CONSUMER_SECRET")
        self._token = None
        self._token_expiry = 0.0

    def is_configured(self):
        return bool(self.consumer_key and self.consumer_secret)

    def _get_token(self):
        if self._token and time.time() < self._token_expiry - 60:
            return self._token
        if not self.is_configured():
            return None
        try:
            r = requests.post(
                AUTH_URL,
                data={"grant_type": "client_credentials"},
                auth=(self.consumer_key, self.consumer_secret),
                timeout=self.timeout,
            )
            r.raise_for_status()
            d = r.json()
            self._token = d.get("access_token")
            self._token_expiry = time.time() + int(d.get("expires_in", 1200))
            return self._token
        except Exception as e:
            logger.warning(f"[EPO] token failed: {e}")
            return None

    def search(self, query, limit=20):
        token = self._get_token()
        if not token:
            logger.warning("[EPO] no token -- set EPO_OPS_CONSUMER_KEY/SECRET")
            return []
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        params = {"q": query, "Range": f"1-{min(max(limit, 1), 100)}"}
        try:
            r = requests.get(f"{BASE}/published-data/search", params=params, headers=headers, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            logger.warning(f"[EPO] search failed: {e}")
            return []
        docs = []
        try:
            results = data.get("ops:world-patent-data", {}).get("ops:biblio-search", {}).get("ops:search-result", {}).get("ops:publication-reference", [])
            if isinstance(results, dict):
                results = [results]
            for it in results:
                d = self._to_doc(it)
                if d:
                    docs.append(d)
        except Exception:
            pass
        return docs

    def _to_doc(self, item):
        try:
            doc_id = item.get("document-id", [{}])
            if isinstance(doc_id, dict):
                doc_id = [doc_id]
            first = doc_id[0] if doc_id else {}
            num = first.get("doc-number", {}).get("$") if isinstance(first.get("doc-number"), dict) else first.get("doc-number")
            country = first.get("country", {}).get("$") if isinstance(first.get("country"), dict) else first.get("country")
            if not num:
                return None
            title = first.get("title") or ""
            abstract = first.get("abstract") or ""
            return {
                "source": "epo",
                "external_id": f"{country or ''}{num}"[:200],
                "title": str(title)[:500] or f"EPO patent {country}{num}",
                "url": f"https://worldwide.espacenet.com/patent/search?q=pn%3D{country}{num}"[:500],
                "content": f"{title}\n\n{abstract}"[:8000],
                "author": "",
                "metadata_json": {"country": country, "doc_number": num},
                "collected_at": datetime.now(timezone.utc),
                "processed": False,
            }
        except Exception:
            return None
