import re

_LATIN_ONLY = re.compile(r'^[a-zA-Z0-9\s\-&,.\']+$')


def _is_latin_only(s: str) -> bool:
    return bool(s and _LATIN_ONLY.match(s))


# Additional noise words (things that show up in titles but aren't meaningful)
NOISE_WORDS = {
    "awesome", "papers", "paper", "need", "needs", "needed", "needing",
    "repository", "repositories", "repo", "repos", "projects", "project",
    "github", "list", "lists", "curated", "collection", "collections",
    "code", "source", "open", "software", "library", "libraries",
    "problem", "problems", "cluster", "clusters", "issue", "issues",
    "topic", "topics", "related", "general", "based", "using", "used",
    "new", "good", "great", "best", "better", "well", "like", "make",
    "getting", "started", "guide", "tutorial", "tutorials", "book", "books",
    "research", "study", "studies", "review", "reviews", "example",
    "examples", "data", "dataset", "datasets", "framework", "frameworks",
    "system", "systems", "tool", "tools", "app", "apps", "application",
    "applications", "web", "mobile", "cloud", "github.io", "https",
    "readme", "documentation", "docs", "star", "stars", "fork", "forks",
    "contribution", "contributions", "pull", "request", "python",
    "javascript", "typescript", "java", "golang", "rust", "node",
    "react", "vue", "angular", "django", "flask", "fastapi",
    "model", "models", "approach", "approaches", "method", "methods",
    "methodology", "results", "result", "findings", "finding",
    "analysis", "analyses", "training", "test", "testing",
    "version", "type", "types", "case", "cases", "work", "works",
    "publication", "publications", "article", "articles",
    "information", "knowledge", "process", "processes", "task", "tasks",
    "solution", "solutions", "feature", "features",
    "value", "values", "level", "levels", "high", "low", "large",
    "small", "old", "recent", "current", "future", "called", "call",
    "coin", "w3c", "2019", "2020", "2021", "2022", "2023", "2024",
    "january", "february", "march", "april", "may", "june", "july",
    "august", "september", "october", "november", "december",
    "shannon", "videos", "video", "resources", "resource", "blog",
    "series", "chapter", "chapters", "part", "parts", "introduction",
    "overview", "summary", "note", "notes", "week", "month", "year",
    "page", "pages", "posts", "post", "thread", "comment", "comments",
    "discussion", "discussions", "question", "questions", "answer",
    "answers", "here", "there", "this", "that", "these", "those",
    "first", "second", "third", "next", "last", "also", "even", "still",
    "just", "only", "much", "many", "more", "most", "some", "other",
}

BRAND_NAMES = {
    "azure", "aws", "gcp", "google", "microsoft", "amazon", "apple",
    "facebook", "meta", "twitter", "linkedin", "oracle", "ibm",
    "tesla", "nvidia", "intel", "amd", "docker", "kubernetes",
    "tensorflow", "pytorch", "keras", "opencv", "matlab", "jupyter",
    "thingsboard", "classiq",
}

# Known multi-word phrases to merge (single + single → bigram)
PHRASE_MERGES = {
    ("machine", "learning"): "machine learning",
    ("deep", "learning"): "deep learning",
    ("artificial", "intelligence"): "artificial intelligence",
    ("quantum", "computing"): "quantum computing",
    ("edge", "computing"): "edge computing",
    ("cloud", "computing"): "cloud computing",
    ("neural", "network"): "neural network",
    ("neural", "networks"): "neural networks",
    ("computer", "vision"): "computer vision",
    ("natural", "language"): "natural language",
    ("language", "processing"): "language processing",
    ("reinforcement", "learning"): "reinforcement learning",
    ("federated", "learning"): "federated learning",
    ("transfer", "learning"): "transfer learning",
    ("image", "segmentation"): "image segmentation",
    ("image", "classification"): "image classification",
    ("image", "processing"): "image processing",
    ("medical", "imaging"): "medical imaging",
    ("intrusion", "detection"): "intrusion detection",
    ("anomaly", "detection"): "anomaly detection",
    ("object", "detection"): "object detection",
    ("cyber", "security"): "cyber security",
    ("data", "science"): "data science",
    ("big", "data"): "big data",
    ("block", "chain"): "blockchain",
    ("supply", "chain"): "supply chain",
    ("public", "health"): "public health",
    ("reverse", "engineering"): "reverse engineering",
    ("generative", "ai"): "generative AI",
    ("large", "language"): "large language",
    ("explainable", "ai"): "explainable AI",
}

