from django.db import models
from accounts.models import Account
import uuid


class Case(models.Model):

    class CaseType(models.TextChoices):
        CIVIL = "civil"
        CRIMINAL = "criminal"
        FAMILY = "family"
        CORPORATE = "corporate"
        CONSTITUTIONAL = "constitutional"

    class Status(models.TextChoices):
        OPEN = "open"
        UNDER_REVIEW = "under_review"
        CLOSED = "closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    case_type = models.CharField(max_length=30, choices=CaseType.choices)
    status = models.CharField(
        max_length=30, choices=Status.choices, default=Status.OPEN
    )

    jurisdiction = models.CharField(max_length=255, blank=True)  # Pakistan courts
    court_name = models.CharField(max_length=255, blank=True)

    created_by = models.ForeignKey(Account, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.status} - {self.title}"
