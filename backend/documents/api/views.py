from django.db.models import QuerySet
from rest_framework.viewsets import ModelViewSet
from .serializers import DocumentSerializer
from rest_framework.permissions import IsAuthenticated
from ..models import Document


class DocumentViewSet(ModelViewSet):

    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Document]:
        return Document.objects.filter(owner=self.request.user).all()
