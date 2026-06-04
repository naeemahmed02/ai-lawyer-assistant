import logging
from typing import Optional, List

from documents.services.vectorstore.qdrant_service import QdrantService
from documents.services.embeddings.embedding_engine import EmbeddingEngine

from ..llm.service import LLMService
from ..llm.builders.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Production-ready Legal RAG Pipeline.

    Flow:
    User Query
        ↓
    Gemini Embedding
        ↓
    Qdrant Retrieval
        ↓
    Context Construction
        ↓
    Prompt Building
        ↓
    Gemini Generation
    """

    def __init__(self):
        self.embedding_engine = EmbeddingEngine(
            model_name="gemini-embedding-001",
            output_dimensionality=3072,
        )

        self.qdrant_service = QdrantService(
            vector_size=3072,
        )

        self.prompt_builder = PromptBuilder()

        self.llm_service = LLMService()

    # --------------------------------------------------
    # Context Builder
    # --------------------------------------------------

    def _build_context(self, search_results) -> str:
        """
        Convert Qdrant results into prompt context.
        """

        if not search_results:
            return ""

        chunks: List[str] = []

        for point in search_results:

            payload = point.payload or {}

            text = payload.get("text")

            if text:
                chunks.append(text)

        return "\n\n".join(chunks)

    # --------------------------------------------------
    # Main RAG Entry
    # --------------------------------------------------

    def run(
        self,
        query: str,
        case_id: Optional[str] = None,
    ) -> dict:

        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        logger.info(
            "Running RAG pipeline. case_id=%s",
            case_id,
        )

        try:
            # ------------------------------------------
            # Embed Query
            # ------------------------------------------

            query_vector = self.embedding_engine.embed(
                query
            )

            logger.debug(
                "Generated query embedding (%s dimensions)",
                len(query_vector),
            )

            # ------------------------------------------
            # Retrieve Relevant Chunks
            # ------------------------------------------

            search_results = (
                self.qdrant_service.search_with_filter(
                    query_vector=query_vector,
                    case_id=case_id,
                    limit=5,
                )
            )

            logger.info(
                "Retrieved %s chunks",
                len(search_results),
            )

            # ------------------------------------------
            # Build Context
            # ------------------------------------------

            context = self._build_context(
                search_results
            )

            # ------------------------------------------
            # Build Prompt
            # ------------------------------------------

            system_prompt = """
You are a legal AI assistant.

Answer the user's question using ONLY the provided legal context.

If the answer is not contained in the context,
say that the information is unavailable.

Be precise and cite relevant facts from the context.
"""

            user_message = f"""
Context:

{context}

Question:

{query}
"""

            prompt = self.prompt_builder.build(
                system_prompt=system_prompt,
                user_message=user_message,
                history=None,
            )

            # ------------------------------------------
            # Generate Answer
            # ------------------------------------------

            answer = self.llm_service.generate(
                messages=prompt,
                model_name="gemini-2.5-flash",
            )

            # ------------------------------------------
            # Return Structured Result
            # ------------------------------------------

            return {
                "query": query,
                "answer": answer,
                "retrieved_chunks": len(search_results),
            }

        except Exception:
            logger.exception(
                "RAG pipeline execution failed."
            )
            raise