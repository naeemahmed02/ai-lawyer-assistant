from documents.services.embeddings.embedding_engine import EmbeddingEngine
from documents.services.vectorstore.qdrant_service import QdrantService
from ..llm.service import LLMService
from ..llm.builders.prompt_builder import PromptBuilder


class RAGPipeline:
    def __init__(self):
        self.embeddings = EmbeddingEngine()

        self.qdrant_service = QdrantService()

        # self.context_builder = ContextBuilder()

        self.prompt_builder = PromptBuilder()

        self.llm_service = LLMService()

        # self.citation_builder = self.CitationBuilder()

    def run(self, query: str, case_id: str = None):

        # embed user query
        query_vector = self.embeddings.embed(query)

        # Retrieve relevent chunks
        results = self.qdrant_service.search_with_filter(
            query_vector=query_vector, case_id=case_id, limit=5
        )

        # Build prompt
        prompt = self.prompt_builder.build(
            system_prompt="You are a helpful assistant.",
            user_message=query,
            history=None,
        )

        # generate respose
        answer = self.llm_service.generate(
            messages=prompt, model_name="gemini-2.5-flash"
        )
