from django.db import models
from accounts.models import Account
import uuid

class Conversion(models.Model):
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
        
        verbose_name = "Coversion"
        verbose_name_plural = "Conversions"
        
        
class Message(models.Model):
    
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        SYSTEM = "system", "System"
        TOOL = "tool", "Tool"
        
        
    id = models.UUIDField(primary_key = True, default=uuid.uuid4, editable=True)
    
    conversion = models.ForeignKey(Conversion, on_delete=models.CASCADE, related_name="messages")
    
    role = models.CharField(max_length=20, choices=Role.choices)
    
    content = models.JSONField(default=dict, blank=True, null=True)
    
    token_count = models.IntegerField(
        default=0,
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(
                fields=["conversation", "created_at"]
            )
        ]