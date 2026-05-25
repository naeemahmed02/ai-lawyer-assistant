from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

import puremagic

from ..models import Document

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


class DocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for legal documents in the AI Legal RAG platform.
    """

    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())

    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

    class Meta:
        model = Document

        exclude = [
            "embedding_id",
            "processing_error",
        ]

        read_only_fields = [
            "id",
            "owner",
            "created_at",
            "updated_at",
            "processing_status",
            "is_vectorized",
            "chunk_count",
            "mime_type",
            "file_size",
            "page_count",
            "language",
            "summary",
            "keywords",
            "extracted_text",
        ]

    # FIELD VALIDATION

    def validate_title(self, value):
        """
        Validate document title.
        """

        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError(
                _("Title must be at least 3 characters long.")
            )

        return value

    def validate_file(self, file):
        """
        Validate uploaded file.
        """

        if not file:
            raise serializers.ValidationError(_("Document file is required."))

        if file.size == 0:
            raise serializers.ValidationError(_("File must not be empty."))

        if file.size > self.MAX_FILE_SIZE:
            raise serializers.ValidationError(_("File size cannot exceed 20 MB."))

        # Read first bytes for MIME detection
        file_header = file.read(2048)

        # Reset pointer after reading
        file.seek(0)

        try:
            guessed_mime = puremagic.from_string(
                file_header,
                mime=True,
            )

        except puremagic.PureError:
            raise serializers.ValidationError(_("Unsupported or corrupted file."))

        if guessed_mime not in ALLOWED_MIME_TYPES:
            raise serializers.ValidationError(
                _(f"File type '{guessed_mime}' is not allowed.")
            )

        return file

    # OBJECT LEVEL VALIDATION
    def validate(self, attrs):
        """
        Cross-field validation.
        """

        document_type = attrs.get("document_type")
        case_id = attrs.get("case_id")

        # Example business rule
        if document_type == Document.DocumentType.JUDGMENT and not case_id:
            raise serializers.ValidationError(
                {"case_id": _("Judgment documents must be linked " "to a case ID.")}
            )

        return attrs

    # CREATE
    def create(self, validated_data):
        """
        Create document instance.
        """

        file = validated_data.get("file")

        if file:
            validated_data["file_size"] = file.size

            # Use detected MIME instead of trusting client header
            file_header = file.read(2048)
            file.seek(0)

            try:
                validated_data["mime_type"] = puremagic.from_string(
                    file_header,
                    mime=True,
                )

            except puremagic.PureError:
                validated_data["mime_type"] = None

        return super().create(validated_data)

    # UPDATE
    def update(self, instance, validated_data):
        """
        Prevent protected AI fields from being updated manually.
        """

        protected_fields = {
            "embedding_id",
            "is_vectorized",
            "processing_status",
            "chunk_count",
            "processing_error",
            "summary",
            "keywords",
            "extracted_text",
        }

        for field in protected_fields:
            validated_data.pop(field, None)

        return super().update(instance, validated_data)
