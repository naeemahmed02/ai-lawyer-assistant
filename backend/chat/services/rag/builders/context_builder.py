from typing import List


class ContextBuilder:
    """
    Convert retrieval results into LMM  context.
    """

    def _build_context(self, search_results) -> str:
        """
        Convert Qdrant results into prompt context.
        """

        if not search_results:
            return ""

        chunks: List[str] = []

        for point in search_results:

            payload = point.payload or {}

            text = payload.get("text")

            if text:
                chunks.append(text)

        return "\n\n".join(chunks)
