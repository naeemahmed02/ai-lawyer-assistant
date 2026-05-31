import uuid
import logging
from typing import List, Optional, Dict, Any

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    FilterSelector,
    PayloadSchemaType,
)

logger = logging.getLogger(__name__)


class QdrantService:
    """
    Qdrant service for Legal RAG systems.

    Features:
    - Safe collection creation
    - Deterministic UUID generation
    - Batch vector upsert
    - Hybrid semantic + metadata search
    - Payload indexing
    - Connection safety
    - Logging + validation
    """

    def __init__(
        self,
        host: str = "qdrant",
        port: int = 6333,
        collection_name: str = "legal_chunks",
        vector_size: int = 384,
        timeout: int = 30,
    ):

        self.collection_name = collection_name
        self.vector_size = vector_size

        # Safe client connection
        self.client = QdrantClient(
            host=host,
            port=port,
            timeout=timeout,
        )

        self._health_check()
        self._ensure_collection()
        self._create_payload_indexes()

    # HEALTH CHECK
    def _health_check(self):
        """
        Verify Qdrant is reachable.
        """

        try:
            self.client.get_collections()
            logger.info("Connected to Qdrant successfully.")

        except Exception as e:
            logger.exception("Qdrant connection failed.")
            raise RuntimeError("Could not connect to Qdrant.") from e

    # COLLECTION MANAGEMENT
    def _ensure_collection(self):
        """
        Create collection if it doesn't exist.
        """

        try:
            collections = self.client.get_collections().collections
            existing = {c.name for c in collections}

            if self.collection_name not in existing:

                logger.info(f"Creating Qdrant collection: {self.collection_name}")

                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE,
                    ),
                )

        except Exception as e:
            logger.exception("Collection initialization failed.")
            raise

    # PAYLOAD INDEXES
    def _create_payload_indexes(self):
        """
        Create payload indexes for fast filtering.
        """

        indexed_fields = [
            "case_id",
            "document_id",
            "document_type",
        ]

        for field in indexed_fields:

            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field,
                    field_schema=PayloadSchemaType.KEYWORD,
                )

            except UnexpectedResponse:
                # Index already exists
                pass

            except Exception as e:
                logger.warning(f"Could not create payload index for {field}: {e}")

    # UUID GENERATION
    @staticmethod
    def _generate_point_id(chunk_id: str) -> str:
        """
        Generate deterministic UUID from chunk_id.

        Ensures:
        - valid UUID format
        - stable IDs
        - deduplication safety
        """

        return str(
            uuid.uuid5(
                uuid.NAMESPACE_DNS,
                chunk_id,
            )
        )

    # UPSERT CHUNKS
    def upsert_chunks(
        self,
        embeddings: List[List[float]],
        chunks: List[str],
        metadata_list: List[Dict[str, Any]],
        batch_size: int = 64,
    ):
        """
        Batch upsert embeddings into Qdrant.
        """

        # VALIDATION
        if not embeddings:
            logger.warning("No embeddings provided.")
            return

        if len(embeddings) != len(chunks):
            raise ValueError("Embeddings/chunks count mismatch.")

        if len(chunks) != len(metadata_list):
            raise ValueError("Chunks/metadata count mismatch.")

        total_points = len(chunks)

        logger.info(f"Preparing {total_points} vectors for Qdrant upsert.")

        # BATCH UPSERT
        for start in range(0, total_points, batch_size):

            end = start + batch_size

            batch_embeddings = embeddings[start:end]
            batch_chunks = chunks[start:end]
            batch_metadata = metadata_list[start:end]

            points: List[PointStruct] = []

            for idx, (embedding, chunk, metadata) in enumerate(
                zip(
                    batch_embeddings,
                    batch_chunks,
                    batch_metadata,
                )
            ):

                if len(embedding) != self.vector_size:
                    raise ValueError(
                        f"Invalid vector size at index {idx}. "
                        f"Expected={self.vector_size}, "
                        f"Got={len(embedding)}"
                    )

                raw_chunk_id = metadata.get(
                    "chunk_id",
                    str(uuid.uuid4()),
                )

                point_id = self._generate_point_id(raw_chunk_id)

                payload = {
                    "text": chunk,
                    **metadata,
                }

                points.append(
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload,
                    )
                )

            try:

                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points,
                    wait=True,
                )

                logger.info(f"Inserted batch " f"{start}-{min(end, total_points)}")

            except Exception as e:
                logger.exception("Qdrant batch upsert failed.")
                raise

    # SEARCH
    def search(
        self,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: float = 0.5,
        query_filter: Optional[Filter] = None,
    ):
        """
        Semantic similarity search.
        """

        return self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=query_filter,
        )

    # FILTER BUILDER
    def build_filter(
        self,
        case_id: Optional[str] = None,
        document_type: Optional[str] = None,
    ) -> Optional[Filter]:
        """
        Build metadata filters safely.
        """

        conditions = []

        if case_id:
            conditions.append(
                FieldCondition(
                    key="case_id",
                    match=MatchValue(value=case_id),
                )
            )

        if document_type:
            conditions.append(
                FieldCondition(
                    key="document_type",
                    match=MatchValue(value=document_type),
                )
            )

        if not conditions:
            return None

        return Filter(must=conditions)

    # HYBRID SEARCH
    def search_with_filter(
        self,
        query_vector: List[float],
        case_id: Optional[str] = None,
        document_type: Optional[str] = None,
        limit: int = 5,
        score_threshold: float = 0.5,
    ):

        query_filter = self.build_filter(
            case_id=case_id,
            document_type=document_type,
        )

        return self.search(
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=query_filter,
        )

    # DELETE
    def delete_by_case(self, case_id: str):
        """
        Delete all vectors for a case.
        """

        try:

            self.client.delete(
                collection_name=self.collection_name,
                points_selector=FilterSelector(
                    filter=Filter(
                        must=[
                            FieldCondition(
                                key="case_id",
                                match=MatchValue(value=case_id),
                            )
                        ]
                    )
                ),
                wait=True,
            )

            logger.info(f"Deleted vectors for case_id={case_id}")

        except Exception:
            logger.exception(f"Failed deleting vectors for case={case_id}")
            raise
