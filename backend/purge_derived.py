"""Purge all pipeline-derived data so we can start with a clean slate.

Keeps: users, raw_documents, refresh_tokens, password_reset_tokens, agent_logs.
Wipes: problem_clusters, research_gaps, opportunities, trends, trend_snapshots,
       notifications, processed_documents, search_history, chat_sessions,
       chat_messages, kg_nodes, kg_edges.
"""
from app.database import SessionLocal
from app import models
from app.services.embedding_service import EmbeddingService


def main():
    db = SessionLocal()
    try:
        counts = {}
        for model in [
            models.ChatMessage, models.ChatSession,
            models.SearchHistory,
            models.Notification,
            models.KnowledgeGraphEdge, models.KnowledgeGraphNode,
            models.TrendSnapshot, models.Trend,
            models.Opportunity, models.ResearchGap, models.ProblemCluster,
            models.ProcessedDocument,
        ]:
            n = db.query(model).delete(synchronize_session=False)
            counts[model.__tablename__] = n
        db.commit()
        for k, v in counts.items():
            print(f"  wiped {v:>5} rows from {k}")
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()

    # Also wipe the vector store
    try:
        emb = EmbeddingService()
        existing = emb.collection.get()
        ids = existing.get("ids", [])
        if ids:
            emb.collection.delete(ids=ids)
            print(f"  wiped {len(ids)} vectors from Chroma")
        else:
            print("  vector store was already empty")
    except Exception as e:
        print(f"  Chroma wipe skipped: {e}")


if __name__ == "__main__":
    main()
