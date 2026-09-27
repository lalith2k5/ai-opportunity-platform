"""Fetch public R&D/industry problem statements from challenge portals.

Sources:
  - SBIR.gov solicitations (via public web API)
  - Challenge.gov RSS feed
  - NASA + NSF + NIST public RSS feeds as fallback sources

Each result is normalized into:
    id, title, organization, description, url, published, source, raw_text
"""
import re
import html

import feedparser
import requests

from app.logger import logger
from app.services.retry_helper import api_retry


_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")

_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
_HEADERS = {
    "User-Agent": _UA,
    "Accept": "application/json, application/rss+xml, text/xml, application/xml, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.sbir.gov/",
    "Origin": "https://www.sbir.gov",
}


def _clean_html(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = _TAG_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text).strip()
    return text


class ChallengePortalService:
    # Multiple endpoints tried in order — SBIR has moved this around
    SBIR_ENDPOINTS = [
        "https://api.www.sbir.gov/public/api/solicitations",
        "https://www.sbir.gov/api/solicitations",
    ]

    RSS_FEEDS = [
        ("challenge_gov", "US Federal Agency (Challenge.gov)",
         "https://www.challenge.gov/?post_type=challenge&feed=rss2"),
        ("nasa", "NASA", "https://www.nasa.gov/rss/dyn/breaking_news.rss"),
        ("nsf", "National Science Foundation",
         "https://www.nsf.gov/rss/rss_www_news.xml"),
        ("nist", "NIST", "https://www.nist.gov/news-events/news/rss.xml"),
        ("darpa", "DARPA", "https://www.darpa.mil/rss/news"),
        ("nih", "NIH", "https://www.nih.gov/news-events/news-releases/rss.xml"),
        ("nsf_awards", "NSF Awards",
         "https://www.nsf.gov/rss/rss_www_awards.xml"),
        ("energy_gov", "Department of Energy",
         "https://www.energy.gov/rss/news"),
        ("cdc", "CDC", "https://tools.cdc.gov/api/v2/resources/media/403372.rss"),
    ]

    HARD_CAP = 40

    @api_retry(max_attempts=2)
    def _get_json(self, url, params=None):
        return requests.get(url, params=params, headers=_HEADERS, timeout=30)

    @api_retry(max_attempts=2)
    def _fetch_rss(self, url):
        # feedparser accepts a custom agent argument
        return feedparser.parse(url, agent=_UA)

    # ---------- SBIR ----------
    def _fetch_sbir(self, query: str, limit: int) -> list:
        items = []
        for endpoint in self.SBIR_ENDPOINTS:
            try:
                resp = self._get_json(endpoint, params={"rows": min(limit, 40), "start": 0})
                if resp.status_code == 200:
                    data = resp.json()
                    items = data if isinstance(data, list) else data.get("data", [])
                    if items:
                        break
                else:
                    logger.debug(f"SBIR {endpoint} status {resp.status_code}")
            except Exception as e:
                logger.debug(f"SBIR {endpoint} failed: {e}")
                continue
        if not items:
            logger.info("SBIR endpoints all unavailable — relying on agency RSS feeds")
            return []

        results = []
        for raw in items[: limit * 2]:
            title = _clean_html(raw.get("solicitation_title") or "")
            if not title:
                continue
            parts = [
                title,
                _clean_html(raw.get("solicitation_agency") or ""),
                _clean_html(raw.get("agency") or ""),
                _clean_html(raw.get("branch") or ""),
                _clean_html(raw.get("program") or ""),
                _clean_html(raw.get("topic_description") or ""),
                _clean_html(raw.get("solicitation_description") or ""),
            ]
            raw_text = " ".join(p for p in parts if p).strip()
            results.append({
                "id": f"sbir:{raw.get('solicitation_id') or raw.get('id') or title[:60]}",
                "title": title,
                "organization": _clean_html(raw.get("agency") or raw.get("branch") or "SBIR"),
                "description": raw_text[:4000],
                "url": raw.get("solicitation_url") or raw.get("url") or "",
                "published": raw.get("open_date") or raw.get("close_date") or "",
                "source": "sbir",
                "raw_text": raw_text[:4000],
            })
            if len(results) >= limit:
                break
        return results

    # ---------- RSS feeds (challenge.gov + agencies) ----------
    def _fetch_rss_source(self, source_name: str, org_label: str, url: str,
                          query: str, limit: int) -> list:
        try:
            feed = self._fetch_rss(url)
        except Exception as e:
            logger.warning(f"{source_name} RSS failed: {e}")
            return []

        results = []
        q_lower = query.lower()
        for entry in feed.entries[: limit * 4]:
            title = _clean_html(entry.get("title") or "")
            summary = _clean_html(entry.get("summary") or entry.get("description") or "")
            if not title:
                continue
            full = (title + " " + summary).lower()
            # Loose matching: allow 3+ char tokens OR prefix match on stems.
            # Accept acronyms separately (ai, ml, nlp).
            if q_lower:
                q_tokens = [t for t in re.split(r"\W+", q_lower) if len(t) >= 3]
                acronyms = [t for t in re.split(r"\W+", q_lower) if 2 <= len(t) < 3]
                if q_tokens or acronyms:
                    matched = any(
                        (t in full) or (t[:5] in full and len(t) >= 6)
                        for t in q_tokens
                    ) or any(f" {a} " in f" {full} " for a in acronyms)
                    if not matched:
                        continue
            results.append({
                "id": f"{source_name}:{entry.get('id') or entry.get('link') or title[:60]}",
                "title": title,
                "organization": org_label,
                "description": summary[:4000],
                "url": entry.get("link", ""),
                "published": entry.get("published", ""),
                "source": source_name,
                "raw_text": (title + " " + summary)[:4000],
            })
            if len(results) >= limit:
                break
        return results

    def fetch_all(self, query: str, limit: int = 20) -> list:
        limit = min(limit, self.HARD_CAP)
        per_source = max(3, limit // 3)

        results = []
        results.extend(self._fetch_sbir(query, per_source))
        for name, org, url in self.RSS_FEEDS:
            results.extend(self._fetch_rss_source(name, org, url, query, per_source))

        # Dedup by normalized title
        seen = set()
        deduped = []
        for r in results:
            key = r["title"].lower().strip()[:120]
            if key in seen:
                continue
            seen.add(key)
            deduped.append(r)

        deduped = deduped[:limit]
        by_src = {}
        for r in deduped:
            by_src[r["source"]] = by_src.get(r["source"], 0) + 1
        logger.info(f"Challenge portals: {len(deduped)} items by source {by_src} for '{query}'")
        return deduped
