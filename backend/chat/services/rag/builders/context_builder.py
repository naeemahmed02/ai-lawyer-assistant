from typing import List, Optional, Dict, Any


class ContextBuilder:
    """
    Production-grade structured context builder for Legal RAG.

    Output MUST remain structured (NO string flattening).
    """

    def build(
        self,
        summary: Optional[str] = None,
        memories: Optional[List[Any]] = None,
        search_results: Optional[List[Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Returns:
            List of structured context objects for PromptBuilder.
        """

        context: List[Dict[str, Any]] = []

        # 1. Conversation Summary
        if summary and summary.strip():
            context.append(
                {
                    "document_id": "conversation_summary",
                    "chunk_index": 0,
                    "text": summary.strip(),
                    "source_type": "summary",
                }
            )

        # 2. Semantic Memories
        if memories:
            for i, memory in enumerate(memories):
                if not memory:
                    continue

                text = getattr(memory, "content", str(memory)).strip()

                if text:
                    context.append(
                        {
                            "document_id": "memory",
                            "chunk_index": i,
                            "text": text,
                            "source_type": "memory",
                        }
                    )

        # 3. Qdrant Search Results (MOST IMPORTANT)
        if search_results:
            for i, point in enumerate(search_results):

                payload = getattr(point, "payload", {}) or {}

                text = payload.get("text", "").strip()

                if not text:
                    continue

                context.append(
                    {
                        "document_id": payload.get("document_id", "unknown_doc"),
                        "chunk_index": payload.get("chunk_index", i),
                        "text": text,
                        "source_type": "qdrant",
                    }
                )

        return context
