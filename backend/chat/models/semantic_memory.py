from pgvector.django import VectorField
from django.db import models
from .conversation import Conversation


class ConversationMemory(models.Model):

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    content = models.TextField()
    embedding = VectorField(dimensions=3072)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Converastion Memory: {self.conversation.id}"

    class Meta:
        verbose_name = "Conversation Memory"
        verbose_name_plural = "Conversation Memories"
