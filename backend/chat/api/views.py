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
from asgiref.sync import async_to_sync
from ..services.llm.exception import LLMGenerationError

logger = logging.getLogger(__name__)


class LegalChatAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from ..services.rag.rag_pipeline import RAGPipeline
        
        query = request.data.get("query")
        case_id = request.data.get("case_id")

        if not query or not query.strip():
            return Response({"error": "Query cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

        rag_pipeline = RAGPipeline()

        try:
            # Safely bridge the synchronous view to your async pipeline execution
            response = async_to_sync(rag_pipeline.run)(query, case_id=case_id)
            return Response(response, status=status.HTTP_200_OK)

        except LLMGenerationError as e:
            logger.error(f"Handled LLM Failure in View: {e}")
            return Response(
                {
                    "error": "The upstream AI generation provider failed.",
                    "details": str(e)
                }, 
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            logger.error(f"Unexpected error in pipeline: {e}")
            return Response(
                {"error": "An unexpected error occurred while processing your request."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
