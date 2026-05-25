import torch
import numpy as np
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from typing import List, Union

class EmbeddingEngine:
    """
    Embedding service for RAG + Qdrant.
    """
    
    def __init__(
        self,
        model: str = "BAAI/bge-small-en",
        max_length: int = 512,
        normalize: bool = True
    ):
        self.model_name = model
        self.max_length = max_length
        self.normalize = normalize
        
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )
        
        # load model + tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name).to(self.device)
        
    
    # Internal pooling
    def _mean_pooling(self, token_embeddings, attention_mask):
        mask = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        summed = tor
        
        