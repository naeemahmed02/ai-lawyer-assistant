from django.db.models import QuerySet
from rest_framework.viewsets import ModelViewSet
from .serializers import DocumentSerializer
from rest_framework.permissions import IsAuthenticated
from ..models import Document
from ..tasks.ingestion_tasks import process_document_task
import logging

logger = logging.getLogger(__name__)


class DocumentViewSet(ModelViewSet):

    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Document]:
        return Document.objects.filter(owner=self.request.user).all()

    def perform_create(self, serializer):
        """
        Save document and trigger async ingestion pipeline.
        """

        document = serializer.save(owner=self.request.user)
        logger.info("Document saved")
        # Trigger async ingestion pipeline
        process_document_task.delay(str(document.id))
        logger.info("process started")
