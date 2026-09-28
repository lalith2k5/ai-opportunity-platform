from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np
from app.agents import opportunity_intelligence as _oi
from app.agents.opportunity_intelligence import _clean_keywords, _title_case


_EXTRA_NOISE = {
    # Institutions / brands
    "mit", "stanford", "berkeley", "cmu", "oxford", "cambridge", "harvard",
    "caltech", "eth", "epfl", "openai", "anthropic", "deepmind", "gemini",
    "claude", "chatgpt", "gpt", "copilot",
    # Corporate / meeting boilerplate
    "group", "advisory", "committee", "board", "member", "members",
    "chair", "chairman", "director", "directors", "president",
    "session", "workshop", "symposium", "seminar", "conference",
    "meeting", "meetings", "summit", "forum", "panel", "keynote",
    "strategic", "highlights", "recap", "bulletin", "newsletter",
    # Academic / publication boilerplate
    "journal", "volume", "issue", "edition", "editor", "editorial",
    "proceedings", "transaction", "transactions", "abstract",
    "introduction", "conclusion", "conclusions", "appendix",
    "figure", "figures", "table", "tables", "equation", "equations",
    "copyright", "license", "affiliation", "affiliations", "corresponding",
    "received", "accepted", "published", "revised", "submitted",
    "author", "authors", "manuscript", "submission", "preprint",
    "fellowships", "fellowship", "scholarship", "scholarships",
    # Numbers-as-words
    "hundred", "thousand", "million", "billion", "trillion", "zero",
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    # Generic verbs / connectors that TF-IDF over-weights
    "wants", "want", "wanted", "wanted", "says", "said", "said",
    "shows", "showed", "shown", "gives", "gave", "given",
    "makes", "made", "takes", "took", "taken", "goes", "went",
    # Over-broad single-word topics (too generic to be a title)
    "emerging", "standards", "standard", "detector", "detectors",
    "polygraph", "zipper", "brain", "lie", "lies", "truth", "false",
    "inspired", "inspiring", "chip", "chips", "objective", "objectives",
    # ---- Phase 10.12: cluster-title noise seen in prod ----
    "centers", "center", "centres", "centre", "leadership", "leaders",
    "leader", "collapse", "partial", "releases", "release", "released",
    "issues", "issue", "concerns", "concern", "problems", "problem",
    "challenges", "challenge", "priorities", "priority", "focus",
    "areas", "area", "domains", "domain", "fields", "field",
    "trends", "trend", "topics", "topic", "themes", "theme",
    "outcomes", "outcome", "results", "result", "findings",
    "analysis", "overview", "summary", "review", "reviews",
    "products", "product", "services", "service", "applications",
    "industries", "industry", "companies", "company", "organizations",
    "groups", "group", "teams", "team", "members", "member",
    "general", "particular", "specific", "various", "multiple",
    "different", "similar", "related", "relevant", "important",
    "significant", "major", "minor", "common", "typical",
    "quality", "quantity", "level", "levels", "scale",
    "types", "type", "kinds", "kind", "forms", "form",
    "problems", "solutions", "solution", "approaches", "approach",
    "methods", "method", "techniques", "technique", "strategies",
    "practices", "practice", "principles", "principle",
    "processes", "process", "procedures", "procedure",
    "proposals", "proposal", "plans", "plan", "planning",
    "objectives", "objective", "goals", "goal", "targets", "target",
}
_oi.NOISE_WORDS.update(_EXTRA_NOISE)

# Short words allowed through (real acronyms/tech terms)
_SHORT_ALLOWED = {
    "ai", "ml", "iot", "nlp", "llm", "rag", "api", "ui", "ux", "db",
    "sql", "aws", "gcp", "xai", "ar", "vr", "cnn", "rnn", "lstm",
    "gan", "vae", "svm", "gpt", "bert", "5g", "6g", "3d",
}


class ProblemDiscoveryAgent:
    MIN_CLUSTERS = 5
    MAX_CLUSTERS = 30
    MIN_KEYWORDS_TO_KEEP = 3   # <- stricter: need 3+ meaningful keywords

    def _clean_topic_keywords(self, raw_keywords: list) -> list:
        cleaned = _clean_keywords(raw_keywords or [])
        combined = cleaned["phrases"] + cleaned["singles"]
        # Reject 3-char words unless they're a known acronym
        out = []
        for k in combined:
            if " " in k or len(k) >= 4 or k.lower() in _SHORT_ALLOWED:
                out.append(k)
        return out

    def _build_cluster_title(self, clean_keywords: list) -> str:
        label = ", ".join(_title_case(k) for k in clean_keywords[:3])
        return f"Problem Cluster: {label}"

    def discover(self, documents: list, n_clusters: int = None) -> list:
        # Build texts while preserving original indices so downstream
        # consumers (sentiment averaging) can map back to the source doc.
        texts = []
        orig_indices = []
        for i, d in enumerate(documents):
            if not d.get("title"):
                continue
            texts.append(d.get("title", "") + " " + (d.get("content", "") or "")[:500])
            orig_indices.append(i)
        if len(texts) < 2:
            return []

        if n_clusters is None:
            n_clusters = max(self.MIN_CLUSTERS, min(self.MAX_CLUSTERS, len(texts) // 8))
        n_clusters = min(n_clusters, len(texts))

        try:
            vectorizer = TfidfVectorizer(
                max_features=min(500, max(100, len(texts) * 5)),
                stop_words="english",
            )
            X = vectorizer.fit_transform(texts)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X)
            feature_names = vectorizer.get_feature_names_out()
            clusters = []
            for i in range(n_clusters):
                indices_in_texts = np.where(labels == i)[0]
                if len(indices_in_texts) == 0:
                    continue
                center = kmeans.cluster_centers_[i]
                top_keywords = [feature_names[j] for j in center.argsort()[-8:][::-1]]

                clean_kws = self._clean_topic_keywords(top_keywords)
                if len(clean_kws) < self.MIN_KEYWORDS_TO_KEEP:
                    continue

                # Map cluster membership back to indices in the original
                # `documents` list (used for per-cluster sentiment aggregation).
                doc_indices = [orig_indices[j] for j in indices_in_texts]

                clusters.append({
                    "title": self._build_cluster_title(clean_kws),
                    "description": f"Recurring issues related to: {', '.join(clean_kws[:8])}",
                    "keywords": clean_kws,
                    "source_count": len(indices_in_texts),
                    "demand_score": min(1.0, len(indices_in_texts) / max(10, len(texts) // 5)),
                    "_doc_indices": doc_indices,
                })
            return clusters
        except Exception as e:
            print(f"Clustering error: {e}")
            return []
