from qdrant_client import QdrantClient
from qdrant_client.models import (
    PointStruct,
    Distance,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
    Range,
    FilterSelector
)

from typing import List, Optional, Any, Dict
import uuid


class QdrantService:
    """
    Qdrant service for Legal RAG System.
    Support filtering, batching, and scalable retrieval.
    """
    
    def __init__(
        self,
        host: str = 'qdrant',
        port: int = 6333,
        collection_name: str = 'legal_chunks',
        vector_size: int = 384
    ):
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name,
        self.vector_size = vector_size
        
        self._ensure_collection()
        
    
    # collection management
    def _ensure_collection(self):
        """
        Creates collection if not exist (safe for production)
        """
        
        collections = self.client.get_collections().collections
        existing = [c.name for c in collections]
        
        if self.collection_name not in existing:
            self.client.create_collection(
                collection_name = self.collection_name,
                vector_config = VectorParams(
                    size = self.vector_size,
                    distance = Distance.COSINE
                )
            )
        