import logging
from typing import Optional
from .builders.context_builder import ContextBuilder
from documents.services.vectorstore.qdrant_service import QdrantService
from documents.services.embeddings.embedding_engine import EmbeddingEngine

from ..llm.service import LLMService
from ..llm.builders.prompt_builder import PromptBuilder
from dataclasses import asdict
from .prompts.system_prompt import system_prompt
from .builders.citation_builder import CitationBuilder

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Production-grade Retrieval-Augmented Generation (RAG) pipeline for
    legal research and question-answering applications.

    The pipeline retrieves relevant legal documents from a vector database,
    constructs grounded context, and generates accurate responses using
    Gemini models. It is designed to provide traceable, context-aware,
    and citation-friendly answers while minimizing hallucinations.

    Key capabilities:
        - Semantic search using Gemini embeddings.
        - Legal document retrieval from Qdrant.
        - Context aggregation and prompt optimization.
        - Gemini-powered answer generation.
        - Source attribution and citation support.
        - Configurable retrieval and generation settings.
        - Robust error handling, logging, and observability.

    Attributes:
        embedding_model: Embedding model used for query vectorization.
        vector_store: Qdrant client for document retrieval.
        llm: Gemini language model used for response generation.
        retriever: Retrieval component responsible for document search.
        prompt_builder: Utility for constructing generation prompts.
        config: Runtime configuration for the pipeline.

    Notes:
        This pipeline is intended for legal assistance and research
        workflows. Generated responses should be reviewed against
        authoritative legal sources before professional use.
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
        self.context_builder = ContextBuilder()
        self.citation_builder = CitationBuilder()

        self.llm_service = LLMService()

    # Main rag entry
    async def run(
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
            # Embed Query
            query_vector = self.embedding_engine.embed(query)
            print("EMBED TYPE:", type(query_vector))

            logger.debug(
                "Generated query embedding (%s dimensions)",
                len(query_vector),
            )

            # Retrieve Relevant Chunks
            search_results = self.qdrant_service.search_with_filter(
                query_vector=query_vector,
                case_id=case_id,
                limit=5,
            )
            print("QDRANT TYPE:", type(search_results))

            logger.info(
                "Retrieved %s chunks",
                len(search_results),
            )

            # Build Context
            context = self.context_builder._build_context(search_results)

            # Build Prompt
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

            # Generate Answer
            answer = await self.llm_service.generate(
                messages=prompt,
                model_name="gemini-2.5-flash",
            )
            print("ANSWER TYPE:", type(answer))

            # build citations
            citations = self.citation_builder.build(search_results)

            return {
                "query": query,
                "answer": asdict(answer),
                "citations": citations,
                "retrieved_chunks": len(search_results),
            }

        except Exception:
            logger.exception("RAG pipeline execution failed.")
            raise
