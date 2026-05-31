import os
import logging
from typing import Optional

from docling.datamodel.document import ConversionResult

logger = logging.getLogger(__name__)


class DocConverter:
    """
    Production-safe Docling wrapper.

    Key design:
    - NO heavy imports at module level
    - Lazy initialization (Celery-safe)
    - Single shared converter per worker process
    """

    def __init__(self):
        self._converter: Optional[object] = None

    def _get_converter(self):
        """
        Lazy-load Docling ONLY inside worker process.
        Prevents Django/Gunicorn startup crash.
        """
        if self._converter is None:
            try:
                from docling.document_converter import DocumentConverter
                self._converter = DocumentConverter()
                logger.info("Docling DocumentConverter initialized")
            except Exception as e:
                logger.exception("Failed to initialize DocumentConverter")
                raise RuntimeError(f"Docling init failed: {e}")

        return self._converter

    def convert_document(self, file_path: str) -> ConversionResult:
        """
        Convert document safely with validation + logging.
        """

        if not file_path:
            raise ValueError("file_path is required")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        converter = self._get_converter()

        try:
            logger.info(f"Starting document conversion: {file_path}")
            result = converter.convert(file_path)
            logger.info(f"Document conversion completed: {file_path}")
            return result

        except Exception as e:
            logger.exception(f"Docling conversion failed: {file_path}")
            raise RuntimeError(f"Conversion failed: {str(e)}")