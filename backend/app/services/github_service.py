import requests
from app.config import settings
from app.logger import logger
from app.services.retry_helper import api_retry


class GitHubService:
    BASE_URL = "https://api.github.com"
    MAX_PER_PAGE = 100

    def __init__(self):
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if settings.GITHUB_TOKEN:
            self.headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"

    @api_retry(max_attempts=3)
    def _get(self, url, params):
        return requests.get(url, headers=self.headers, params=params, timeout=20)

    def search_repositories(self, query: str, per_page: int = 10):
        """Fetch up to `per_page` repos, paging if needed."""
        url = f"{self.BASE_URL}/search/repositories"
        collected = []
        page = 1
        while len(collected) < per_page:
            chunk = min(self.MAX_PER_PAGE, per_page - len(collected))
            params = {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": chunk,
                "page": page,
            }
            try:
                response = self._get(url, params)
                if response.status_code != 200:
                    logger.warning(f"GitHub repos status {response.status_code}")
                    break
                items = response.json().get("items", [])
                if not items:
                    break
                collected.extend(items)
                if len(items) < chunk:
                    break
                page += 1
                if page > 10:  # cap at 10 pages = 1000 results
                    break
            except Exception as e:
                logger.error(f"GitHub repos error: {e}")
                break
        logger.info(f"GitHub: fetched {len(collected)} repos for '{query}'")
        return collected

    def search_issues(self, query: str, per_page: int = 10):
        url = f"{self.BASE_URL}/search/issues"
        params = {"q": f"{query} is:issue", "sort": "comments", "order": "desc", "per_page": min(per_page, 100)}
        try:
            response = self._get(url, params)
            if response.status_code == 200:
                items = response.json().get("items", [])
                logger.info(f"GitHub: fetched {len(items)} issues")
                return items
        except Exception as e:
            logger.error(f"GitHub issues error: {e}")
        return []
