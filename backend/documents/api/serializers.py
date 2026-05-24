from rest_framework import serializers
from ..models import Document
import magic

ALLOWED_MIME_TYPES = [
    "application/pdf",
    "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]


class DocumentSerializers(serializers.ModelSerializer):
    
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
        
        if file.size == 0:
            raise serializers.ValidationError("File must not be empty")
        pass
        