import logging
from typing import List, Dict, Any

from django.shortcuts import get_object_or_404
from django.db import transaction

from documents.models import Document
from ..utils.json_safe import make_json_safe

logger = logging.getLogger(__name__)


class DocumentIngestionPipeline:
    """
    CLEAN ORCHESTRATION LAYER (NO ML IMPORTS HERE)

    Responsibilities:
    - DB state handling
    - calling runtime service
    - error management
    """

    def run(self, document_id: str) -> Dict[str, Any]:

        document = None

        try:
            # FETCH DOCUMENT
            document = get_object_or_404(Document, id=document_id)

            if document.processing_status == Document.ProcessingStatus.COMPLETED:
                return {
                    "status": "already_completed",
                    "document_id": str(document.id),
                }

            with transaction.atomic():
                document.processing_status = Document.ProcessingStatus.PROCESSING
                document.save(update_fields=["processing_status"])

            logger.info(f"Pipeline started document={document.id}")

            # CALL RUNTIME (ALL HEAVY WORK)
            from .runtime import IngestionRuntime

            runtime = IngestionRuntime()

            result = runtime.process(document)

            # AI ANALYSIS
            from documents.services.analysis.document_analysis_service import (
                DocumentAnalysisService,
            )

            analysis_service = DocumentAnalysisService()

            analysis = analysis_service.analyze(document)

            # FINALIZE DOCUMENT DATA
            document.summary = analysis["summary"]

            document.keywords = {
                "tags": analysis["tags"],
            }

            # FINALIZE STATE
            with transaction.atomic():
                document.processing_status = Document.ProcessingStatus.COMPLETED
                document.is_vectorized = True

                document.save(
                    update_fields=[
                        "summary",
                        "keywords",
                        "processing_status",
                        "is_vectorized",
                    ]
                )

            logger.info(f"Pipeline completed document={document.id}")

            return result

        except Exception as e:
            logger.exception(f"Pipeline failed document={document_id}: {e}")

            if document:
                try:
                    document.processing_status = Document.ProcessingStatus.FAILED
                    document.save(update_fields=["processing_status"])
                except Exception:
                    logger.error("Failed updating document status")

            raise
