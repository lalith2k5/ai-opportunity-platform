from concurrent.futures import ThreadPoolExecutor, as_completed
from app.services.github_service import GitHubService
from app.services.reddit_service import RedditService
from app.services.arxiv_service import ArxivService
from app.services.news_service import NewsService
from app.services.rd_cells_service import RDCellsService
from app.services.patents_service import PatentsService
from app.logger import logger

# Mode → per-source caps
MODES = {
    "quick": {"github": 8,   "arxiv": 8,   "news": 8,   "reddit": 8,   "rd_cells": 8,   "patents": 8,   "github_issues": 8},
    "deep":  {"github": 100, "arxiv": 100, "news": 100, "reddit": 50,  "rd_cells": 60,  "patents": 50,  "github_issues": 50},
}


class DataCollectionAgent:
    def __init__(self):
        self.github = GitHubService()
        self.reddit = RedditService()
        self.arxiv = ArxivService()
        self.news = NewsService()
        self.rd_cells = RDCellsService()
        self.patents = PatentsService()

    def _active_source_names(self):
        """Return the set of active DataSource names, or None if none registered.

        None means 'no registry configured -> allow all'. An empty set means
        every source is disabled (unlikely but honoured literally).
        """
        try:
            from app.database import SessionLocal
            from app import models as _m
            db = SessionLocal()
            try:
                rows = db.query(_m.DataSource).all()
                if not rows:
                    return None
                return {r.name for r in rows if r.is_active}
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"[DataCollection] active-source lookup failed: {e}")
            return None

    def collect_all(self, query: str, mode: str = "quick") -> dict:
        caps = MODES.get(mode, MODES["quick"])
        logger.info(f"[DataCollection] Fetching for '{query}' (mode={mode}, caps={caps})")

        tasks = {
            "github":        lambda: self.github.search_repositories(query, per_page=caps["github"]),
            "github_issues": lambda: self.github.search_issues(query, per_page=caps["github_issues"]),
            "arxiv":    lambda: self.arxiv.search_papers(query, max_results=caps["arxiv"]),
            "news":     lambda: self.news.search_news(query, limit=caps["news"]),
            "reddit":   lambda: self.reddit.search_posts(query, limit=caps["reddit"]),
            "rd_cells": lambda: self.rd_cells.search_rd_cells(query, limit=caps["rd_cells"]),
            "patents":  lambda: self.patents.search_patents(query, limit=caps["patents"]),
        }

        # ---- Phase 10.8: SRS FR-01 -- filter by active DataSource registry ----
        active = self._active_source_names()
        if active is not None:
            name_to_ds = {
                "github": "github",
                "github_issues": "github",   # shares the github DataSource row
                "arxiv": "arxiv",
                "news": "news",
                "reddit": "reddit",
                "rd_cells": "rd_cells",
                "patents": "patents",
            }
            before = sorted(tasks.keys())
            tasks = {k: v for k, v in tasks.items() if name_to_ds.get(k) in active}
            logger.info(
                f"[DataCollection] active filter -> kept {sorted(tasks.keys())} "
                f"(dropped {sorted(set(before) - set(tasks.keys()))})"
            )

        results = {"github": [], "github_issues": [], "arxiv": [], "news": [], "reddit": [], "rd_cells": [], "patents": []}
        with ThreadPoolExecutor(max_workers=4) as ex:
            futures = {ex.submit(fn): name for name, fn in tasks.items()}
            for fut in as_completed(futures):
                name = futures[fut]
                try:
                    results[name] = fut.result()
                except Exception as e:
                    logger.error(f"[DataCollection] {name} failed: {e}")
                    results[name] = []

        # ---- D5: update Source.last_fetched for sources that just ran ----
        try:
            from app.database import SessionLocal as _SLlf
            from app import models as _mlf
            from datetime import datetime as _dtlf, timezone as _tzlf
            _dblf = _SLlf()
            try:
                _name_map = {
                    "github": "github",
                    "github_issues": "github",
                    "arxiv": "arxiv",
                    "news": "news",
                    "reddit": "reddit",
                    "rd_cells": "rd_cells",
                    "patents": "patents",
                }
                _now = _dtlf.now(_tzlf.utc)
                _touched = set()
                for task_name in tasks.keys():
                    ds_name = _name_map.get(task_name)
                    if not ds_name or ds_name in _touched:
                        continue
                    _touched.add(ds_name)
                    _row = _dblf.query(_mlf.Source).filter(_mlf.Source.name == ds_name).first()
                    if _row:
                        _row.last_fetched = _now
                _dblf.commit()
            finally:
                _dblf.close()
        except Exception as _e:
            logger.warning(f"[DataCollection] last_fetched update failed: {_e}")

        logger.info(
            f"[DataCollection] Result: "
            f"{len(results['github'])} repos, "
            f"{len(results['github_issues'])} issues, "
            f"{len(results['arxiv'])} papers, "
            f"{len(results['news'])} news, "
            f"{len(results['reddit'])} reddit, "
            f"{len(results['patents'])} patents"
        )
        return results
