from rest_framework import serializers
from ...models import case_model


class CaseSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = case_model.Case
        fields = (
            "id",
            "title",
            "description",
            "case_type",
            "status",
            "jurisdiction",
            "court_name",
            "created_by",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "created_by",
            "created_at",
            "updated_at",
        )

    def validate_title(self, value):
        """
        Validate case title.
        """
        value = value.strip()

        if not value:
            raise serializers.ValidationError("Case title cannot be empty.")

        if len(value) < 5:
            raise serializers.ValidationError(
                "Case title must contain at least 5 characters."
            )

        if len(value) > 255:
            raise serializers.ValidationError(
                "Case title cannot exceed 255 characters."
            )

        return value

    def validate_description(self, value):
        """
        Validate description.
        """
        if value:
            value = value.strip()

            if len(value) < 20:
                raise serializers.ValidationError(
                    "Description must contain at least 20 characters."
                )

        return value

    def validate_jurisdiction(self, value):
        """
        Normalize jurisdiction.
        """
        return value.strip() if value else value

    def validate_court_name(self, value):
        """
        Normalize court name.
        """
        return value.strip() if value else value

    def validate(self, attrs):
        """
        Cross-field validation.
        """

        case_type = attrs.get("case_type", getattr(self.instance, "case_type", None))

        court_name = attrs.get("court_name", getattr(self.instance, "court_name", ""))

        jurisdiction = attrs.get(
            "jurisdiction", getattr(self.instance, "jurisdiction", "")
        )

        status = attrs.get("status", getattr(self.instance, "status", None))

        # Court name required for active cases
        if status != case_model.Case.Status.CLOSED and not court_name:
            raise serializers.ValidationError(
                {
                    "court_name": (
                        "Court name is required for open or " "under-review cases."
                    )
                }
            )

        # Jurisdiction required for legal cases
        if not jurisdiction:
            raise serializers.ValidationError(
                {"jurisdiction": ("Jurisdiction is required.")}
            )

        # Example business rule
        if case_type == case_model.Case.CaseType.CONSTITUTIONAL and not court_name:
            raise serializers.ValidationError(
                {"court_name": ("Court name is required for constitutional cases.")}
            )

        return attrs

    def create(self, validated_data):
        """
        Automatically assign creator.
        """

        request = self.context.get("request")

        if request and request.user.is_authenticated:
            validated_data["created_by"] = request.user

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Prevent creator modification.
        """

        validated_data.pop("created_by", None)

        return super().update(instance, validated_data)
