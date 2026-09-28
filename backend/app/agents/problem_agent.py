"""ProblemAgent — dedup + canonicalization for structured problem profiles.

Canonicalizes problem_title to a stable hash so profiles describing the
same underlying problem (differing only in punctuation, word order, or
stopwords) collapse to the same key.

Design goals:
  - Deterministic: same input -> same hash, always.
  - Conservative: prefers false negatives (miss a dup) over false positives
    (merge two genuinely different problems).
  - No LLM calls: pure CPU, safe to run inside the save path.
"""
import hashlib
import re


# Short function words. Dropped before hashing so "the memory leak" and
# "memory leak" produce identical canonical forms. Kept deliberately small —
# dropping too many words risks collapsing distinct problems.
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "have", "in", "is", "it", "its", "of", "on", "or", "that",
    "the", "this", "to", "via", "was", "were", "will", "with",
    "using", "based", "into", "onto", "over", "under",
}

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class ProblemAgent:
    """Canonicalization + dedup wrapper for problem profiles."""

    @staticmethod
    def canonicalize(title: str) -> str:
        """Lowercase, tokenize, drop stopwords, sort tokens, join."""
        if not title:
            return ""
        low = title.lower()
        tokens = _TOKEN_RE.findall(low)
        filtered = [t for t in tokens if t and t not in _STOPWORDS]
        if not filtered:
            # If stopword removal stripped everything, fall back to raw tokens.
            # Hash is still deterministic for the same input.
            filtered = tokens
        filtered.sort()
        return " ".join(filtered)

    @classmethod
    def compute_hash(cls, title: str) -> str:
        """16-char hex hash of the canonical form. Empty string if title is blank."""
        canonical = cls.canonicalize(title)
        if not canonical:
            return ""
        return hashlib.sha1(canonical.encode("utf-8")).hexdigest()[:16]

    def dedup(self, profiles: list) -> list:
        """Intra-batch dedup: keep first occurrence per canonical hash.

        Profiles without a computable hash are passed through unchanged
        (we would rather store an unhashable row than silently drop it).
        Adds a private '_canonical_hash' key to each kept profile.
        """
        seen = set()
        out = []
        for p in profiles:
            h = self.compute_hash(p.get("problem_title") or "")
            if not h:
                out.append(p)
                continue
            if h in seen:
                continue
            seen.add(h)
            p["_canonical_hash"] = h
            out.append(p)
        return out
