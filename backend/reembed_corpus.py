"""One-shot: embed all processed_documents into Chroma.

Idempotent -- uses deterministic IDs (pd:<id>) so re-runs overwrite
instead of duplicating. Uses the local SentenceTransformer only.
No LLM, no quota.

Usage (from backend/, venv active):
    python3 reembed_corpus.py            # all docs
    python3 reembed_corpus.py 500        # cap at 500
"""
import sys

from app.database import SessionLocal
from app import models
from app.services.embedding_service import EmbeddingService


BATCH = 64


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 100000
    emb = EmbeddingService()
    db = SessionLocal()
    try:
        total = db.query(models.ProcessedDocument).count()
        print(f"[reembed] DB has {total} processed_documents (cap={limit})")
        print(f"[reembed] chroma currently has {emb.count()} vectors")

        rows = (
            db.query(models.ProcessedDocument)
            .order_by(models.ProcessedDocument.id)
            .limit(limit)
            .all()
        )
        print(f"[reembed] embedding {len(rows)} rows in batches of {BATCH}")

        raw_ids = [r.raw_document_id for r in rows if r.raw_document_id]
        raw_map = {}
        if raw_ids:
            for rd in db.query(models.RawDocument).filter(
                models.RawDocument.id.in_(raw_ids)
            ).all():
                raw_map[rd.id] = rd

        done = 0
        for i in range(0, len(rows), BATCH):
            chunk = rows[i:i+BATCH]
            texts, ids, metas = [], [], []
            for r in chunk:
                rd = raw_map.get(r.raw_document_id)
                title = (rd.title if rd else "") or ""
                source = (rd.source if rd else "") or "unknown"
                text = (title + " " + (r.cleaned_text or ""))[:1000]
                if not text.strip():
                    continue
                texts.append(text)
                ids.append(f"pd:{r.id}")
                metas.append({"source": source, "processed_document_id": r.id})
            if not texts:
                continue
            try:
                vecs = emb.model.encode(texts, batch_size=32).tolist()
                emb.collection.upsert(
                    documents=texts,
                    embeddings=vecs,
                    metadatas=metas,
                    ids=ids,
                )
                done += len(texts)
                print(f"[reembed] batch {i//BATCH + 1}: +{len(texts)}  (total {done})")
            except Exception as e:
                print(f"[reembed] batch {i//BATCH + 1} FAILED: {e}")

        print(f"[reembed] done. embedded/updated {done} docs.")
        print(f"[reembed] chroma now has {emb.count()} vectors")
    finally:
        db.close()


if __name__ == "__main__":
    main()