ACRONYMS = {
    "ai", "ml", "iot", "llm", "nlp", "rag", "api", "ui", "ux",
    "db", "sql", "aws", "gcp", "cnn", "rnn", "lstm", "gan", "vae",
    "knn", "svm", "gpt", "bert", "xai", "ar", "vr",
}


def _title_case(s: str) -> str:
    parts = []
    for word in s.split():
        if word.lower() in ACRONYMS:
            parts.append(word.upper())
        else:
            parts.append(word.capitalize())
    return " ".join(parts)


def _singularize(word: str) -> str:
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 3 and word.endswith("es") and word[-3] not in "aeiou":
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _is_meaningful(token: str) -> bool:
    """A token is meaningful if it's not noise/brand/short/numeric."""
    if len(token) < 3:
        return False
    if token.isdigit():
        return False
    if token in NOISE_WORDS or token in BRAND_NAMES:
        return False
    return True


def _clean_keywords(keywords: list) -> dict:
    """
    1. Extract clean tokens.
    2. Merge known bigrams (machine learning → 'machine learning').
    3. Return phrases + singles.
    """
    # Step 1: clean individual keywords into tokens
    cleaned_singles = []
    seen_singles = set()

    for kw in keywords:
        if not kw:
            continue
        if not _is_latin_only(kw):
            continue
        w = kw.lower().strip()
        if " " in w:
            # Multi-word from TF-IDF: keep if all tokens meaningful
            tokens = w.split()
            if all(_is_meaningful(t) for t in tokens):
                root = " ".join(_singularize(t) for t in tokens)
                if root not in seen_singles:
                    seen_singles.add(root)
                    cleaned_singles.append(w)
            continue

        # Single word
        if not _is_meaningful(w):
            continue
        root = _singularize(w)
        if root in seen_singles:
            continue
        seen_singles.add(root)
        cleaned_singles.append(w)

    # Step 2: merge known bigram pairs found in singles
    merged_phrases = []
    consumed = set()
    for i, w1 in enumerate(cleaned_singles):
        if i in consumed:
            continue
        for j, w2 in enumerate(cleaned_singles):
            if j <= i or j in consumed:
                continue
            key1 = (_singularize(w1), _singularize(w2))
            key2 = (_singularize(w2), _singularize(w1))
            if key1 in PHRASE_MERGES:
                merged_phrases.append(PHRASE_MERGES[key1])
                consumed.add(i)
                consumed.add(j)
                break
            elif key2 in PHRASE_MERGES:
                merged_phrases.append(PHRASE_MERGES[key2])
                consumed.add(i)
                consumed.add(j)
                break

    # Remaining singles (not consumed) that aren't part of a merged phrase
    remaining = [w for i, w in enumerate(cleaned_singles) if i not in consumed]
    # Also add any multi-word phrases that were already clean
    remaining = [w for w in remaining if " " in w] + [w for w in remaining if " " not in w]

    return {"phrases": merged_phrases, "singles": remaining}


