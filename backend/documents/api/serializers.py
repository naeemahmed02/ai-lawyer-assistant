from rest_framework import serializers
from ..models import Document
import puremagic

ALLOWED_MIME_TYPES = [
    "application/pdf",
    "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]


class DocumentSerializers(serializers.ModelSerializer):
    
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())

    MAX_FILE_SIZE = 20 * 1024 * 1024

    class Meta:
        model = Document
        fields = "__all__"
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

    def validate_title(self, value):
        value = value.strip()
        if value.length < 3:
            raise serializers.ValidationError("Title is too short.")

        return value

    def validate_file(self, file):
        
        if not file:
            raise serializers.ValidationError("Document file is required.")

        if file.size == 0:
            raise serializers.ValidationError("File must not be empty")
        
        if file.size > self.MAX_FILE_SIZE:
            raise serializers.ValidationError(f"File size can not exceed {self.MAX_FILE_SIZE} MB")
        
        # Read the first 2048 bytes for magic number identification
        file_header = file.read(2048)
        file.seek(0)    # Reset pointer so the file can still be saved
        
        try:
            guessed_mime = puremagic.from_string(file_header, mime=True)
        except puremagic.PureError:
            raise serializers.ValidationError("Unsupported or corrupted file type.")
        
        if guessed_mime not in ALLOWED_MIME_TYPES:
            raise serializers.ValidationError(
                f"File type '{guessed_mime}' is not allowed."
            )
            
    # object level validation
    def validate(self, attrs):
        """Cross field validation"""
        doc_type = attrs.get("document_type")
        case_id = attrs.get('case_id')
        
        if (doc_type == Document.DocumentType.JUDGMENT and not case_id):
            raise serializers.ValidationError(
                {
                    "case_id": (
                        "Judgment documents must be linked "
                        "to a case ID."
                    )
                }
            )
            
        return attrs
        