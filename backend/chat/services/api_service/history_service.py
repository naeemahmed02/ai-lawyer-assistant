from ...models.message import Message


class HistoryService:

    MAX_HISTORY_MESSAGES = 20

    def build_history(self, conversation):

        messages = Message.objects.filter(conversation=conversation).order_by(
            "-created_at"
        )[: self.MAX_HISTORY_MESSAGES]

        return [
            {
                "role": msg.role,
                "content": msg.content.get("text", ""),
            }
            for msg in reversed(messages)
        ]
