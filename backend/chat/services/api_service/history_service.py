from ...models.message import Message


class RecentHistoryService:
    WINDOW = 6

    def get_recent(self, conversation):
        messages = list(
            Message.objects.filter(conversation=conversation)
            .only("role", "content", "created_at")
            .order_by("-created_at")[: self.WINDOW]
        )

        return [
            {
                "role": m.role,
                "content": m.content.get("text", ""),  # type: ignore
            }
            for m in reversed(messages)
        ]
