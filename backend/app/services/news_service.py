import feedparser
from app.logger import logger
from app.services.retry_helper import api_retry

class NewsService:
    RSS_FEEDS = [
        "https://techcrunch.com/feed/",
        "https://www.wired.com/feed/rss",
        "https://feeds.arstechnica.com/arstechnica/index",
        "https://www.technologyreview.com/feed/",
        "https://venturebeat.com/feed/",
    ]

    @api_retry(max_attempts=2)
    def _fetch_feed(self, feed_url):
        return feedparser.parse(feed_url)

    def search_news(self, query: str, limit: int = 10):
        results = []
        query_lower = query.lower()
        for feed_url in self.RSS_FEEDS:
            try:
                feed = self._fetch_feed(feed_url)
                for entry in feed.entries[:20]:
                    title = entry.get("title", "")
                    summary = entry.get("summary", "")
                    if query_lower in title.lower() or query_lower in summary.lower():
                        results.append({
                            "title": title,
                            "summary": summary,
                            "url": entry.get("link", ""),
                            "published": entry.get("published", ""),
                            "source": feed.feed.get("title", ""),
                        })
                        if len(results) >= limit:
                            logger.info(f"News: fetched {len(results)} matching articles")
                            return results
            except Exception as e:
                logger.warning(f"RSS error for {feed_url}: {e}")
        logger.info(f"News: fetched {len(results)} matching articles")
        return results
