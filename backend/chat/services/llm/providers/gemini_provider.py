import logging
from google import genai

from ..schemas import LLMResponse
from ..exception import (
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderResponseError,
)
from .base import BaseLLMProvider

from django.conf import settings

logger = logging.getLogger(__name__)


class GeminiAIProvider(BaseLLMProvider):
    def __init__(self):
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)

    async def generate(self, messages, model, **kwargs):

        try:
            prompt = "\n".join(msg["content"] for msg in messages)

            response = self.client.models.generate_content_stream(
                model=model,
                contents=prompt,
            )

            if not response.text:
                raise ProviderResponseError("Empty response from Gemini")

            return LLMResponse(
                content=response.text,
                model=model,
                provider="gemini",
            )
        except Exception as exc:
            error = str(exc).lower()

            if "api key" or "api_key" in error:
                raise ProviderAuthenticationError(str(exc)) from exc

            raise ProviderConnectionError(str(exc)) from exc
