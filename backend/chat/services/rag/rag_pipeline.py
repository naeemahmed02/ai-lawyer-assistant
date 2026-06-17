import logging
from typing import Optional

from dataclasses import asdict

from documents.services.vectorstore.qdrant_service import QdrantService
from documents.services.embeddings.embedding_engine import EmbeddingEngine

from ..llm.service import LLMService
from ..llm.builders.prompt_builder import PromptBuilder

from .builders.context_builder import ContextBuilder
from .builders.citation_builder import CitationBuilder

from ..api_service.history_service import RecentHistoryService
from ...models.conversation_summary import ConversationSummary
from ..memory.semantic_memory_retrieval import MemoryRetriever

from .prompts.system_prompt import system_prompt
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Production-grade Legal RAG Pipeline.

    Responsibilities:
    - Query embedding
    - Semantic memory retrieval (pgvector)
    - Recent conversation retrieval
    - Conversation summary retrieval
    - Legal document retrieval (Qdrant)
    - Context assembly
    - Prompt construction
    - LLM inference
    - Citation generation
    """

    def __init__(self):
        self.embedding_engine = EmbeddingEngine(
            model_name="gemini-embedding-001",
            output_dimensionality=3072,
        )

        self.qdrant_service = QdrantService(vector_size=3072)

        self.llm_service = LLMService()

        self.prompt_builder = PromptBuilder()
        self.context_builder = ContextBuilder()
        self.citation_builder = CitationBuilder()

        self.history_service = RecentHistoryService()
        self.memory_retriever = MemoryRetriever()

    # Main entry
    async def run(
        self,
        query: str,
        conversation,
        case_id: Optional[str] = None,
    ) -> dict:

        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        query = query.strip()

        logger.info(
            "RAG pipeline started | conversation_id=%s | case_id=%s",
            getattr(conversation, "id", None),
            case_id,
        )

        try:
            # 1. Embed Query
            query_vector = self.embedding_engine.embed(query)

            logger.debug(
                "Query embedded | dims=%s",
                len(query_vector),
            )

            memories = await sync_to_async(self.memory_retriever.get_relevant)(
                conversation=conversation,
                query_embedding=query_vector,
                top_k=3,
            )

            summary_obj = await sync_to_async(
                lambda: (
                    ConversationSummary.objects.filter(conversation=conversation)
                    .only("summary")
                    .first()
                )
            )()

            summary = summary_obj.summary if summary_obj else ""

            # 4. Retrieve Recent History
            history = await sync_to_async(self.history_service.get_recent)(conversation)

            # 5. Retrieve Legal Documents (Qdrant)
            search_results = self.qdrant_service.search_with_filter(
                query_vector=query_vector,
                case_id=case_id,
                limit=5,
            )

            logger.info(
                "Retrieved context | qdrant=%s | memories=%s | history=%s",
                len(search_results),
                len(memories),
                len(history),
            )

            # 6. Build Structured Context
            context = self.context_builder.build(
                summary=summary,
                memories=memories,
                search_results=search_results,
            )

            formatted_context = [
                {
                    "src_id": f"SRC_{i+1}",
                    "document_id": item["document_id"],
                    "chunk_index": item["chunk_index"],
                    "text": item["text"],
                }
                for i, item in enumerate(context)
            ]

            # 7. Build Final Prompt
            prompt = self.prompt_builder.build(
                system_prompt=system_prompt,
                user_message=query,
                history=history,
                context=formatted_context,
            )

            # 8. LLM Call
            answer = await self.llm_service.generate(
                messages=prompt,
                model_name="gemini-2.5-flash",
            )

            # 9. Citations
            citations = self.citation_builder.build(search_results)

            logger.info(
                "RAG pipeline completed | conversation_id=%s",
                getattr(conversation, "id", None),
            )

            # 10. Response
            return {
                "query": query,
                "answer": asdict(answer),
                "citations": citations,
                "metrics": {
                    "chunks_retrieved": len(search_results),
                    "memories_retrieved": len(memories),
                    "history_length": len(history),
                },
            }

        except Exception as e:
            logger.exception(
                "RAG pipeline failed | conversation_id=%s",
                getattr(conversation, "id", None),
            )
            raise RuntimeError(f"RAG pipeline error: {str(e)}") from e
