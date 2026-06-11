from ...models.message import Message
from ...services.llm.service import LLMService


class SummaryService:

    def __init__(self):
        self.llm_service = LLMService()

    def generate_summary(self, conversation) -> str:

        messages = Message.objects.filter(conversation=conversation).order_by(
            "-created_at"
        )[:3]

        text = "\n".join(f"{m.role}: {m.content.get('text', '')}" for m in messages)  # type: ignore

        llm_messages = [
            {
                "role": "system",
                "content": (
                    "You are a legal assistant. Generate a concise summary "
                    "of the legal conversation, highlighting key facts, "
                    "issues, advice, and outcomes."
                ),
            },
            {
                "role": "user",
                "content": text,
            },
        ]

        response = self.llm_service.generate(
            model_name="gemini-2.5-flash",
            messages=llm_messages,
        )

        return response.content
