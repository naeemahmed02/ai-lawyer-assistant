from django.db import models
from .conversation import Conversation


class ConversationSummary(models.Model):

    conversation = models.OneToOneField(Conversation, on_delete=models.CASCADE)
    summary = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Converastion Summary: {self.conversation.id}"

    class Meta:
        verbose_name = "Conversation Summary"
        verbose_name_plural = "Conversation Summaries"
