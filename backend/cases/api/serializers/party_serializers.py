from rest_framework import serializers
from ...models import party_model


class PartySerializer(serializers.ModelSerializer):

    class Meta:
        model = party_model.Party
        fields = (
            "id",
            "case",
            "name",
            "role",
            "advocate_name",
        )

        read_only_fields = ("id",)

    def validate_name(self, value):
        """
        Validate party name.
        """

        value = value.strip()

        if not value:
            raise serializers.ValidationError("Party name cannot be empty.")

        if len(value) < 3:
            raise serializers.ValidationError(
                "Party name must contain at least 3 characters."
            )

        if len(value) > 255:
            raise serializers.ValidationError(
                "Party name cannot exceed 255 characters."
            )

        return value

    def validate_advocate_name(self, value):
        """
        Validate advocate name.
        """

        if not value:
            return value

        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError(
                "Advocate name must contain at least 3 characters."
            )

        if len(value) > 255:
            raise serializers.ValidationError(
                "Advocate name cannot exceed 255 characters."
            )

        return value

    def validate(self, attrs):
        """
        Cross-field validation.
        """

        case = attrs.get("case", getattr(self.instance, "case", None))

        role = attrs.get("role", getattr(self.instance, "role", None))

        name = attrs.get("name", getattr(self.instance, "name", None))

        # Prevent duplicate party-role combinations
        queryset = party_model.Party.objects.filter(
            case=case, role=role, name__iexact=name
        )

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                {"name": (f"{role.title()} '{name}' " "already exists in this case.")}
            )

        return attrs

    def create(self, validated_data):
        """
        Extra create logic if needed later.
        """
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Extra update logic if needed later.
        """
        return super().update(instance, validated_data)
