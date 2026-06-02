from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):

    @abstractmethod
    async def generate(self, messages: list[dict], **kwargs):
        pass
