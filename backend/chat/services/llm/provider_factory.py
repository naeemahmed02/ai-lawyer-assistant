from .model_registry import MODEL_REGISTRY
from .providers.gemini_provider import GeminiAIProvider

from .exception import ModelNotFoundError, ProviderNotFoundError


class ProviderFactory:

    _providers = {
        "gemini": GeminiAIProvider(),
    }

    @classmethod
    def get_provider(cls, model_name):
        config = MODEL_REGISTRY.get(model_name)

        if not config:
            raise ModelNotFoundError(f"Unknown model: {model_name}")

        provider_name = config["provider"]

        provider = cls._providers.get(provider_name)

        if not provider:
            raise ProviderNotFoundError(f"Unknown provider: {provider_name}")

        return provider
