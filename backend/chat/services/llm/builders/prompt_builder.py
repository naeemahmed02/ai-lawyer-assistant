from typing import List, Dict, Any

from ..exception import PromptBuilderError


class PromptBuilder:
    """
    Responsible for constructing a provider-agnostic chat prompt.

    The prompt builder combines:

    - System instructions
    - Conversation history
    - Current user message

    into a normalized list of chat messages that can be
    consumed by the LLM service and translated by the
    provider layer (Gemini, OpenAI, Anthropic, etc.).

    Example:
        builder = PromptBuilder()

        messages = builder.build(
            system_prompt="You are a helpful assistant.",
            history=[
                {
                    "role": "user",
                    "content": "Hello"
                },
                {
                    "role": "assistant",
                    "content": "Hi, how can I help?"
                }
            ],
            user_message="Explain transformers."
        )

    Returns:
        [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": "Hello"
            },
            {
                "role": "assistant",
                "content": "Hi, how can I help?"
            },
            {
                "role": "user",
                "content": "Explain transformers."
            }
        ]
    """

    ALLOWED_ROLES = {
        "system",
        "user",
        "assistant",
        "tool",
    }

    def build(
        self,
        system_prompt: str | None,
        history: List[Dict[str, Any]] | None,
        user_message: str,
    ) -> List[Dict[str, str]]:
        """
        Build a normalized list of chat messages.

        Args:
            system_prompt:
                Optional system-level instruction that guides
                model behavior.

            history:
                Previous conversation messages.

            user_message:
                Latest message from the user.

        Returns:
            List of normalized chat messages.

        Raises:
            PromptBuilderError:
                If the user message is empty or history
                contains invalid messages.
        """

        if not user_message or not user_message.strip():
            raise PromptBuilderError("User message cannot be empty.")

        history = history or []

        messages: List[Dict[str, str]] = []

        if system_prompt and system_prompt.strip():
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt.strip(),
                }
            )

        for message in history:
            self._validate_message(message)

            messages.append(
                {
                    "role": message["role"],
                    "content": str(message["content"]).strip(),
                }
            )

        messages.append(
            {
                "role": "user",
                "content": user_message.strip(),
            }
        )

        return messages

    def _validate_message(
        self,
        message: Dict[str, Any],
    ) -> None:
        """
        Validate a history message.

        Args:
            message:
                Chat message dictionary.

        Raises:
            PromptBuilderError:
                If the message structure is invalid.
        """

        if not isinstance(message, dict):
            raise PromptBuilderError("History message must be a dictionary.")

        role = message.get("role")
        content = message.get("content")

        if role not in self.ALLOWED_ROLES:
            raise PromptBuilderError(f"Invalid role: {role}")

        if not content:
            raise PromptBuilderError("Message content cannot be empty.")
