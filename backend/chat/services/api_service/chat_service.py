from django.db import transaction
from django.db import DatabaseError
from .conversation_service import ConversationService
from .history_service import HistoryService
from .rag_service import RagService


class LegalChatService:

    DEFAULT_MODEL = "gemini-2.5-flash"

    def process_chat(
        self,
        *,
        user,
        query,
        case_id=None,
        conversation_id=None,
    ):

        with transaction.atomic():

            conversation = ConversationService().get_or_create(
                user=user,
                conversation_id=conversation_id,
                query=query,
                default_model=self.DEFAULT_MODEL,
            )

            history = HistoryService().build_history(conversation)

            response = RagService().generate(
                query=query,
                case_id=case_id,
                history=history,
            )

            ConversationService().save_messages(
                conversation=conversation,
                query=query,
                response=response,
            )

            return {
                **response,
                "conversation_id": str(conversation.id),
            }
