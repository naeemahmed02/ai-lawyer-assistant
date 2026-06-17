from typing import Any, Dict, List, Optional

from ..exception import PromptBuilderError


class PromptBuilder:
    """
    Production-grade prompt builder for Legal RAG systems.

    Key guarantees:
    - No hallucinated citations
    - Strict SRC-based grounding
    - Multi-document traceability
    - Provider-agnostic chat format
    """

    ALLOWED_ROLES = {"system", "user", "assistant", "tool"}

    # -------------------------------------------------------------
    # PUBLIC API
    # -------------------------------------------------------------
    def build(
        self,
        system_prompt: str,
        user_message: str,
        history: Optional[List[Dict[str, Any]]] = None,
        context: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, str]]:
        """
        Build provider-agnostic messages for LLM.
        """

        if not user_message or not user_message.strip():
            raise PromptBuilderError("User message cannot be empty.")

        messages: List[Dict[str, str]] = []

        # ---------------------------------------------------------
        # 1. SYSTEM INSTRUCTIONS (STATIC BEHAVIOR)
        # ---------------------------------------------------------
        if system_prompt and system_prompt.strip():
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt.strip(),
                }
            )

        # ---------------------------------------------------------
        # 2. STRUCTURED CONTEXT (RAG EVIDENCE LAYER)
        # ---------------------------------------------------------
        if context:
            formatted_context = self._format_context(context)

            messages.append(
                {
                    "role": "system",
                    "content": (
                        "You are given STRICT EVIDENCE SOURCES for answering.\n"
                        "Rules:\n"
                        "- Use ONLY these sources to answer.\n"
                        "- Every claim MUST cite SRC IDs.\n"
                        "- Do NOT invent or modify citations.\n"
                        "- If information is missing, say it is unavailable.\n\n"
                        f"{formatted_context}"
                    ),
                }
            )

        # ---------------------------------------------------------
        # 3. CONVERSATION HISTORY (OPTIONAL MEMORY)
        # ---------------------------------------------------------
        for message in history or []:
            self._validate_message(message)

            messages.append(
                {
                    "role": message["role"],
                    "content": str(message["content"]).strip(),
                }
            )

        # ---------------------------------------------------------
        # 4. USER QUERY (CURRENT INPUT)
        # ---------------------------------------------------------
        messages.append(
            {
                "role": "user",
                "content": user_message.strip(),
            }
        )

        return messages

    # -------------------------------------------------------------
    # CONTEXT FORMATTING (CRITICAL FOR RAG SAFETY)
    # -------------------------------------------------------------
    def _format_context(self, context: List[Dict[str, Any]]) -> str:
        """
        Convert retrieved chunks into deterministic citation-safe format.
        """

        blocks = []

        for i, item in enumerate(context, 1):

            doc_id = item.get("document_id", "unknown_doc")
            chunk_id = item.get("chunk_index", "unknown_chunk")
            text = item.get("text", "").strip()

            blocks.append(f"[SRC_{i} | doc:{doc_id} | chunk:{chunk_id}]\n" f"{text}")

        return "\n\n".join(blocks)

    # -------------------------------------------------------------
    # VALIDATION
    # -------------------------------------------------------------
    def _validate_message(self, message: Dict[str, Any]) -> None:

        if not isinstance(message, dict):
            raise PromptBuilderError("History message must be a dictionary.")

        role = message.get("role")
        content = message.get("content")

        if role not in self.ALLOWED_ROLES:
            raise PromptBuilderError(f"Invalid role: {role}")

        if not content or not str(content).strip():
            raise PromptBuilderError("Message content cannot be empty.")
