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

    @staticmethod
    def _normalize_issue(item: dict) -> dict:
        """Reshape a GitHub search/issues result to the pipeline's shared shape.

        GitHub uses `body` for content and `html_url` for the link; every other
        source in this codebase uses `summary` and `url`. Aliasing here lets the
        orchestrator's documents loop treat issues identically to news and arxiv
        items, and lets _save_to_db dedupe them via a stable prefixed id.
        """
        raw_id = item.get("id")
        ext_id = f"github_issue:{raw_id}" if raw_id is not None else ""
        repo_url = item.get("repository_url", "") or ""
        repo_name = repo_url.rsplit("/", 1)[-1] if "/" in repo_url else ""
        return {
            "id": ext_id,
            "title": (item.get("title") or "").strip(),
            "summary": (item.get("body") or "").strip(),
            "url": item.get("html_url") or "",
            "published": item.get("created_at") or "",
            "state": item.get("state") or "",
            "comments": item.get("comments") or 0,
            "labels": [
                l.get("name") for l in (item.get("labels") or [])
                if isinstance(l, dict) and l.get("name")
            ],
            "repo": repo_name,
            "number": item.get("number"),
            "user": (item.get("user") or {}).get("login") or "",
        }

    def search_issues(self, query: str, per_page: int = 10):
        url = f"{self.BASE_URL}/search/issues"
        params = {"q": f"{query} is:issue", "sort": "comments", "order": "desc", "per_page": min(per_page, 100)}
        try:
            response = self._get(url, params)
            if response.status_code == 200:
                items = response.json().get("items", [])
                normalized = [self._normalize_issue(it) for it in items if it.get("title")]
                logger.info(f"GitHub: fetched {len(items)} issues ({len(normalized)} with title)")
                return normalized
        except Exception as e:
            logger.error(f"GitHub issues error: {e}")
        return []
