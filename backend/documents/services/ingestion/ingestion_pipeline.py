from ..extraction.extractor import DocConverter
from ..chunking.document_chunker import SemanticChunking
from ..embeddings.embedding_engine import EmbeddingEngine
from documents.models import Document
from docling.document_converter import DocumentConverter

from ..vectorstore.qdrant_service import QdrantService
from django.shortcuts import get_object_or_404


class DocumentIngestionPipeline:
    """Complete production ingestion pipeline.

    Flow:
    PDF -> Text -> Clean -> Chunk -> Embed -> Qdrant
    """

    def __init__(self):
        # Heavy AI model initialized ONLY ONCE
        self.shared_converter = DocumentConverter()

        # Dependency Injection
        self.extractor = DocConverter(converter=self.shared_converter)

        self.chunker = SemanticChunking()

        self.embedding_engine = EmbeddingEngine()
        self.qdrant_service = QdrantService()

    def run(self, document_id: str):

        # fetch the document from the database
        document = get_object_or_404(Document, id=document_id)

        # extract the text

        # 1. Initialize the heavy AI model ONLY ONCE globally
        shared_converter = DocumentConverter()

        # 2. Inject the shared model into your utility worker class
        worker = DocConverter(converter=shared_converter)

        # doc_to_processed = [document]

        raw_result = worker.convert_document(document.file.path)

        # extract real text
        raw_text = raw_result.document.export_to_markdown()

        document.extracted_text = {
            "text": raw_text,
            "source": "docling",
            "pages": (
                len(raw_result.document.pages)
                if hasattr(raw_result.document, "pages")
                else None
            ),
        }
        document.save()

        # chunk text
        chunks = self.chunker.semantic_chunking(raw_text)

        # generate embeddings
        embeddings = self.embedding_engine.embed_batch(chunks)

        # prepare metadata
        metadata_list = []
        
        for idx, chunk in enumerate(chunks):
            
            metadata_list.append({
                "chunk_id" : f"{str(document.id)}_{idx}",
                "document_id": str(document.id),
                "case_id": str(document.case_id),
                "document_type": document.document_type,
                "chunk_index" : idx
            }
            )
            
        # Store in qdrant
        self.qdrant_service.upsert_chunks(
            embeddings = embeddings,
            chunks = chunks,
            metadata_list = metadata_list
            
        )
        
        # mark document processed
        document.processing_status = Document.ProcessingStatus.COMPLETED
        document.save()