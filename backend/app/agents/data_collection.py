from concurrent.futures import ThreadPoolExecutor, as_completed
from app.services.github_service import GitHubService
from app.services.reddit_service import RedditService
from app.services.arxiv_service import ArxivService
from app.services.news_service import NewsService
from app.logger import logger

# Mode → per-source caps
MODES = {
    "quick": {"github": 8,   "arxiv": 8,   "news": 8,   "reddit": 8},
    "deep":  {"github": 100, "arxiv": 100, "news": 100, "reddit": 50},
}


class DataCollectionAgent:
    def __init__(self):
        self.github = GitHubService()
        self.reddit = RedditService()
        self.arxiv = ArxivService()
        self.news = NewsService()

    def collect_all(self, query: str, mode: str = "quick") -> dict:
        caps = MODES.get(mode, MODES["quick"])
        logger.info(f"[DataCollection] Fetching for '{query}' (mode={mode}, caps={caps})")

        tasks = {
            "github": lambda: self.github.search_repositories(query, per_page=caps["github"]),
            "arxiv":  lambda: self.arxiv.search_papers(query, max_results=caps["arxiv"]),
            "news":   lambda: self.news.search_news(query, limit=caps["news"]),
            "reddit": lambda: self.reddit.search_posts(query, limit=caps["reddit"]),
        }

        results = {"github": [], "arxiv": [], "news": [], "reddit": []}
        with ThreadPoolExecutor(max_workers=4) as ex:
            futures = {ex.submit(fn): name for name, fn in tasks.items()}
            for fut in as_completed(futures):
                name = futures[fut]
                try:
                    results[name] = fut.result()
                except Exception as e:
                    logger.error(f"[DataCollection] {name} failed: {e}")
                    results[name] = []

        logger.info(
            f"[DataCollection] Result: "
            f"{len(results['github'])} repos, "
            f"{len(results['arxiv'])} papers, "
            f"{len(results['news'])} news, "
            f"{len(results['reddit'])} reddit"
        )
        return results
