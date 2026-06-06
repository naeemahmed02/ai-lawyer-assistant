# import torch
# import numpy as np
# import torch.nn.functional as F
# from transformers import AutoTokenizer, AutoModel
# from typing import List


# class EmbeddingEngine:
#     """
#     Embedding service for RAG + Qdrant.
#     """

#     def __init__(
#         self,
#         model_name: str = "BAAI/bge-small-en",
#         max_length: int = 512,
#         normalize: bool = True,
#     ):
#         self.model_name = model_name
#         self.max_length = max_length
#         self.normalize = normalize

#         # Device setup (GPU if available)
#         self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

#         # Load model + tokenizer
#         self.tokenizer = AutoTokenizer.from_pretrained(model_name)
#         self.model = AutoModel.from_pretrained(model_name).to(self.device)

#         self.model.eval()

#     # Internal pooling
#     def _mean_pooling(self, token_embeddings, attention_mask):
#         mask = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
#         summed = torch.sum(token_embeddings * mask, dim=1)
#         counts = torch.clamp(mask.sum(dim=1), min=1e-9)
#         return summed / counts

#     # Single text embedding
#     def embed(self, text: str) -> List[float]:
#         inputs = self.tokenizer(
#             text,
#             padding=True,
#             truncation=True,
#             max_length=self.max_length,
#             return_tensors="pt",
#         ).to(self.device)

#         with torch.no_grad():
#             outputs = self.model(**inputs)

#         embeddings = self._mean_pooling(
#             outputs.last_hidden_state, inputs["attention_mask"]
#         )

#         if self.normalize:
#             embeddings = F.normalize(embeddings, p=2, dim=1)

#         return embeddings.squeeze(0).cpu().numpy().tolist()

#     # Batch embedding
#     def embed_batch(self, texts: List[str]) -> List[List[float]]:
#         inputs = self.tokenizer(
#             texts,
#             padding=True,
#             truncation=True,
#             max_length=self.max_length,
#             return_tensors="pt",
#         ).to(self.device)

#         with torch.no_grad():
#             outputs = self.model(**inputs)

#         embeddings = self._mean_pooling(
#             outputs.last_hidden_state, inputs["attention_mask"]
#         )

#         if self.normalize:
#             embeddings = F.normalize(embeddings, p=2, dim=1)

#         return embeddings.cpu().numpy().tolist()


# if __name__ == "__main__":
#     engine = EmbeddingEngine()

#     text = "Machine learning is amazing."

#     embedding = engine.embed(text)

#     print(f"Text: {text}")
#     print(f"Embedding dimension: {len(embedding)}")
#     print(f"First 10 values: {embedding[:10]}")


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

    Notes:
    - Ensure Qdrant collection dimension matches output_dimensionality.
    - All indexed documents and queries must use the same model/config.
    """

    DEFAULT_MODEL = "gemini-embedding-001"

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
        Generate embedding for a single text.

        Returns:
            List[float]
        """

        if not text or not text.strip():
            raise ValueError("Text cannot be empty.")

        try:
            response = self.client.models.embed_content(
                model=self.model_name,
                contents=text,
                config=self._embedding_config(),
            )

            return response.embeddings[0].values

        except Exception as exc:
            logger.exception("Embedding generation failed.")
            raise RuntimeError(f"Failed generating embedding: {exc}") from exc

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Returns:
            List[List[float]]
        """

        if not texts:
            return []

        try:
            response = self.client.models.embed_content(
                model=self.model_name,
                contents=texts,
                config=self._embedding_config(),
            )

            return [embedding.values for embedding in response.embeddings]

        except Exception as exc:
            logger.exception("Batch embedding generation failed.")
            raise RuntimeError(f"Failed generating batch embeddings: {exc}") from exc

    def embedding_dimension(self) -> int:
        """
        Helper method to determine actual vector size.

        Useful for creating Qdrant collections.
        """

        vector = self.embed("dimension test")
        return len(vector)
