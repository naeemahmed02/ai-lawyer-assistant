from abc import ABC, abstractmethod
from ..schemas import LLMResponse


class BaseLLMProvider(ABC):

    @abstractmethod
    async def generate(self, messages: list[dict], **kwargs) -> LLMResponse:
        pass
