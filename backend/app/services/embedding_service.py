import chromadb
from sentence_transformers import SentenceTransformer
from app.config import settings
import uuid

class EmbeddingService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        print("Loading embedding model (first run may take a minute)...")
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        self.collection = self.client.get_or_create_collection(name="documents")
        print("Embedding service ready")

    def add_documents(self, documents: list, metadatas: list = None, ids: list = None):
        if not documents:
            return []
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
        if metadatas is None:
            metadatas = [{"source": "unknown"} for _ in documents]
        embeddings = self.model.encode(documents).tolist()
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        return ids

    def search(self, query: str, n_results: int = 5):
        query_embedding = self.model.encode([query]).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )
        return results

    def count(self):
        return self.collection.count()
