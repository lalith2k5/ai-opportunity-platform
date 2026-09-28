from collections import Counter

from app.agents.opportunity_intelligence import _clean_keywords


# Generic words that make sense only inside a phrase (e.g. "artificial intelligence"),
# not as a trend on their own. Applied to singles only — phrases pass through untouched.
# Standalone single words that are too generic to be a trend on their own.
_TREND_SINGLE_BLOCKLIST = {
    "intelligence", "learning", "computing", "science", "technology",
    "machine", "computer", "computers", "algorithms", "algorithm",
    "run", "running", "runs", "use", "using", "used", "make", "making",
    "study", "studies", "work", "works", "show", "shows",
    "python", "javascript", "typescript", "golang", "rust", "java",
    "exercises", "exercise", "programming", "tutorial", "course",
    "site", "online", "spanish", "hackathon", "university",
    "chapter", "lecture", "homework", "assignment",
    "quantum", "cyber", "computing", "advanced", "basics",
}

# Multi-word items are ONLY kept if they appear here. This is stricter than a
# blocklist but prevents TF-IDF-generated bigrams like "exercises learning"
# from ever reaching the UI.
_VALID_TREND_PHRASES = {
    # AI / ML
    "machine learning", "deep learning", "artificial intelligence",
    "neural network", "neural networks", "computer vision",
    "natural language", "natural language processing",
    "reinforcement learning", "federated learning", "transfer learning",
    "generative ai", "large language", "large language model",
    "large language models", "explainable ai",
    # Quantum
    "quantum computing", "quantum computer", "quantum computers",
    "quantum algorithms", "quantum machine", "quantum cryptography",
    "quantum information", "quantum simulation",
    # Security
    "cyber security", "cybersecurity", "intrusion detection",
    "anomaly detection", "reverse engineering",
    # Data
    "data science", "big data", "data analysis", "data mining",
    # Other technologies
    "blockchain", "supply chain", "public health", "edge computing",
    "cloud computing", "image segmentation", "image classification",
    "image processing", "medical imaging", "object detection",
    "autonomous vehicles", "self driving", "open source",
}


def _is_valid_item(item: str) -> bool:
    """A trend is valid if it's a meaningful single word, or a whitelisted phrase."""
    low = item.lower().strip()
    if not low:
        return False
    words = low.split()
    if len(words) == 1:
        if low in _TREND_SINGLE_BLOCKLIST:
            return False
        if len(low) < 4:
            return False
        return True
    # Multi-word: only whitelist passes
    return low in _VALID_TREND_PHRASES


def _clean_list(raw: list) -> list:
    """Filter every extracted keyword through the trend validity check."""
    cleaned = _clean_keywords(raw or [])
    items = cleaned["phrases"] + cleaned["singles"]
    seen = set()
    out = []
    for item in items:
        low = item.lower().strip()
        if low in seen:
            continue
        seen.add(low)
        if _is_valid_item(item):
            out.append(item)
    return out


class InnovationMonitorAgent:
    """Count how often cleaned keywords appear across all documents.

    Uses the same noise filter as the title/scoring pipeline, plus a
    trend-specific blocklist, so generic words (run, software, research,
    intelligence) don't appear as standalone trends.
    """

    MAX_TRENDS = 10

    def monitor(self, documents: list, clusters: list = None) -> list:
        """Count cleaned keywords across docs and enrich each trend with
        SRS §14 signals: mentions, source frequency, publication frequency
        (arXiv hit ratio), and problem recurrence (clusters that mention it)."""
        keyword_counter = Counter()
        source_counter = Counter()
        # Per-keyword, per-source hit counts -- computed while walking docs
        per_kw_source = {}

        for doc in documents:
            src = doc.get("source", "unknown")
            source_counter[src] += 1
            for kw in _clean_list(doc.get("keywords") or []):
                key = kw.lower()
                keyword_counter[key] += 1
                d = per_kw_source.setdefault(key, Counter())
                d[src] += 1

        # Pre-extract cluster keyword sets for problem_recurrence
        cluster_kw_sets = []
        if clusters:
            for c in clusters:
                kws = {str(k).lower() for k in (c.get("keywords") or []) if k}
                if kws:
                    cluster_kw_sets.append(kws)

        arxiv_doc_count = source_counter.get("arxiv", 0) or 1

        trends = []
        for keyword, count in keyword_counter.most_common(self.MAX_TRENDS):
            per_src = dict(per_kw_source.get(keyword, {}))
            arxiv_hits = per_src.get("arxiv", 0)
            publication_frequency = round(arxiv_hits / arxiv_doc_count, 3)

            problem_recurrence = sum(
                1 for kws in cluster_kw_sets if keyword in kws
            )

            trends.append({
                "name": keyword,
                "category": "emerging_technology",
                "trend_score": min(1.0, count / 10.0),
                "source_data": {
                    "mentions": count,
                    "sources": dict(source_counter),
                    "per_source": per_src,
                    "publication_frequency": publication_frequency,
                    "problem_recurrence": problem_recurrence,
                },
            })
        return trends
