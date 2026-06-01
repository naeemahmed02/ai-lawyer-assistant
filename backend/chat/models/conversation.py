from django.db import models
from accounts.models import Account
import uuid

class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    owner = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="conversions")
    
    title = models.CharField(max_length=400, blank=True)
    
    summary = models.JSONField(default=dict, blank=True, null=True)
    
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    is_archived = models.BooleanField(default=False)
    
    class Meta:
        ordering = ["-updated_at"]
        
        verbose_name = "conversation"
        verbose_name_plural = "conversations"
        