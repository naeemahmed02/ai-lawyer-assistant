import asyncio
import logging
from typing import List

from .provider_factory import ProviderFactory
from .schemas import LLMResponse

from .exception import LLMGenerationError

logger = logging.getLogger(__name__)


class LLMService:

    MAX_RETRIES = 3

    async def generate(
        self, model_name: str, messages: List[dict], **kwargs
    ) -> LLMResponse:

        provider = ProviderFactory.get_provider(model_name=model_name)

        for attempt in range(self.MAX_RETRIES):

            try:
                logger.info(
                    "llm_request",
                    extra={
                        "model": model_name,
                        "attempt": attempt + 1,
                    },
                )

                response = provider.generate(model=model_name, messages=messages, **kwargs)

                logger.info("llm_success", extra={"model": model_name})

                return response

            # ... inside LLMService.generate loops ...
            except Exception as e: # <-- Catch the actual error object
                logger.exception(
                    "llm_failure",
                    extra={
                        "model": model_name,
                        "attempt": attempt + 1,
                    },
                )

                if attempt == self.MAX_RETRIES - 1:
                    # 'from e' links the original exception traceback to your custom error
                    raise LLMGenerationError(f"Generation failed model: {model_name}. Reason: {str(e)}") from e

                await asyncio.sleep(2**attempt)
