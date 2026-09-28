"""Embed ALL raw_documents into Chroma (D1 fix).

Sources from raw_documents (not processed_documents) so the vector store
covers the full corpus. Deterministic IDs (raw:<id>) so re-runs upsert.

Usage (from backend/, venv active):
    python3 reembed_corpus.py
    python3 reembed_corpus.py 500
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
        total = db.query(models.RawDocument).count()
        print(f"[reembed] DB has {total} raw_documents (cap={limit})", flush=True)
        print(f"[reembed] chroma currently has {emb.count()} vectors", flush=True)

        rows = (db.query(models.RawDocument)
                .order_by(models.RawDocument.id).limit(limit).all())
        print(f"[reembed] embedding {len(rows)} raw docs in batches of {BATCH}", flush=True)

        done = 0
        for i in range(0, len(rows), BATCH):
            chunk = rows[i:i+BATCH]
            texts, ids, metas = [], [], []
            for r in chunk:
                text = ((r.title or "")[:400] + " " + (r.content or "")[:1000]).strip()
                if not text:
                    continue
                texts.append(text)
                ids.append(f"raw:{r.id}")
                metas.append({
                    "source": (r.source or "unknown"),
                    "raw_document_id": r.id,
                    "url": (r.url or "")[:400],
                })
            if not texts:
                continue
            try:
                vecs = emb.model.encode(texts, batch_size=32).tolist()
                emb.collection.upsert(
                    documents=texts, embeddings=vecs,
                    metadatas=metas, ids=ids,
                )
                done += len(texts)
                print(f"[reembed] batch {i//BATCH + 1}: +{len(texts)} (total {done})", flush=True)
            except Exception as e:
                print(f"[reembed] batch {i//BATCH + 1} FAILED: {e}", flush=True)

        print(f"[reembed] done. embedded/updated {done} raw docs.", flush=True)
        print(f"[reembed] chroma now has {emb.count()} vectors", flush=True)
    finally:
        db.close()


if __name__ == "__main__":
    main()
