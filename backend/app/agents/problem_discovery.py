from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np


class ProblemDiscoveryAgent:
    """TF-IDF + KMeans. Cluster count scales with document volume."""

    MIN_CLUSTERS = 5
    MAX_CLUSTERS = 30

    def discover(self, documents: list, n_clusters: int = None) -> list:
        texts = [
            (d.get("title", "") + " " + (d.get("content", "") or "")[:500])
            for d in documents if d.get("title")
        ]
        if len(texts) < 2:
            return []

        if n_clusters is None:
            # ~1 cluster per 8 docs, clamped between min and max
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
                indices = np.where(labels == i)[0]
                if len(indices) == 0:
                    continue
                center = kmeans.cluster_centers_[i]
                top_keywords = [feature_names[j] for j in center.argsort()[-8:][::-1]]
                clusters.append({
                    "title": f"Problem Cluster: {', '.join(top_keywords[:3])}",
                    "description": f"Recurring issues related to: {', '.join(top_keywords)}",
                    "keywords": top_keywords,
                    "source_count": len(indices),
                    "demand_score": min(1.0, len(indices) / max(10, len(texts) // 5)),
                })
            return clusters
        except Exception as e:
            print(f"Clustering error: {e}")
            return []
