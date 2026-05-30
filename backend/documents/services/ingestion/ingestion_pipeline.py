import logging
from typing import List

from django.db import transaction
from django.shortcuts import get_object_or_404

from documents.models import Document

from docling.document_converter import DocumentConverter

from ..chunking.document_chunker import SemanticChunking
from ..embeddings.embedding_engine import EmbeddingEngine
from ..extraction.extractor import DocConverter
from ..utils.json_safe import make_json_safe
from ..vectorstore.qdrant_service import QdrantService

logger = logging.getLogger(__name__)


class DocumentIngestionPipeline:
    """
    Production-grade ingestion pipeline.

    Flow:
    PDF -> Extraction -> Chunking -> Embeddings -> Qdrant
    """

    def __init__(self):

        # Heavy model initialized once per worker process
        self.converter = DocumentConverter()

        # Dependency injection
        self.extractor = DocConverter(converter=self.converter)

        self.chunker = SemanticChunking()

        self.embedding_engine = EmbeddingEngine()

        self.qdrant = QdrantService()

    def run(self, document_id: str):

        document = None

        try:
            # ----------------------------------------
            # 1. Fetch document
            # ----------------------------------------
            document = get_object_or_404(Document, id=document_id)

            logger.info(f"Starting ingestion document={document.id}")

            # mark processing
            document.processing_status = (
                Document.ProcessingStatus.PROCESSING
            )
            document.save(update_fields=["processing_status"])

            # ----------------------------------------
            # 2. Extract document
            # ----------------------------------------
            raw_result = self.extractor.convert_document(
                document.file.path
            )

            if not raw_result:
                raise ValueError("Document extraction failed")

            # ----------------------------------------
            # 3. Export markdown safely
            # ----------------------------------------
            raw_text = raw_result.document.export_to_markdown()

            if not raw_text or not raw_text.strip():
                raise ValueError("No text extracted from document")

            # ----------------------------------------
            # 4. Safe metadata extraction
            # ----------------------------------------
            pages = getattr(raw_result.document, "pages", None)

            extracted_payload = {
                "text": raw_text,
                "source": "docling",
                "pages": len(pages) if pages else 0,
            }

            # make JSON serializable
            extracted_payload = make_json_safe(extracted_payload)

            # ----------------------------------------
            # 5. Save extracted text
            # ----------------------------------------
            document.extracted_text = extracted_payload

            document.save(update_fields=["extracted_text"])

            logger.info(
                f"Extraction completed document={document.id}"
            )

            # ----------------------------------------
            # 6. Chunking
            # ----------------------------------------
            chunks: List[str] = self.chunker.semantic_chunking(
                raw_text
            )

            if not chunks:
                raise ValueError("No chunks generated")

            logger.info(
                f"Generated {len(chunks)} chunks "
                f"for document={document.id}"
            )

            # ----------------------------------------
            # 7. Generate embeddings
            # ----------------------------------------
            embeddings = self.embedding_engine.embed_batch(chunks)

            if not embeddings:
                raise ValueError("No embeddings generated")

            if len(embeddings) != len(chunks):
                raise ValueError(
                    "Embeddings/chunks count mismatch"
                )

            # ----------------------------------------
            # 8. Build metadata
            # ----------------------------------------
            metadata_list = []

            for idx, _chunk in enumerate(chunks):

                metadata_list.append(
                    {
                        "chunk_id": f"{document.id}_{idx}",
                        "document_id": str(document.id),
                        "case_id": str(document.case_id),
                        "document_type": str(
                            document.document_type
                        ),
                        "chunk_index": idx,
                    }
                )

            # ----------------------------------------
            # 9. Store in Qdrant
            # ----------------------------------------
            self.qdrant.upsert_chunks(
                embeddings=embeddings,
                chunks=chunks,
                metadata_list=metadata_list,
            )

            logger.info(
                f"Qdrant upsert successful document={document.id}"
            )

            # ----------------------------------------
            # 10. Mark completed
            # ----------------------------------------
            document.processing_status = (
                Document.ProcessingStatus.COMPLETED
            )

            document.save(update_fields=["processing_status"])

            logger.info(
                f"Document ingestion completed "
                f"document={document.id}"
            )

            return {
                "status": "success",
                "document_id": str(document.id),
                "chunks": len(chunks),
            }

        except Exception as e:

            logger.exception(
                f"Ingestion failed document_id={document_id}: {e}"
            )

            # avoid secondary crash
            if document:

                document.processing_status = (
                    Document.ProcessingStatus.FAILED
                )

                document.save(
                    update_fields=["processing_status"]
                )

            raise