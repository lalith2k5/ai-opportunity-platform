"""
R&D Cells service — fetches research blog posts from corporate,
academic, and government research labs.

Feeds are RSS/Atom. Output shape matches NewsService so the rest
of the pipeline treats it identically.
"""
import feedparser
from app.logger import logger
from app.services.retry_helper import api_retry


class RDCellsService:
    # Corporate labs — verified working feeds
    CORPORATE_FEEDS = [
        ("Google Research",       "https://research.google/blog/rss/"),
        ("Microsoft Research",    "https://www.microsoft.com/en-us/research/feed/"),
        ("DeepMind",              "https://deepmind.google/blog/feed/basic/"),
        ("NVIDIA Research",       "https://blogs.nvidia.com/feed/"),
        ("Apple ML Research",     "https://machinelearning.apple.com/rss.xml"),
        ("OpenAI Research",       "https://openai.com/news/rss.xml"),
        ("Meta Engineering",      "https://engineering.fb.com/feed/"),
        ("AWS Science",           "https://www.amazon.science/index.rss"),
    ]

    # Academic / non-profit labs
    ACADEMIC_FEEDS = [
        ("MIT CSAIL",             "https://news.mit.edu/topic/mitcomputer-science-and-artificial-intelligence-laboratory-csail-rss.xml"),
        ("MIT News AI",           "https://news.mit.edu/rss/topic/artificial-intelligence2"),
        ("Berkeley AI Research",  "https://bair.berkeley.edu/blog/feed.xml"),
        ("Allen Institute AI",    "https://allenai.org/rss.xml"),
        ("CMU ML",                "https://blog.ml.cmu.edu/feed/"),
    ]

    # Government / defense labs
    GOVERNMENT_FEEDS = [
        ("DARPA",                 "https://www.darpa.mil/rss/news.xml"),
        ("NASA",                  "https://www.nasa.gov/rss/dyn/breaking_news.rss"),
    ]

    ALL_FEEDS = CORPORATE_FEEDS + ACADEMIC_FEEDS + GOVERNMENT_FEEDS

    STOPWORDS = {
        "the", "a", "an", "of", "and", "or", "to", "in", "for", "on",
        "with", "at", "by", "is", "are", "be", "was", "were", "as",
        "it", "its", "this", "that", "these", "those", "from", "into",
    }

    @api_retry(max_attempts=2)
    def _fetch_feed(self, url):
        return feedparser.parse(url)

    def _query_tokens(self, query: str) -> list:
        """Split query into meaningful tokens (stopwords + shorts removed)."""
        words = [w.strip(".,!?;:'\"()[]{}") for w in query.lower().split()]
        tokens = [w for w in words if len(w) >= 3 and w not in self.STOPWORDS]
        return tokens or [w for w in words if w]  # fallback to raw if all filtered

    def _matches(self, text: str, tokens: list) -> int:
        """Return number of matching tokens (0 = no match)."""
        text_lower = text.lower()
        return sum(1 for tok in tokens if tok in text_lower)

    def search_rd_cells(self, query: str, limit: int = 20):
        """Fetch posts from R&D lab feeds matching the query. Returns normalized list."""
        results = []
        tokens = self._query_tokens(query)
        seen_titles = set()

        for lab_name, feed_url in self.ALL_FEEDS:
            try:
                feed = self._fetch_feed(feed_url)
                for entry in feed.entries[:40]:
                    title = entry.get("title", "")
                    summary = entry.get("summary", "") or entry.get("description", "")

                    # Dedup by title across all feeds
                    title_key = title.lower().strip()
                    if not title_key or title_key in seen_titles:
                        continue

                    # Match: require at least one query token in title or summary
                    haystack = title + " " + summary
                    score = self._matches(haystack, tokens)
                    if score > 0:
                        seen_titles.add(title_key)
                        results.append({
                            "id": f"rdcell:{lab_name}:{entry.get('id', title[:60])}",
                            "title": title,
                            "summary": summary,
                            "url": entry.get("link", ""),
                            "published": entry.get("published", ""),
                            "source": "rd_cells",
                            "lab": lab_name,
                            "score": score,
                        })
                        if len(results) >= limit * 4:
                            # Collect extra candidates, sort by score, return top N
                            results.sort(key=lambda r: r.get("score", 0), reverse=True)
                            top = results[:limit]
                            logger.info(
                                f"R&D Cells: {len(top)} posts (from {len(results)} "
                                f"candidates across {len(self.ALL_FEEDS)} lab feeds)"
                            )
                            return top
            except Exception as e:
                logger.warning(f"R&D Cells feed error [{lab_name}]: {e}")

        results.sort(key=lambda r: r.get("score", 0), reverse=True)
        top = results[:limit]
        logger.info(
            f"R&D Cells: {len(top)} posts (from {len(results)} "
            f"candidates across {len(self.ALL_FEEDS)} lab feeds)"
        )
        return top
