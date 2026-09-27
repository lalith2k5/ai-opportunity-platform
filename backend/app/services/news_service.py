import feedparser
from app.logger import logger
from app.services.retry_helper import api_retry


class NewsService:
    RSS_FEEDS = [
        "https://techcrunch.com/feed/",
        "https://www.wired.com/feed/rss",
        "https://feeds.arstechnica.com/arstechnica/index",
        "https://venturebeat.com/feed/",
        "https://www.theverge.com/rss/index.xml",
        "https://www.technologyreview.com/feed/",
        "https://syncedreview.com/feed/",
        "https://openai.com/blog/rss.xml",
        "https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml",
        "https://phys.org/rss-feed/technology-news/computer-sciences/",
        "https://www.forbes.com/innovation/feed2/",
        "https://news.crunchbase.com/feed/",
        "https://feeds.feedburner.com/TheHackersNews",
        "https://www.healthcareitnews.com/rss.xml",
        "https://www.nature.com/nature.rss",
        "https://www.science.org/rss/news_current.xml",
    ]

    @api_retry(max_attempts=2)
    def _fetch_feed(self, feed_url):
        return feedparser.parse(feed_url)

    def search_news(self, query: str, limit: int = 10):
        results = []
        query_lower = query.lower()
        seen_titles = set()

        for feed_url in self.RSS_FEEDS:
            try:
                feed = self._fetch_feed(feed_url)
                for entry in feed.entries[:60]:
                    title = entry.get("title", "")
                    summary = entry.get("summary", "")

                    if title.lower() in seen_titles:
                        continue

                    if query_lower in title.lower() or query_lower in summary.lower():
                        seen_titles.add(title.lower())
                        results.append({
                            "title": title,
                            "summary": summary,
                            "url": entry.get("link", ""),
                            "published": entry.get("published", ""),
                            "source": feed.feed.get("title", feed_url),
                        })
                        if len(results) >= limit:
                            logger.info(f"News: {len(results)} articles from {len(self.RSS_FEEDS)} feeds")
                            return results
            except Exception as e:
                logger.warning(f"RSS error for {feed_url}: {e}")

        logger.info(f"News: {len(results)} articles from {len(self.RSS_FEEDS)} feeds")
        return results
