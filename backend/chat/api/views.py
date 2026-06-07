from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from asgiref.sync import async_to_sync
from django.shortcuts import get_object_or_404
from django.db import DatabaseError
from rest_framework import viewsets, exceptions
from ..models.conversation import Conversation
from ..models.message import Message
from ..services.rag.rag_pipeline import RAGPipeline
from ..services.llm.exception import LLMGenerationError
from .serializers.conversation_serializers import ConversationSerializers
from .serializers.message_serializers import MessageSerializer
from django.db.models import QuerySet

import logging

logger = logging.getLogger(__name__)


class LegalChatAPIView(APIView):
    permission_classes = [IsAuthenticated]

    DEFAULT_MODEL = "gemini-2.5-flash"

    def post(self, request):

        query = request.data.get("query", "").strip()
        case_id = request.data.get("case_id")
        conversation_id = request.data.get("conversation_id")

        if not query:
            return Response(
                {"error": "Query cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            # Get existing conversation or create new one
            if conversation_id:

                conversation = get_object_or_404(
                    Conversation.objects.only(
                        "id",
                        "owner",
                        "title",
                        "model_name",
                    ),
                    id=conversation_id,
                    owner=request.user,
                )

            else:

                conversation = Conversation.objects.create(
                    owner=request.user,
                    title=query[:80],
                    model_name=self.DEFAULT_MODEL,
                )

            # Save user message
            Message.objects.create(
                conversation=conversation,
                role=Message.Role.USER,
                content={
                    "text": query,
                },
            )

            # Execute RAG Pipeline
            rag_pipeline = RAGPipeline()

            response = async_to_sync(rag_pipeline.run)(
                query=query,
                case_id=case_id,
            )

            if not response:
                raise LLMGenerationError("Empty response received from pipeline.")

            # Extract response metadata safely
            answer = response.get("answer", "")

            citations = response.get(
                "citations",
                [],
            )

            usage = response.get(
                "usage",
                {},
            )

            total_tokens = usage.get(
                "total_tokens",
                0,
            )

            model_name = response.get(
                "model",
                self.DEFAULT_MODEL,
            )

            # Save assistant message
            Message.objects.create(
                conversation=conversation,
                role=Message.Role.ASSISTANT,
                content={
                    "text": answer,
                    "citations": citations,
                },
                token_count=total_tokens,
            )

            # Update conversation metadata
            update_fields = []

            if conversation.model_name != model_name:
                conversation.model_name = model_name
                update_fields.append("model_name")

            if conversation.title == "Unknown":
                conversation.title = query[:80]
                update_fields.append("title")

            if update_fields:
                conversation.save(update_fields=update_fields)

            # Return response
            return Response(
                {
                    **response,
                    "conversation_id": str(conversation.id),
                },
                status=status.HTTP_200_OK,
            )

        except LLMGenerationError as exc:

            logger.exception("LLM generation failed.")

            if "conversation" in locals():

                Message.objects.create(
                    conversation=conversation,
                    role=Message.Role.SYSTEM,
                    content={
                        "error": str(exc),
                    },
                )

            return Response(
                {
                    "error": ("The AI provider failed " "to generate a response."),
                    "details": str(exc),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        except DatabaseError:

            logger.exception("Database error occurred.")

            return Response(
                {"error": ("A database error occurred.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        except Exception:

            logger.exception("Unexpected error.")

            return Response(
                {"error": ("An unexpected error occurred.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
