import logging
from google import genai
from django.conf import settings

from ..schemas import LLMResponse
from ..exception import (
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderResponseError,
)
from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class GeminiAIProvider(BaseLLMProvider):
    def __init__(self):
        # Initialize client with the Django settings key managed by your .env configuration
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)

    def generate(self, messages, model, **kwargs):
        """
        Synchronously generates content from the Gemini API to match
        the synchronous Django view and RAG pipeline architectures.
        """
        try:
            # Reconstruct the message prompts into a single payload string
            prompt = "\n".join(msg["content"] for msg in messages)

            # Use the official synchronous generate_content method instead of streaming
            response = self.client.models.generate_content(
                model=model,
                contents=prompt,
            )

            if not response.text:
                raise ProviderResponseError("Empty response received from Gemini.")

            return LLMResponse(
                content=response.text,
                model=model,
                provider="gemini",
            )

        except Exception as exc:
            error_message = str(exc).lower()

            # FIX: Explicit evaluation so other exceptions aren't swallowed as Auth errors
            if "api key" in error_message or "api_key" in error_message:
                raise ProviderAuthenticationError(
                    f"Invalid Google API Key configuration: {exc}"
                ) from exc

            raise ProviderConnectionError(
                f"Gemini API Connection failed: {exc}"
            ) from exc
