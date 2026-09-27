import requests
from app.config import settings
from app.logger import logger
from app.services.retry_helper import api_retry

class GitHubService:
    BASE_URL = "https://api.github.com"

    def __init__(self):
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if settings.GITHUB_TOKEN:
            self.headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"

    @api_retry(max_attempts=3)
    def _get(self, url, params):
        return requests.get(url, headers=self.headers, params=params, timeout=15)

    def search_repositories(self, query: str, per_page: int = 10):
        url = f"{self.BASE_URL}/search/repositories"
        params = {"q": query, "sort": "stars", "order": "desc", "per_page": per_page}
        try:
            response = self._get(url, params)
            if response.status_code == 200:
                items = response.json().get("items", [])
                logger.info(f"GitHub: fetched {len(items)} repos for '{query}'")
                return items
            logger.warning(f"GitHub repos status {response.status_code}")
        except Exception as e:
            logger.error(f"GitHub repos error: {e}")
        return []

    def search_issues(self, query: str, per_page: int = 10):
        url = f"{self.BASE_URL}/search/issues"
        params = {"q": f"{query} is:issue", "sort": "comments", "order": "desc", "per_page": per_page}
        try:
            response = self._get(url, params)
            if response.status_code == 200:
                items = response.json().get("items", [])
                logger.info(f"GitHub: fetched {len(items)} issues")
                return items
        except Exception as e:
            logger.error(f"GitHub issues error: {e}")
        return []
