import re
import numpy as np
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class SemanticChunking:
    """
    Production-ready semantic chunking engine.

    Features:
    - Lazy-loaded SentenceTransformer (prevents Django startup crash)
    - CPU/GPU safe execution
    - Batch optimized embeddings
    - Memory efficient cosine similarity
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        similarity_threshold: float = 0.6,
        device: Optional[str] = None,
    ):
        self.model_name = model_name
        self.similarity_threshold = similarity_threshold
        self.device = device

        self._model = None

    # LAZY MODEL LOADING (CRITICAL)
    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info(f"Loading SentenceTransformer model: {self.model_name}")

                self._model = SentenceTransformer(
                    self.model_name,
                    device=self.device if self.device else "cpu",
                )

                logger.info("SentenceTransformer loaded successfully")

            except Exception as e:
                logger.exception("Failed to load SentenceTransformer model")
                raise RuntimeError(f"Embedding model initialization failed: {e}")

        return self._model

    # TEXT PREPROCESSING
    def _split_sentences(self, text: str) -> List[str]:
        if not text:
            return []

        sentences = [
            s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s and s.strip()
        ]

        return sentences

    # MAIN CHUNKING LOGIC
    def semantic_chunking(self, text: str) -> List[str]:
        sentences = self._split_sentences(text)

        if len(sentences) <= 1:
            return sentences

        model = self._get_model()

        try:
            # EMBEDDINGS (OPTIMIZED)
            embeddings = model.encode(
                sentences,
                batch_size=32,
                show_progress_bar=False,
                normalize_embeddings=True,  # IMPORTANT: avoids manual normalization
            )

            embeddings = np.array(embeddings)

        except Exception as e:
            logger.exception("Embedding generation failed")
            raise RuntimeError(f"Embedding failed: {e}")

        # SEMANTIC GROUPING
        chunks: List[str] = []
        current_chunk = [sentences[0]]

        for i in range(1, len(sentences)):

            # cosine similarity (already normalized)
            similarity = float(np.dot(embeddings[i - 1], embeddings[i]))

            if similarity < self.similarity_threshold:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentences[i]]
            else:
                current_chunk.append(sentences[i])

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks
