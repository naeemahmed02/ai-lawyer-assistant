from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter

from django_filters.rest_framework import DjangoFilterBackend
from .serializers.case_serializers import CaseSerializer
from .serializers.party_serializers import PartySerializer

from ..models.case_model import Case
from ..models.party_model import Party


class CaseViewSet(viewsets.ModelViewSet):
    """
    CRUD for legal cases.
    """

    serializer_class = CaseSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = (
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    )

    filterset_fields = (
        "status",
        "case_type",
    )

    search_fields = (
        "title",
        "description",
        "court_name",
        "jurisdiction",
    )

    ordering_fields = (
        "created_at",
        "updated_at",
        "title",
    )

    ordering = ("-created_at",)

    def get_queryset(self):  # type: ignore
        """
        Return only current user's cases.
        """

        return (
            Case.objects.select_related("created_by")
            .prefetch_related("parties")
            .filter(created_by=self.request.user)
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class PartyViewSet(viewsets.ModelViewSet):
    """
    CRUD for case parties.
    """

    serializer_class = PartySerializer
    permission_classes = [IsAuthenticated]

    filter_backends = (
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    )

    filterset_fields = (
        "role",
        "case",
    )

    search_fields = (
        "name",
        "advocate_name",
    )

    ordering_fields = (
        "name",
        "role",
    )

    ordering = ("name",)

    def get_queryset(self):  # type: ignore
        """
        Only parties belonging to
        cases owned by current user.
        """

        return Party.objects.select_related(
            "case",
            "case__created_by",
        ).filter(case__created_by=self.request.user)
