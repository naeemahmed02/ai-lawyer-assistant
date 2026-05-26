import torch
import numpy as np
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from typing import List


class EmbeddingEngine:
    """
    Embedding service for RAG + Qdrant.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en",
        max_length: int = 512,
        normalize: bool = True,
    ):
        self.model_name = model_name
        self.max_length = max_length
        self.normalize = normalize

        # Device setup (GPU if available)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Load model + tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)

        self.model.eval()

    # Internal pooling
    def _mean_pooling(self, token_embeddings, attention_mask):
        mask = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        summed = torch.sum(token_embeddings * mask, dim=1)
        counts = torch.clamp(mask.sum(dim=1), min=1e-9)
        return summed / counts

    # Single text embedding
    def embed(self, text: str) -> List[float]:
        inputs = self.tokenizer(
            text,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)

        embeddings = self._mean_pooling(
            outputs.last_hidden_state, inputs["attention_mask"]
        )

        if self.normalize:
            embeddings = F.normalize(embeddings, p=2, dim=1)

        return embeddings.squeeze(0).cpu().numpy().tolist()

    # Batch embedding
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)

        embeddings = self._mean_pooling(
            outputs.last_hidden_state, inputs["attention_mask"]
        )

        if self.normalize:
            embeddings = F.normalize(embeddings, p=2, dim=1)

        return embeddings.cpu().numpy().tolist()


if __name__ == "__main__":
    engine = EmbeddingEngine()

    text = "Machine learning is amazing."

    embedding = engine.embed(text)

    print(f"Text: {text}")
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 10 values: {embedding[:10]}")