from ...models.conversation import Conversation
from ...models.message import Message

from rest_framework import serializers


class ConversationSerializers(serializers.ModelSerializer):

    class Meta:
        model = Conversation
        fields = (
            "id",
            "title",
            "model_name",
            "summary",
            "is_archived",
            "created_at",
            "updated_at",
        )

        read_only_fields = ("id", "created_at", "updated_at")

    def validate_title(self, value):
        value = value.strip()

        if len(value) > 400:
            raise serializers.ValidationError("Title cannot exceed 400 characters.")
        return value

    def validate_model_name(self, value):
        value = value.strip()

        allowed_models = {
            "gemini-2.5-flash",
            "gemini-2.5-pro",
        }

        if value not in allowed_models:
            raise serializers.ValidationError(
                f"Unsupported model. Allowed models: {', '.join(allowed_models)}"
            )

        return value

    def validate_summary(self, value):
        if value is None:
            return {}

        if not isinstance(value, dict):
            raise serializers.ValidationError("Summary must be a json object")

        return value

    def validate(self, attrs):
        title = attrs.get("title", "")

        if title and len(title.strip()) < 3:
            raise serializers.ValidationError(
                {"title": "Title must contain at least 3 characters"}
            )
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")

        # Remove 'owner' from validated_data if it exists to avoid the duplicate argument error
        validated_data.pop("owner", None)

        return Conversation.objects.create(owner=request.user, **validated_data)
