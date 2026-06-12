from django.db import models
from .case_model import Case
import uuid


class Party(models.Model):
    class Role(models.TextChoices):

        PLAINTIFF = "plaintiff"
        DEFENDANT = "defendant"
        PETITIONER = "petitioner"
        RESPONDENT = "respondent"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="parties")

    name = models.CharField(max_length=255)

    role = models.CharField(max_length=30, choices=Role.choices)

    advocate_name = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return f"{self.name} - {self.case}"
