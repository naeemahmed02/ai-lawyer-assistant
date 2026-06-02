from google import genai
from .base import BaseLLMProvider
from django.conf import settings


class GeminiAIProvider(BaseLLMProvider):
    def __init__(self):
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)

    async def generate(self, messages, model, **kwargs):
        response = await self.client.models.generate_content_stream(
            model=model, contents=""
        )
        return response
