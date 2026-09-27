from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService

class AIChatAgent:
    def __init__(self):
        self.embedding = EmbeddingService()
        self.llm = LLMService()

    def answer(self, question: str) -> dict:
        context_docs = []
        try:
            if self.embedding.count() > 0:
                results = self.embedding.search(question, n_results=5)
                context_docs = results.get("documents", [[]])[0]
        except Exception as e:
            print(f"Vector search error: {e}")
        context = "\n\n".join(context_docs) if context_docs else ""
        response = self.llm.generate(question, context)
        return {"response": response, "sources": context_docs}
