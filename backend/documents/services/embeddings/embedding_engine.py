from __future__ import annotations

import logging
from typing import List, Optional
from google.genai import types
from django.conf import settings

logger = logging.getLogger(__name__)


class EmbeddingEngine:
    """
    Gemini Embedding Engine

    Production-ready embedding service for:
    - Qdrant
    - RAG pipelines
    - Semantic search
    """

    DEFAULT_MODEL = "gemini-embedding-001"
    MAX_BATCH_SIZE = 96  # Safely under Google's strict 100-request limit

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        output_dimensionality: Optional[int] = None,
    ):
        self.model_name = model_name
        self.output_dimensionality = output_dimensionality

    @property
    def client(self):
        if not hasattr(self, "_client"):
            from google import genai

            self._client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        return self._client

    def _embedding_config(self):
        """
        Build embedding config only when dimensions are specified.
        """
        if self.output_dimensionality is None:
            return None

        return types.EmbedContentConfig(
            output_dimensionality=self.output_dimensionality
        )

    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text string.
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty.")

        try:
            response = self.client.models.embed_content(
                model=self.model_name,
                contents=text.strip(),
                config=self._embedding_config(),
            )
            return response.embeddings[0].values

        except Exception as exc:
            logger.exception("Embedding generation failed.")
            raise RuntimeError(f"Failed generating embedding: {exc}") from exc

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts, safely splitting them
        into sub-batches to abide by the Gemini API limit of 100 requests per call.
        """
        if not texts:
            return []

        # Defensive step: Ensure no empty or pure whitespace blocks crash the API call
        cleaned_texts = [t.strip() if (t and t.strip()) else "N/A" for t in texts]

        all_embeddings: List[List[float]] = []
        total_chunks = len(cleaned_texts)

        # Loop through chunks in increments of 96
        for i in range(0, total_chunks, self.MAX_BATCH_SIZE):
            sub_batch = cleaned_texts[i : i + self.MAX_BATCH_SIZE]

            logger.info(
                f"Processing sub-batch {(i // self.MAX_BATCH_SIZE) + 1} "
                f"for model {self.model_name} (Size: {len(sub_batch)})"
            )

            try:
                response = self.client.models.embed_content(
                    model=self.model_name,
                    contents=sub_batch,
                    config=self._embedding_config(),
                )

                # Safely extract values out of the response structures
                batch_vectors = [embedding.values for embedding in response.embeddings]
                all_embeddings.extend(batch_vectors)

            except Exception as exc:
                logger.exception(
                    f"Batch embedding sub-segment failed at chunk index range {i}:{i+self.MAX_BATCH_SIZE}"
                )
                raise RuntimeError(
                    f"Failed generating batch embeddings subset: {exc}"
                ) from exc

        return all_embeddings

    def embedding_dimension(self) -> int:
        """
        Helper method to determine actual vector size.
        Useful for creating Qdrant collections dynamically.
        """
        vector = self.embed("dimension test")
        return len(vector)
