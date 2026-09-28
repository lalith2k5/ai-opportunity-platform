"""Delete pd:<id> style vectors from Chroma (left over from earlier reembed).

After Phase 10.10 the reembed uses raw:<id> IDs. Older pd:<id> entries
still exist and cause duplicate search hits for the same document.
Idempotent. No LLM.

Usage: python3 cleanup_chroma_dups.py
"""
from app.services.embedding_service import EmbeddingService


def main():
    emb = EmbeddingService()
    before = emb.count()
    print(f"[chroma-clean] before: {before} vectors")

    # Get all IDs, delete those starting with "pd:"
    try:
        data = emb.collection.get()
        all_ids = data.get("ids", [])
    except Exception as e:
        print(f"[chroma-clean] get failed: {e}")
        return

    pd_ids = [i for i in all_ids if i.startswith("pd:")]
    print(f"[chroma-clean] found {len(pd_ids)} stale 'pd:' ids")

    if not pd_ids:
        print("[chroma-clean] nothing to delete")
        return

    # Delete in batches of 500
    BATCH = 500
    deleted = 0
    for i in range(0, len(pd_ids), BATCH):
        chunk = pd_ids[i:i+BATCH]
        try:
            emb.collection.delete(ids=chunk)
            deleted += len(chunk)
            print(f"[chroma-clean] deleted {deleted}/{len(pd_ids)}")
        except Exception as e:
            print(f"[chroma-clean] batch failed: {e}")

    after = emb.count()
    print(f"[chroma-clean] after: {after} vectors (was {before})")


if __name__ == "__main__":
    main()
