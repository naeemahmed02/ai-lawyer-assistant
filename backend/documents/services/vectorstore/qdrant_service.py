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
    Production-ready Qdrant service for Legal RAG.

    Features
    --------
    - Health checks
    - Collection auto creation
    - Collection dimension validation
    - Deterministic IDs
    - Batch upserts
    - Metadata filtering
    - Payload indexing
    - Safe deletion
    """

    def __init__(
        self,
        host: str = "qdrant",
        port: int = 6333,
        collection_name: str = "legal_chunks",
        vector_size: int = 3072,
        timeout: int = 30,
    ):
        self.collection_name = collection_name
        self.vector_size = vector_size

        self.client = QdrantClient(
            host=host,
            port=port,
            timeout=timeout,
        )

        self._health_check()
        self._ensure_collection()
        self._create_payload_indexes()

    # HEALTH
    def _health_check(self) -> None:
        try:
            self.client.get_collections()
            logger.info("Connected to Qdrant.")
        except Exception as exc:
            logger.exception("Qdrant connection failed.")
            raise RuntimeError("Unable to connect to Qdrant.") from exc

    # COLLECTION
    def _ensure_collection(self) -> None:
        """
        Creates collection if missing.

        If collection exists:
        validates vector dimension.
        """

        collections = {c.name for c in self.client.get_collections().collections}

        if self.collection_name not in collections:

            logger.info(
                "Creating collection '%s' (dimension=%s)",
                self.collection_name,
                self.vector_size,
            )

            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE,
                ),
            )

            return

        info = self.client.get_collection(collection_name=self.collection_name)

        actual_size = info.config.params.vectors.size  # type: ignore

        if actual_size != self.vector_size:
            raise RuntimeError(
                f"Collection '{self.collection_name}' "
                f"dimension mismatch. "
                f"Collection={actual_size}, "
                f"Configured={self.vector_size}. "
                f"Delete and rebuild collection."
            )

        logger.info(
            "Collection '%s' verified (dimension=%s)",
            self.collection_name,
            actual_size,
        )

    def recreate_collection(self) -> None:
        """
        Delete and recreate collection.

        Useful when switching embedding models.
        """

        logger.warning(
            "Recreating collection '%s'",
            self.collection_name,
        )

        try:
            if self.client.collection_exists(self.collection_name):
                self.client.delete_collection(self.collection_name)

            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE,
                ),
            )

            logger.info("Collection recreated successfully.")

        except Exception:
            logger.exception("Failed recreating collection.")
            raise

    # PAYLOAD INDEXES
    def _create_payload_indexes(self) -> None:
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
                pass

            except Exception as exc:
                logger.warning(
                    "Could not create index for %s: %s",
                    field,
                    exc,
                )

    # IDS
    @staticmethod
    def _generate_point_id(
        chunk_id: str,
    ) -> str:
        return str(
            uuid.uuid5(
                uuid.NAMESPACE_DNS,
                chunk_id,
            )
        )

    # UPSERT
    def upsert_chunks(
        self,
        embeddings: List[List[float]],
        chunks: List[str],
        metadata_list: List[Dict[str, Any]],
        batch_size: int = 64,
    ) -> None:

        if not embeddings:
            logger.warning("No embeddings supplied.")
            return

        if len(embeddings) != len(chunks):
            raise ValueError("Embeddings/chunks mismatch.")

        if len(chunks) != len(metadata_list):
            raise ValueError("Chunks/metadata mismatch.")

        total = len(chunks)

        logger.info(
            "Upserting %s vectors into Qdrant.",
            total,
        )

        for start in range(
            0,
            total,
            batch_size,
        ):
            end = min(
                start + batch_size,
                total,
            )

            points = []

            for embedding, chunk, metadata in zip(
                embeddings[start:end],
                chunks[start:end],
                metadata_list[start:end],
            ):

                if not isinstance(
                    embedding,
                    list,
                ):
                    raise ValueError("Embedding must be a list.")

                if len(embedding) != self.vector_size:
                    raise ValueError(
                        f"Vector size mismatch. "
                        f"Expected={self.vector_size}, "
                        f"Got={len(embedding)}"
                    )

                chunk_id = metadata.get(
                    "chunk_id",
                    str(uuid.uuid4()),
                )

                point_id = self._generate_point_id(chunk_id)

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

                logger.info(
                    "Inserted batch %s-%s",
                    start,
                    end,
                )

            except Exception:
                logger.exception("Batch upsert failed.")
                raise

    # FILTERS
    def build_filter(
        self,
        case_id: Optional[str] = None,
        document_type: Optional[str] = None,
    ) -> Optional[Filter]:

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

        return Filter(
            must=conditions,
        )

    # SEARCH
    def search(
        self,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: Optional[float] = None,
        query_filter: Optional[Filter] = None,
    ):

        if len(query_vector) != self.vector_size:
            raise ValueError(
                f"Query vector dimension mismatch. "
                f"Expected={self.vector_size}, "
                f"Got={len(query_vector)}"
            )

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=query_filter,
            with_payload=True,
        )

        return response.points

    def search_with_filter(
        self,
        query_vector: List[float],
        case_id: Optional[str] = None,
        document_type: Optional[str] = None,
        limit: int = 5,
        score_threshold: Optional[float] = None,
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
    def delete_by_case(
        self,
        case_id: str,
    ) -> None:

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

            logger.info(
                "Deleted vectors for case_id=%s",
                case_id,
            )

        except Exception:
            logger.exception(
                "Delete failed for case=%s",
                case_id,
            )
            raise