class OpportunityIntelligenceAgent:
    WEIGHTS = {
        "demand": 0.25,
        "research_gap": 0.20,
        "trend": 0.15,
        "competition": 0.10,
        "feasibility": 0.15,
        "market_readiness": 0.10,
        "confidence": 0.05,
    }

    def _generate_title(self, cluster: dict, gap: dict = None) -> str:
        kw = _clean_keywords(cluster.get("keywords", []))
        phrases = kw["phrases"]
        singles = kw["singles"]

        # 1. Two phrases → "P1 for P2"
        if len(phrases) >= 2:
            return f"{_title_case(phrases[0])} for {_title_case(phrases[1])}"

        # 2. One phrase + one single → "Phrase for Single"
        if len(phrases) == 1 and len(singles) >= 1:
            return f"{_title_case(phrases[0])} for {_title_case(singles[0])}"

        # 3. One phrase only → "Phrase Innovation"
        if len(phrases) == 1:
            return f"{_title_case(phrases[0])} Innovations"

        # 4. Three or more singles → "S1, S2 & S3"
        if len(singles) >= 3:
            s1, s2, s3 = [_title_case(s) for s in singles[:3]]
            return f"{s1}, {s2} & {s3}"

        # 5. Two singles → "S1 & S2"
        if len(singles) == 2:
            return f"{_title_case(singles[0])} & {_title_case(singles[1])}"

        # 6. One single
        if len(singles) == 1:
            return f"{_title_case(singles[0])} Innovations"

        return "Emerging Innovation Opportunity"

    def _generate_description(self, cluster: dict, gap: dict = None) -> str:
        kw = _clean_keywords(cluster.get("keywords", []))
        all_kws = kw["phrases"] + kw["singles"]
        if not all_kws:
            return cluster.get("description", "Emerging opportunity.")

        focus = ", ".join(_title_case(k) for k in all_kws[:4])
        gap_note = ""
        if gap and gap.get("gap_score", 0) > 0.5:
            gap_note = " with significant research coverage gaps"
        return f"Opportunity focused on {focus}{gap_note}."


    def _derive_competition_score(self, keywords: list, github_items: list) -> float:
        """More matching repos → more competition → HIGHER score (harder)."""
        if not keywords or not github_items:
            return 0.3
        text = " ".join([
            (r.get("name", "") + " " + (r.get("description", "") or "")).lower()
            for r in github_items
        ])
        matches = sum(1 for kw in keywords if kw.lower() in text)
        density = matches / max(len(keywords), 1)
        return round(min(1.0, 0.2 + density * 0.8), 3)

    def _derive_feasibility_score(self, keywords: list, github_items: list, arxiv_items: list) -> float:
        """Repo stars + paper count → higher technical feasibility."""
        stars = sum(r.get("stargazers_count", 0) or 0 for r in (github_items or []))
        papers = len(arxiv_items or [])
        # Normalize: 20k stars + 10 papers → max feasibility
        star_component = min(1.0, stars / 20000.0)
        paper_component = min(1.0, papers / 10.0)
        return round(0.3 + 0.5 * star_component + 0.2 * paper_component, 3)

    def _derive_market_readiness_score(self, keywords: list, news_items: list) -> float:
        """More news coverage → higher market readiness."""
        if not keywords or not news_items:
            return 0.4
        text = " ".join([
            (n.get("title", "") + " " + (n.get("summary", ""))).lower()
            for n in news_items
        ])
        matches = sum(1 for kw in keywords if kw.lower() in text)
        density = matches / max(len(keywords), 1)
        return round(min(1.0, 0.3 + density * 0.7), 3)

    def score(self, problem_cluster: dict, research_gap: dict = None, trend: dict = None,
              github_items: list = None, arxiv_items: list = None, news_items: list = None) -> dict:
        demand = problem_cluster.get("demand_score", 0.5)
        gap = research_gap.get("gap_score", 0.5) if research_gap else 0.5
        trend_score = trend.get("trend_score", 0.5) if trend else 0.5
        keywords = problem_cluster.get("keywords", [])
        competition = self._derive_competition_score(keywords, github_items or [])
        feasibility = self._derive_feasibility_score(keywords, github_items or [], arxiv_items or [])
        market_readiness = self._derive_market_readiness_score(keywords, news_items or [])
        confidence = 0.8

        opportunity_score = (
            self.WEIGHTS["demand"] * demand +
            self.WEIGHTS["research_gap"] * gap +
            self.WEIGHTS["trend"] * trend_score +
            self.WEIGHTS["competition"] * (1 - competition) +
            self.WEIGHTS["feasibility"] * feasibility +
            self.WEIGHTS["market_readiness"] * market_readiness +
            self.WEIGHTS["confidence"] * confidence
        )

        title = self._generate_title(problem_cluster, research_gap)
        description = self._generate_description(problem_cluster, research_gap)

        raw_title = problem_cluster.get("title", "")
        if raw_title:
            description += f" Source cluster: {raw_title[:120]}"

        return {
            "title": title,
            "description": description,
            "demand_score": round(demand, 3),
            "research_gap_score": round(gap, 3),
            "trend_score": round(trend_score, 3),
            "competition_score": competition,
            "feasibility_score": feasibility,
            "market_readiness_score": market_readiness,
            "confidence_score": confidence,
            "opportunity_score": round(opportunity_score, 3),
        }
