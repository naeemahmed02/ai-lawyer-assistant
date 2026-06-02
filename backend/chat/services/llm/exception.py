class LLMException(Exception):
    """Base LLM exception."""


class ModelNotFoundError(LLMException):
    """Requested model does not exist in registry."""


class ProviderNotFoundError(LLMException):
    """Provider not registered."""


class ProviderConnectionError(LLMException):
    """Could not connect to provider."""


class ProviderAuthenticationError(LLMException):
    """Invalid API key or authentication failure."""


class ProviderRateLimitError(LLMException):
    """Provider rate limit exceeded."""


class ProviderResponseError(LLMException):
    """Invalid response from provider."""


class LLMGenerationError(LLMException):
    """Generation failed after retries."""
