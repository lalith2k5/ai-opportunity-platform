from app.services.github_service import GitHubService
from app.services.reddit_service import RedditService
from app.services.arxiv_service import ArxivService
from app.services.news_service import NewsService

class DataCollectionAgent:
    def __init__(self):
        self.github = GitHubService()
        self.reddit = RedditService()
        self.arxiv = ArxivService()
        self.news = NewsService()

    def collect_all(self, query: str) -> dict:
        print(f"[DataCollection] Fetching data for: {query}")
        github_repos = self.github.search_repositories(query, per_page=8)
        print(f"[DataCollection] GitHub: {len(github_repos)} repos")
        arxiv_papers = self.arxiv.search_papers(query, max_results=8)
        print(f"[DataCollection] arXiv: {len(arxiv_papers)} papers")
        news = self.news.search_news(query, limit=8)
        print(f"[DataCollection] News: {len(news)} articles")
        reddit = self.reddit.search_posts(query, limit=8)
        print(f"[DataCollection] Reddit: {len(reddit)} posts")
        return {
            "github": github_repos,
            "arxiv": arxiv_papers,
            "news": news,
            "reddit": reddit
        }
