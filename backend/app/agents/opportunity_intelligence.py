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
        "demand": 0.18,
        "research_gap": 0.15,
        "trend": 0.12,
        "innovation": 0.07,
        "competition": 0.07,
        "feasibility": 0.12,
        "market_readiness": 0.08,
        "confidence": 0.05,
        # ---- Phase 10.3: SRS 21 completion ----
        "technology_suitability": 0.06,
        "evidence_strength": 0.06,
        "recency": 0.04,
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

    def _item_text(self, item: dict) -> str:
        """Concatenate every text-bearing field on a raw item, lowercased."""
        parts = [
            item.get("title") or "",
            item.get("name") or "",
            item.get("description") or "",
            item.get("summary") or "",
            item.get("selftext") or "",
        ]
        return " ".join(p for p in parts if p).lower()

    def _derive_innovation_score(self, keywords: list, raw_items: dict) -> float:
        """
        Novelty/diversity of the signal around *this* cluster.

        - diversity (0.5): how many of the 4 sources have docs matching this cluster
        - balance   (0.3): 1 - dominant_source_share  (penalizes single-source clusters)
        - breadth   (0.2): min(1, len(keywords) / 8)

        Ranges from 0.15 (only one source touches the topic) to ~0.93 (evenly spread).
        """
        if not keywords or not raw_items:
            return 0.3

        keywords_lower = [str(k).lower() for k in keywords if k]
        if not keywords_lower:
            return 0.3

        source_matches = {}
        for src in ("github", "arxiv", "news", "reddit"):
            items = raw_items.get(src) or []
            count = 0
            for item in items:
                text = self._item_text(item)
                if any(kw in text for kw in keywords_lower):
                    count += 1
            if count > 0:
                source_matches[src] = count

        if not source_matches:
            return 0.15

        diversity = len(source_matches) / 4.0
        total = sum(source_matches.values())
        max_share = max(source_matches.values()) / total
        balance = 1.0 - max_share
        breadth = min(1.0, len(keywords) / 8.0)

        score = 0.5 * diversity + 0.3 * balance + 0.2 * breadth
        return round(score, 3)

    # ---------- Phase 10.3: SRS 21 new factors ----------
    def _derive_technology_suitability_score(
        self, profile_techs: list, cluster_techs: list
    ) -> float:
        """Suitability = how real/actionable the technologies tied to this opp are.

        Inputs:
          profile_techs: list of dicts {name, stage, confidence} from
                         problem_technologies for the matched profile
          cluster_techs: list of tech names from the KG Technology nodes
                         linked to the cluster (fallback signal)

        Stages (SRS 12): used > proposed > emerging > potentially_applicable.
        Weighted mean of stage scores times avg confidence. Falls back to
        the cluster techs count if profile techs are empty.
        """
        stage_vals = {
            "used": 1.0,
            "proposed": 0.8,
            "emerging": 0.6,
            "potentially_applicable": 0.3,
        }
        if profile_techs:
            total = 0.0
            n = 0
            for t in profile_techs:
                stage = str(t.get("stage") or "potentially_applicable").lower()
                conf = float(t.get("confidence") or 0.5)
                total += stage_vals.get(stage, 0.3) * (0.5 + 0.5 * conf)
                n += 1
            score = total / max(n, 1)
            return round(max(0.2, min(1.0, score)), 3)
        if cluster_techs:
            score = min(1.0, len(cluster_techs) / 8.0)
            return round(0.4 + 0.4 * score, 3)
        return 0.2

    def _derive_evidence_strength_score(self, evidence_count: int) -> float:
        """Log-scale from evidence row count (SRS 21): 0 -> 0.2, 5+ -> 1.0."""
        import math
        n = max(0, int(evidence_count))
        score = 0.2 + 0.8 * (math.log1p(n) / math.log1p(8))
        return round(min(1.0, score), 3)

    def _derive_recency_score(self, created_at) -> float:
        """Freshness of the opportunity (SRS 21): today -> 1.0, 30d -> 0.4, 90d+ -> 0.2."""
        if created_at is None:
            return 0.5
        try:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            ts = created_at
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            days = max(0.0, (now - ts).total_seconds() / 86400.0)
            if days <= 1:
                return 1.0
            if days <= 7:
                return 0.9
            if days <= 30:
                return 0.4 + 0.5 * (1 - (days - 1) / 29)
            if days <= 90:
                return 0.2 + 0.2 * (1 - (days - 30) / 60)
            return 0.2
        except Exception:
            return 0.5

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
              github_items: list = None, arxiv_items: list = None, news_items: list = None,
              raw_items: dict = None, avg_sentiment: float = None,
              profile_techs: list = None, cluster_techs: list = None,
              evidence_count: int = 0, created_at=None) -> dict:
        demand = problem_cluster.get("demand_score", 0.5)
        gap = research_gap.get("gap_score", 0.5) if research_gap else 0.5
        trend_score = trend.get("trend_score", 0.5) if trend else 0.5
        keywords = problem_cluster.get("keywords", [])
        competition = self._derive_competition_score(keywords, github_items or [])
        feasibility = self._derive_feasibility_score(keywords, github_items or [], arxiv_items or [])

        # Market readiness: base score from news coverage, then modulated by
        # aggregate sentiment. avg_sentiment ∈ [-1, 1] (VADER compound).
        # Positive buzz → readiness amplified up to +15%. Negative → dampened
        # to −15%. Clamped to [0, 1] after modulation.
        market_readiness_raw = self._derive_market_readiness_score(keywords, news_items or [])
        if avg_sentiment is not None:
            modifier = 1.0 + 0.15 * max(-1.0, min(1.0, float(avg_sentiment)))
            market_readiness = max(0.0, min(1.0, market_readiness_raw * modifier))
        else:
            market_readiness = market_readiness_raw

        innovation = self._derive_innovation_score(keywords, raw_items or {})
        confidence = 0.8

        # ---- Phase 10.3: SRS 21 new factors ----
        technology_suitability = self._derive_technology_suitability_score(
            profile_techs or [], cluster_techs or []
        )
        evidence_strength = self._derive_evidence_strength_score(evidence_count or 0)
        recency = self._derive_recency_score(created_at)

        opportunity_score = (
            self.WEIGHTS["demand"] * demand +
            self.WEIGHTS["research_gap"] * gap +
            self.WEIGHTS["trend"] * trend_score +
            self.WEIGHTS["innovation"] * innovation +
            self.WEIGHTS["competition"] * (1 - competition) +
            self.WEIGHTS["feasibility"] * feasibility +
            self.WEIGHTS["market_readiness"] * market_readiness +
            self.WEIGHTS["confidence"] * confidence +
            self.WEIGHTS["technology_suitability"] * technology_suitability +
            self.WEIGHTS["evidence_strength"] * evidence_strength +
            self.WEIGHTS["recency"] * recency
        )

        title = self._generate_title(problem_cluster, research_gap)
        description = self._generate_description(problem_cluster, research_gap)

        raw_title = problem_cluster.get("title", "")
        if raw_title and _is_latin_only(raw_title):
            description += f" Source cluster: {raw_title[:120]}"

        return {
            "title": title,
            "description": description,
            "demand_score": round(demand, 3),
            "research_gap_score": round(gap, 3),
            "trend_score": round(trend_score, 3),
            "innovation_score": innovation,
            "competition_score": competition,
            "feasibility_score": feasibility,
            "market_readiness_score": market_readiness,
            "confidence_score": confidence,
            "technology_suitability_score": technology_suitability,
            "evidence_strength_score": evidence_strength,
            "recency_score": recency,
            "opportunity_score": round(opportunity_score, 3),
        }
