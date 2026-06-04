from rest_framework import viewsets, status
from .serializers.conversation_serializers import ConversationSerializers
from rest_framework.permissions import IsAuthenticated
from django.db.models import QuerySet
from ..models.conversation import Conversation
import logging
from ..models.message import Message
from .serializers.message_serializers import MessageSerializer
from rest_framework.views import APIView
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class LegalChatAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from ..services.rag.rag_pipeline import RAGPipeline
        # get the query
        query = request.data.get("query")

        case_id = request.data.get("case_id")

        rag_pipeline = RAGPipeline()

        response = rag_pipeline.run(query)

        return Response(response)


class CoversationViewSet(viewsets.ModelViewSet):

    serializer_class = ConversationSerializers
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return Conversation.objects.filter(owner=self.request.user).all()

    def perform_create(self, serializer):

        conversation = serializer.save(owner=self.request.user)
        logger.info("Coversation saved")


class MessageViewSet(viewsets.ModelViewSet):

    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return Message.objects.filter(owner=self.request.user).all()

    def perform_create(self, serializer):

        message = serializer.save(owner=self.request.user)
        logger.info("Message saved")
