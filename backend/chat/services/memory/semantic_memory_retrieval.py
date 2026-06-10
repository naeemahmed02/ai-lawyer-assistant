from django.db.models import F
from pgvector.django import CosineDistance
from ...models.semantic_memory import ConversationMemory


class MemoryRetriever:

    def get_relevant(self, conversation, query_embedding, top_k):

        return (
            ConversationMemory.objects.filter(conversation=conversation)
            .annotate(distance=CosineDistance("embedding", query_embedding))
            .order_by("distance")[:top_k]
        )
