import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Document(models.Model):
    """
    Central document model for the Advanced Legal RAG platform.

    A Document represents any legal artifact uploaded into the system,
    including petitions, judgments, contracts, hearing records,
    evidences, and supporting files.

    This model is designed for:
    - Vector database synchronization
    - LLM retrieval pipelines
    - Semantic chunking
    - OCR workflows
    - AI summarization
    - Citation extraction
    - Multi-tenant legal systems
    """

    class DocumentType(models.TextChoices):
        """
        Supported legal document categories.
        """

        JUDGMENT = "judgment", _("Judgment")
        PETITION = "petition", _("Petition")
        CONTRACT = "contract", _("Contract")
        HEARING = "hearing", _("Hearing")
        EVIDENCE = "evidence", _("Evidence")
        LEGAL_NOTICE = "legal_notice", _("Legal Notice")
        AGREEMENT = "agreement", _("Agreement")
        AFFIDAVIT = "affidavit", _("Affidavit")
        OTHER = "other", _("Other")

    class ProcessingStatus(models.TextChoices):
        """
        AI/RAG document processing lifecycle.
        """

        PENDING = "pending", _("Pending")
        PROCESSING = "processing", _("Processing")
        COMPLETED = "completed", _("Completed")
        FAILED = "failed", _("Failed")

    # Primary Identifier
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Globally unique identifier for the document."),
    )

    # Core Document Information
    title = models.CharField(
        max_length=1000,
        unique=True,
        db_index=True,
        help_text=_("Human-readable title of the document."),
    )

    file = models.FileField(
        upload_to="docs/documents/%Y/%m/%d/",
        help_text=_("Original uploaded legal document file."),
    )

    document_type = models.CharField(
        max_length=50,
        choices=DocumentType.choices,
        db_index=True,
        help_text=_("Categorization type of the legal document."),
    )

    # Ownership & Multi-Tenancy
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
        help_text=_("User who uploaded or owns the document."),
    )

    # Legal Case Association
    case_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
        help_text=_(
            "Optional external/internal case identifier associated "
            "with this document."
        ),
    )

    # AI / RAG Processing Fields
    extracted_text = models.JSONField(
        null=True,
        blank=True,
        help_text=_(
            "Structured extracted content from OCR, parsers, "
            "or AI preprocessing pipelines."
        ),
    )

    summary = models.TextField(
        null=True,
        blank=True,
        help_text=_("AI-generated summary of the document."),
    )

    keywords = models.JSONField(
        null=True,
        blank=True,
        help_text=_("AI extracted keywords, entities, citations, and tags."),
    )

    embedding_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Reference ID for vector database embedding storage."),
    )

    chunk_count = models.PositiveIntegerField(
        default=0,
        help_text=_("Number of semantic chunks generated for retrieval."),
    )

    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
        db_index=True,
        help_text=_("Current AI/RAG processing state."),
    )

    processing_error = models.TextField(
        null=True,
        blank=True,
        help_text=_("Stores processing failure logs or exception messages."),
    )

    is_vectorized = models.BooleanField(
        default=False,
        db_index=True,
        help_text=_("Indicates whether embeddings were successfully generated."),
    )

    # File Metadata
    file_size = models.BigIntegerField(
        null=True,
        blank=True,
        help_text=_("Uploaded file size in bytes."),
    )

    mime_type = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Detected MIME type of the uploaded file."),
    )

    language = models.CharField(
        max_length=50,
        default="en",
        help_text=_("Detected primary language of the document."),
    )

    page_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_("Total number of pages in the document."),
    )

    # Audit & Lifecycle
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text=_("Timestamp when the document was created."),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("Timestamp when the document was last updated."),
    )

    # Model Metadata
    class Meta:
        """
        Database-level configuration and optimization.
        """

        verbose_name = _("Document")
        verbose_name_plural = _("Documents")

        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["document_type"]),
            models.Index(fields=["processing_status"]),
            models.Index(fields=["case_id"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["owner", "created_at"]),
        ]

    # -------------------------------------------------------------------------
    # String Representation
    def __str__(self):
        """
        Human-readable representation of the document.
        """
        return f"{self.title} ({self.document_type})"

    # Convenience Properties
    @property
    def is_processed(self) -> bool:
        """
        Returns True if AI processing completed successfully.
        """
        return self.processing_status == self.ProcessingStatus.COMPLETED

    @property
    def has_embeddings(self) -> bool:
        """
        Returns True if vector embeddings exist.
        """
        return bool(self.embedding_id and self.is_vectorized)
