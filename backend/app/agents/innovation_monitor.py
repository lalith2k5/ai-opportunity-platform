from collections import Counter

from app.agents.opportunity_intelligence import _clean_keywords


# Generic words that make sense only inside a phrase (e.g. "artificial intelligence"),
# not as a trend on their own. Applied to singles only — phrases pass through untouched.
_TREND_SINGLE_BLOCKLIST = {
    "intelligence", "learning", "computing", "science", "technology",
    "run", "running", "runs", "use", "using", "used", "make", "making",
    "python", "javascript", "typescript", "golang", "rust",
    "study", "studies", "work", "works", "show", "shows",
}


def _clean_list(raw: list) -> list:
    """Run keywords through the shared cleaning pipeline, then drop any
    standalone singles that are pure filler for trend purposes."""
    cleaned = _clean_keywords(raw or [])
    phrases = cleaned["phrases"]
    singles = [
        s for s in cleaned["singles"]
        if s.lower() not in _TREND_SINGLE_BLOCKLIST
    ]
    return phrases + singles


class InnovationMonitorAgent:
    """Count how often cleaned keywords appear across all documents.

    Uses the same noise filter as the title/scoring pipeline, plus a
    trend-specific blocklist, so generic words (run, software, research,
    intelligence) don't appear as standalone trends.
    """

    MAX_TRENDS = 10

    def monitor(self, documents: list) -> list:
        keyword_counter = Counter()
        source_counter = Counter()

        for doc in documents:
            source_counter[doc.get("source", "unknown")] += 1
            for kw in _clean_list(doc.get("keywords") or []):
                keyword_counter[kw.lower()] += 1

        trends = []
        for keyword, count in keyword_counter.most_common(self.MAX_TRENDS):
            trends.append({
                "name": keyword,
                "category": "emerging_technology",
                "trend_score": min(1.0, count / 10.0),
                "source_data": {
                    "mentions": count,
                    "sources": dict(source_counter),
                },
            })
        return trends
