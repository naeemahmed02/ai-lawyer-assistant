from typing import List, Optional


class ContextBuilder:
    """
    Build structured context for the LLM from multiple sources.

    Context sources:

    - Conversation summary
    - Semantic memories
    - Qdrant retrieval results
    """

    def build(
        self,
        summary: Optional[str] = None,
        memories: Optional[List[str]] = None,
        search_results=None,
    ) -> str:
        """
        Build contextual information for the LLM.

        Returns:
            A formatted context string.
        """

        sections: List[str] = []

        # Conversation summary
        if summary and summary.strip():
            sections.append(f"## Conversation Summary\n{summary.strip()}")

        # Semantic memories
        if memories:
            cleaned_memories = [
                memory.strip() for memory in memories if memory and memory.strip()
            ]

            if cleaned_memories:
                sections.append(
                    "## Relevant Previous Context\n"
                    + "\n".join(f"- {memory}" for memory in cleaned_memories)
                )

        # Legal reference material from Qdrant
        rag_chunks: List[str] = []

        if search_results:

            for point in search_results:

                payload = point.payload or {}

                text = payload.get("text")

                if text and text.strip():
                    rag_chunks.append(text.strip())

        if rag_chunks:
            sections.append("## Legal Reference Material\n" + "\n\n".join(rag_chunks))

        return "\n\n".join(sections)
