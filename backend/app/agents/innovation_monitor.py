from collections import Counter

class InnovationMonitorAgent:
    def monitor(self, documents: list) -> list:
        keyword_counter = Counter()
        source_counter = Counter()
        for doc in documents:
            for kw in (doc.get("keywords") or []):
                keyword_counter[kw.lower()] += 1
            source_counter[doc.get("source", "unknown")] += 1
        trends = []
        for keyword, count in keyword_counter.most_common(10):
            trends.append({
                "name": keyword,
                "category": "emerging_technology",
                "trend_score": min(1.0, count / 10.0),
                "source_data": {"mentions": count, "sources": dict(source_counter)}
            })
        return trends
