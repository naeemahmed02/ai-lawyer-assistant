from rest_framework import serializers

from ...models import Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = (
            "id",
            "conversion",
            "role",
            "content",
            "token_count",
            "created_at",
        )

        read_only_fields = (
            "id",
            "token_count",
            "created_at",
        )

    def validate_role(self, value):
        valid_roles = {choice[0] for choice in Message.Role.choices}

        if value not in valid_roles:
            raise serializers.ValidationError("Invalid message role.")

        return value

    def validate_content(self, value):
        if value is None:
            raise serializers.ValidationError("Content cannot be null.")

        if not isinstance(value, dict):
            raise serializers.ValidationError("Content must be a JSON object.")

        return value

    def validate_token_count(self, value):
        if value < 0:
            raise serializers.ValidationError("Token count cannot be negative.")

        return value

    def validate(self, attrs):
        request = self.context.get("request")
        conversation = attrs.get("conversion")

        # Ensure the conversation belongs to the authenticated user
        if (
            request
            and request.user.is_authenticated
            and conversation.owner_id != request.user.id
        ):
            raise serializers.ValidationError(
                {
                    "conversion": (
                        "You do not have permission "
                        "to add messages to this conversation."
                    )
                }
            )

        return attrs
