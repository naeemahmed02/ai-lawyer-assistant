from qdrant_client import QdrantClient
from qdrant_client.models import (
    PointStruct,
    Distance,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
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
        # host: str = 'qdrant',
        # port: int = 6333,
        host="localhost",
        port=6333,
        collection_name: str = 'legal_chunks',
        vector_size: int = 384
    ):
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name
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
                vectors_config = VectorParams(
                    size = self.vector_size,
                    distance = Distance.COSINE
                )
            )
            
    # Upsert (Batch Optimized)
    def upsert_chunks(
        self,
        embeddings: List[List[float]],
        chunks: List[str],
        metadata_list: List[Dict[str, Any]]
        
    ):
        """Batch insert embeddings into Qdrant"""
        
        points = []
        
        for emb, chunk, meta in zip(embeddings, chunks, metadata_list):
            
            point_id = meta.get("chunk_id", str(uuid.uuid4))
            
            payload = {
                "text": chunk,
                **meta
            }
            
            points.append(PointStruct(
                id = point_id,
                vector=emb,
                payload = payload
            ))
            
        self.client.upsert(
            collection_name=self.collection_name,
            points = points
        )
        
    # Basic Search
    def search(
        self,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: float = 0.5,
        query_filter: Optional[Filter] = None
    ):
        """Semantic search with optional filtering."""
        
        return self.client.search(
            collection_name=self.collection_name,
            query_vector = query_vector,
            limit = limit,
            score_threshold=score_threshold,
            query_filter = query_filter
            
        )
        
    
    # Advanced filter builder
    def build_filter(
        self,
        case_id: Optional[str] = None,
        document_type: Optional[str] = None
    ) -> Optional[Filter]:
        must_conditions = []
        
        if case_id:
            must_conditions.append(
                FieldCondition(
                    key = 'case_id',
                    match = MatchValue(value = case_id)
                )
            )
            
        if document_type:
            must_conditions.append(
                FieldCondition(
                    key = "document_type",
                    match = MatchValue(value = document_type)
                )
            )
            
        if not must_conditions:
            return None
        
        return Filter(must=must_conditions)
    
    # Filtered search
    def search_with_filter(
        self,
        query_vector:List[float],
        case_id: Optional[str] = None,
        document_type: Optional[str] = None,
        limit: int = 5,
        score_threshold: float = 0.5
    ):
        """
        Hybird semantic + metadata search
        """
        
        query_filter = self.build_filter(
            case_id = case_id,
            document_type=document_type,
        )
        
        return self.search(
            query_vector = query_vector,
            limit = limit,
            score_threshold = score_threshold,
            query_filter = query_filter
        )
        
        
    def delete_by_case(self, case_id: str):
        """
        Deletes all vectors for a case.
        """

        self.client.delete(
            collection_name=self.collection_name,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(
                            key="case_id",
                            match=MatchValue(value=case_id)
                        )
                    ]
                )
            )
        )
        