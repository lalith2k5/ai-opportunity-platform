import praw
from app.config import settings
from app.logger import logger

class RedditService:
    def __init__(self):
        if settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET:
            try:
                self.reddit = praw.Reddit(
                    client_id=settings.REDDIT_CLIENT_ID,
                    client_secret=settings.REDDIT_CLIENT_SECRET,
                    user_agent=settings.REDDIT_USER_AGENT,
                )
                logger.info("Reddit service initialized")
            except Exception as e:
                logger.warning(f"Reddit init failed: {e}")
                self.reddit = None
        else:
            logger.info("Reddit credentials not configured — skipping")
            self.reddit = None

    def search_posts(self, query: str, limit: int = 10):
        if not self.reddit:
            return []
        results = []
        try:
            for submission in self.reddit.subreddit("all").search(query, limit=limit, sort="relevance"):
                results.append({
                    "id": submission.id,
                    "title": submission.title,
                    "selftext": submission.selftext,
                    "url": submission.url,
                    "score": submission.score,
                    "num_comments": submission.num_comments,
                    "subreddit": str(submission.subreddit),
                })
            logger.info(f"Reddit: fetched {len(results)} posts")
        except Exception as e:
            logger.error(f"Reddit search error: {e}")
        return results
