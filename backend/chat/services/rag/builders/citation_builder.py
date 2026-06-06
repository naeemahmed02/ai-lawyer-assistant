from typing import List


class CitationBuilder:
    """Create legal citation from retrieval results"""

    def build(self, retrieval_result):

        if not retrieval_result:
            return ""

        citations: List[dict] = []

        for result in retrieval_result:

            payload = result.payload

            citations.append(
                {
                    "document_id": payload.get("document_id"),
                    "case_id": payload.get("case_id"),
                    "chunk_index": payload.get("chunk_index"),
                }
            )
        return citations
