import re

class ResearchGapAgent:
    # Phrases that typically introduce future work or open problems
    FUTURE_WORK_PATTERNS = [
        r"future work (?:will|should|may|could|might|must|is|includes?|involves?)",
        r"future research (?:will|should|may|could|might|is|includes?|directions?)",
        r"remains? (?:an? )?open (?:problem|question|challenge|issue)",
        r"not (?:yet )?(?:been )?(?:addressed|explored|studied|solved)",
        r"open (?:problem|question|challenge|issue)",
        r"worth (?:investigating|exploring|studying)",
        r"calls? for further",
        r"promising (?:direction|avenue|future)",
        r"unexplored",
        r"needs? (?:to be )?(?:further )?(?:studied|explored|investigated|addressed)",
    ]

    def extract_future_work(self, text: str, max_snippets: int = 3) -> list:
        """Extract sentences mentioning future work / open problems."""
        if not text:
            return []
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        snippets = []
        for sent in sentences:
            lower = sent.lower()
            for pattern in self.FUTURE_WORK_PATTERNS:
                if re.search(pattern, lower):
                    clean = sent.strip()
                    if 20 < len(clean) < 400:
                        snippets.append(clean)
                    break
            if len(snippets) >= max_snippets:
                break
        return snippets

    def detect_gaps(self, problem_clusters: list, arxiv_papers: list) -> list:
        gaps = []
        paper_text = " ".join([(p.get("title", "") + " " + p.get("summary", "")).lower() for p in arxiv_papers])

        # Extract all future-work snippets from papers
        all_future_work = []
        for paper in arxiv_papers:
            fw = self.extract_future_work(paper.get("summary", ""), max_snippets=2)
            if fw:
                all_future_work.append({
                    "paper_title": paper.get("title", ""),
                    "snippets": fw,
                })

        for cluster in problem_clusters:
            keywords = cluster.get("keywords", [])
            if not keywords:
                continue
            matches = sum(1 for kw in keywords if kw.lower() in paper_text)
            coverage = matches / max(len(keywords), 1)
            gap_score = 1.0 - coverage

            # Find relevant future-work snippets for this cluster
            relevant_future_work = []
            for fw in all_future_work:
                for snippet in fw["snippets"]:
                    snippet_lower = snippet.lower()
                    if any(kw.lower() in snippet_lower for kw in keywords[:5]):
                        relevant_future_work.append({
                            "paper": fw["paper_title"],
                            "snippet": snippet,
                        })
                        break

            # Strip "Problem Cluster:" prefix and Chinese chars for cleaner titles
            raw_title = cluster.get("title", "Unknown")
            clean_title = raw_title.replace("Problem Cluster:", "").strip()
            import re as _re
            clean_title = _re.sub(r"[^\x00-\x7F]+", "", clean_title).strip()
            if not clean_title:
                clean_title = "Unknown Domain"

            gaps.append({
                "title": f"Research Gap: {clean_title}",
                "description": f"Limited research coverage ({coverage:.0%}) for problems related to: {', '.join(keywords[:5])}",
                "gap_score": round(gap_score, 2),
                "evidence": {
                    "coverage": coverage,
                    "keywords": keywords,
                    "future_work_snippets": relevant_future_work[:3],
                },
            })
        return gaps
