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

    def merge_provenance(self, existing_row, new_profile: dict) -> bool:
        """Cross-source merge: append new provenance to an existing row.

        Called when a new profile matches an existing DB row by canonical_hash
        or source_url. Records where else this same problem was seen, unions
        keywords and required_technology. Returns True if anything changed.
        """
        new_source = (new_profile.get("source") or "").strip()
        new_url = (new_profile.get("source_url") or "").strip()
        new_org = (new_profile.get("organization") or "").strip()[:500]

        # No-op if the new profile is the row's own primary source
        if new_source == (existing_row.source or "") and new_url == (existing_row.source_url or ""):
            return False

        current = existing_row.additional_sources or []
        if not isinstance(current, list):
            current = []

        for entry in current:
            if (isinstance(entry, dict)
                    and entry.get("source") == new_source
                    and entry.get("source_url") == new_url):
                return False

        current = list(current)
        current.append({
            "source": new_source,
            "source_url": new_url,
            "organization": new_org,
        })
        existing_row.additional_sources = current

        # Union keywords
        if isinstance(new_profile.get("keywords"), list):
            seen_kw = set()
            merged_kw = []
            for kw in list(existing_row.keywords or []) + list(new_profile["keywords"]):
                if kw and kw not in seen_kw:
                    seen_kw.add(kw)
                    merged_kw.append(kw)
            existing_row.keywords = merged_kw

        # Union required_technology
        if isinstance(new_profile.get("required_technology"), list):
            seen_tech = set()
            merged_tech = []
            for t in list(existing_row.required_technology or []) + list(new_profile["required_technology"]):
                if t and t not in seen_tech:
                    seen_tech.add(t)
                    merged_tech.append(t)
            existing_row.required_technology = merged_tech

        return True
