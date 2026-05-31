import logging
from typing import List, Dict, Any
from ..utils.json_safe import make_json_safe

logger = logging.getLogger(__name__)


class IngestionRuntime:
    """
    HEAVY ML LAYER (ISOLATED FROM DJANGO IMPORT GRAPH)

    Contains:
    - docling
    - sentence-transformers
    - embeddings
    - qdrant
    """

    def __init__(self):
        self._extractor = None
        self._chunker = None
        self._embedding_engine = None
        self._qdrant = None

    # DOC EXTRACTION (LAZY)
    def _get_extractor(self):
        if self._extractor is None:
            from ..extraction.extractor import DocConverter
            self._extractor = DocConverter()
        return self._extractor

    # CHUNKING (LAZY)
    def _get_chunker(self):
        if self._chunker is None:
            from ..chunking.document_chunker import SemanticChunking
            self._chunker = SemanticChunking()
        return self._chunker

    # EMBEDDINGS (LAZY)
    def _get_embedding_engine(self):
        if self._embedding_engine is None:
            from ..embeddings.embedding_engine import EmbeddingEngine
            self._embedding_engine = EmbeddingEngine()
        return self._embedding_engine

    # VECTOR STORE (LAZY)
    def _get_qdrant(self):
        if self._qdrant is None:
            from ..vectorstore.qdrant_service import QdrantService
            self._qdrant = QdrantService()
        return self._qdrant

    # MAIN PROCESS
    def process(self, document) -> Dict[str, Any]:

        # 1. Extraction
        extractor = self._get_extractor()
        raw_result = extractor.convert_document(document.file.path)

        if not raw_result or not hasattr(raw_result, "document"):
            raise ValueError("Extraction failed")

        raw_text = raw_result.document.export_to_markdown()

        if not raw_text or not raw_text.strip():
            raise ValueError("Empty extracted text")

        pages = getattr(raw_result.document, "pages", None)
        page_count = len(pages) if pages else 0

        document.extracted_text = make_json_safe({
            "text": raw_text,
            "source": "docling",
            "pages": page_count,
        })
        document.page_count = page_count
        document.save(update_fields=["extracted_text", "page_count"])

        # 2. Chunking
        chunker = self._get_chunker()
        chunks = chunker.semantic_chunking(raw_text)

        if not chunks:
            raise ValueError("No chunks generated")

        document.chunk_count = len(chunks)
        document.save(update_fields=["chunk_count"])

        # 3. Embeddings
        embedding_engine = self._get_embedding_engine()
        embeddings = embedding_engine.embed_batch(chunks)

        if not embeddings or len(embeddings) != len(chunks):
            raise ValueError("Embedding mismatch")

        # 4. Metadata
        metadata_list: List[Dict[str, Any]] = [
            {
                "chunk_id": f"{document.id}_{i}",
                "document_id": str(document.id),
                "case_id": str(document.case_id),
                "document_type": str(document.document_type),
                "chunk_index": i,
            }
            for i in range(len(chunks))
        ]

        # 5. Vector DB
        qdrant = self._get_qdrant()
        qdrant.upsert_chunks(
            embeddings=embeddings,
            chunks=chunks,
            metadata_list=metadata_list,
        )

        return {
            "status": "success",
            "document_id": str(document.id),
            "chunks": len(chunks),
            "pages": page_count,
        }