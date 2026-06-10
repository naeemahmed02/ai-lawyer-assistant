from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, exceptions
from ..models.conversation import Conversation
from ..models.message import Message
from ..services.llm.exception import LLMGenerationError
from .serializers.conversation_serializers import ConversationSerializers
from .serializers.message_serializers import MessageSerializer
from django.db.models import QuerySet
from ..services.api_service.chat_service import LegalChatService

import logging

logger = logging.getLogger(__name__)


class LegalChatAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        query = request.data.get("query", "").strip()

        if not query:
            return Response(
                {"error": "Query cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            response = LegalChatService().process_chat(
                user=request.user,
                query=query,
                case_id=request.data.get("case_id"),
                conversation_id=request.data.get("conversation_id"),
            )

            return Response(response)

        except LLMGenerationError as exc:
            return Response(
                {
                    "error": "The AI provider failed to generate a response.",
                    "details": str(exc),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )


class CoversationViewSet(viewsets.ModelViewSet):

    serializer_class = ConversationSerializers
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet:  # type: ignore
        return Conversation.objects.filter(owner=self.request.user).all()

    def perform_create(self, serializer):

        conversation = serializer.save(owner=self.request.user)
        logger.info("Coversation saved")


class MessageViewSet(viewsets.ModelViewSet):

    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet:  # type: ignore
        return Message.objects.filter(conversation__owner=self.request.user)

    def perform_create(self, serializer):
        # Get the conversation from the validated data sent in the request
        conversation = serializer.validated_data.get("conversation")

        # Safety Check: Ensure the conversation actually belongs to the logged-in user
        if conversation and conversation.owner != self.request.user:
            raise exceptions.PermissionDenied(
                "You do not have permission to add a message to this conversation."
            )

        # 3. Save the message (it automatically links to the conversation)
        message = serializer.save()
        logger.info(f"Message saved for conversation {conversation.id}")
