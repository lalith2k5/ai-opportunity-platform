"""Knowledge Graph schema — canonical relation + node vocabulary.

Per SRS §31, the KG uses uppercase relations. This module is the single
source of truth for relation names and their legacy-to-canonical mapping.

Canonical (SRS §31, 10 relations — Reddit removed per user deferral):
    Problem      RELATED_TO         Technology
    Problem      STUDIED_BY         ResearchPaper
    Problem      REPORTED_BY        Organization
    Problem      FOUND_IN           Source
    Technology   HAS_TREND          Trend
    ResearchPaper HAS_LIMITATION    Limitation
    Problem      HAS_POTENTIAL_GAP  ResearchGap
    Opportunity  SUPPORTED_BY       Evidence
    Opportunity  USES               Technology
    Opportunity  ADDRESSES          Problem

Auxiliary relations (uppercase, not in spec §31 but present in the KG
for traversal / display):
    MENTIONS, HAS_KEYWORD, BELONGS_TO_TOPIC, AUTHORED_BY, STUDIES,
    WRITTEN_IN, SOLVES, PUBLISHED, INFORMS, TARGETS_INDUSTRY,
    RESEARCHES, HIGHLIGHTED_IN
"""

CANONICAL_RELATIONS = frozenset({
    "RELATED_TO",
    "STUDIED_BY",
    "REPORTED_BY",
    "FOUND_IN",
    "HAS_TREND",
    "HAS_LIMITATION",
    "HAS_POTENTIAL_GAP",
    "SUPPORTED_BY",
    "USES",
    "ADDRESSES",
})

# Legacy lowercase names → canonical uppercase. Used by _normalize_relation
# and by the migration that rewrites existing kg_edges rows.
LEGACY_RELATION_MAP = {
    "related_to":         "RELATED_TO",
    "studied_by":         "STUDIED_BY",
    "reported_by":        "REPORTED_BY",
    "found_in":           "FOUND_IN",
    "has_trend":          "HAS_TREND",
    "has_limitation":     "HAS_LIMITATION",
    "has_potential_gap":  "HAS_POTENTIAL_GAP",
    "supported_by":       "SUPPORTED_BY",
    "uses":               "USES",
    "addresses":          "ADDRESSES",

    # Auxiliary
    "mentions":           "MENTIONS",
    "has_keyword":        "HAS_KEYWORD",
    "belongs_to_topic":   "BELONGS_TO_TOPIC",
    "authored_by":        "AUTHORED_BY",
    "studies":            "STUDIES",
    "written_in":         "WRITTEN_IN",
    "solves":             "SOLVES",
    "published":          "PUBLISHED",
    "informed_by":        "INFORMS",
    "targets_industry":   "TARGETS_INDUSTRY",
    "researches":         "RESEARCHES",
    "highlighted_in":     "HIGHLIGHTED_IN",
}


def normalize_relation(relation: str) -> str:
    """Map any relation name (legacy or already-uppercase) to canonical form.

    Unknown relations are upper-cased and returned as-is, so no data is
    lost if new relations are added downstream without updating this map.
    """
    if not relation:
        return ""
    r = str(relation).strip()
    if not r:
        return ""
    low = r.lower()
    if low in LEGACY_RELATION_MAP:
        return LEGACY_RELATION_MAP[low]
    return r.upper()
