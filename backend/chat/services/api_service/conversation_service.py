from django.shortcuts import get_object_or_404
from ...models.conversation import Conversation
from ...models.message import Message


class ConversationService:

    def get_or_create(
        self,
        *,
        user,
        conversation_id,
        query,
        default_model,
    ):

        if conversation_id:
            return get_object_or_404(
                Conversation,
                id=conversation_id,
                owner=user,
            )

        return Conversation.objects.create(
            owner=user,
            title=query[:80],
            model_name=default_model,
        )

    def save_messages(
        self,
        *,
        conversation,
        query,
        response,
    ):

        Message.objects.create(
            conversation=conversation,
            role=Message.Role.USER,
            content={"text": query},
        )

        answer = response.get("answer")

        if isinstance(answer, dict):
            assistant_text = answer.get("content") or answer.get("text") or str(answer)
        else:
            assistant_text = str(answer)

        Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content={
                "text": assistant_text,
                "citations": response.get("citations", []),
            },
            token_count=response.get("usage", {}).get(
                "total_tokens",
                0,
            ),
        )
