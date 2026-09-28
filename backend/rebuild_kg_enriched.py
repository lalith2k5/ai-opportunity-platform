"""One-shot: rebuild enriched KG edges from Phase 2/3/4 tables.

Deletes ONLY the enriched-graph-only relations (those produced by
KnowledgeGraphAgent.build_enriched_graph), then rebuilds them.
Semantic-graph relations (HAS_KEYWORD, SOLVES, MENTIONS, ...) are
left untouched. RELATED_TO is co-produced by both graphs, so we
do NOT delete it -- that would wipe semantic-layer edges too.

Idempotent. No LLM. Pure DB + in-memory graph rebuild.

Usage (from backend/, venv active):
    python3 rebuild_kg_enriched.py
"""
from sqlalchemy import text

from app.database import SessionLocal, engine
from app import models
from app.agents.knowledge_graph import KnowledgeGraphAgent


ENRICHED_ONLY_RELATIONS = [
    "STUDIED_BY",
    "REPORTED_BY",
    "FOUND_IN",
    "HAS_LIMITATION",
    "HAS_POTENTIAL_GAP",
    "SUPPORTED_BY",
    "USES",
    "HAS_TREND",
]


def main():
    print("[rebuild_kg] deleting enriched-graph-only relations")
    with engine.begin() as conn:
        for rel in ENRICHED_ONLY_RELATIONS:
            n = conn.execute(text(
                "DELETE FROM kg_edges WHERE relation = :rel"
            ), {"rel": rel}).rowcount
            print(f"  {rel:<22} {n} rows deleted")

    print("[rebuild_kg] rebuilding enriched graph from Phase 2/3/4 tables")
    kg = KnowledgeGraphAgent()
    stats = kg.build_enriched_graph()
    persist = kg.persist()
    print(f"[rebuild_kg] graph size in memory: {stats}")
    print(f"[rebuild_kg] persisted to DB:      {persist}")

    db = SessionLocal()
    try:
        print("[rebuild_kg] final relation counts:")
        for rel in ENRICHED_ONLY_RELATIONS:
            n = db.query(models.KnowledgeGraphEdge).filter(
                models.KnowledgeGraphEdge.relation == rel
            ).count()
            print(f"  {rel:<22} {n}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
