from dataclasses import dataclass
from typing import Optional


@dataclass
class TokenUsage:
    prompt_token: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    usage: Optional[TokenUsage] = None
