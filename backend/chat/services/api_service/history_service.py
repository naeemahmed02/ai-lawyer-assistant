from ...models.message import Message

# class HistoryService:

#     MAX_HISTORY_MESSAGES = 20

#     def build_history(self, conversation):

#         messages = Message.objects.filter(conversation=conversation).order_by(
#             "-created_at"
#         )[: self.MAX_HISTORY_MESSAGES]

#         return [
#             {
#                 "role": msg.role,
#                 "content": msg.content.get("text", ""),  # type: ignore
#             }
#             for msg in reversed(messages)
#         ]


class RecentHistoryService:
    WINDOW = 6

    def get_recent(self, conversation):
        messages = Message.objects.filter(conversation=conversation).order_by(
            "-created_at"
        )[: self.WINDOW]

        return [
            {"role": m.role, "content": m.content.get("text", "")}  # type: ignore
            for m in reversed(messages)
        ]
