from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

from ..models import Account


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for returning user profile information.
    """

    class Meta:
        model = Account
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "username",
            "phone_number",
            "role",
            "is_active",
            "is_staff",
            "date_joined",
        )

        # Fields that should not be editable
        read_only_fields = (
            "id",
            "email",
            "is_active",
            "is_staff",
            "date_joined",
        )


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    Handles:
    - Email uniqueness validation
    - Username uniqueness validation
    - Password validation
    - User creation
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        style={"input_type": "password"},
    )

    class Meta:
        model = Account
        fields = (
            "first_name",
            "last_name",
            "email",
            "username",
            "password",
        )

    def validate_email(self, value):
        """
        Validate that the email is unique.
        """
        email = value.lower().strip()

        if Account.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )

        return email

    def validate_username(self, value):
        """
        Validate that the username is unique.
        """
        username = value.strip()

        if Account.objects.filter(username=username).exists():
            raise serializers.ValidationError(
                "Username already exists. Please choose another one."
            )

        return username

    def validate_password(self, value):
        """
        Validate password using Django's built-in validators.
        """
        validate_password(value)
        return value

    def create(self, validated_data):
        """
        Create and return a new user.
        """

        user = Account.objects.create_user(
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            username=validated_data["username"],
            password=validated_data["password"],
        )

        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.

    Authenticates the user and returns:
    - User data
    - Access token
    - Refresh token
    """

    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        """
        Validate user credentials.
        """

        email = attrs.get("email")
        password = attrs.get("password")

        # Authenticate user
        user = authenticate(
            request=self.context.get("request"),
            email=email,
            password=password,
        )

        if not user:
            raise AuthenticationFailed("Invalid email or password.")

        if not user.is_active:
            raise AuthenticationFailed(
                "Your account is inactive. Please contact support."
            )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return {
            "user": UserSerializer(user).data,
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
        }


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing user password.

    Requires:
    - old_password
    - new_password
    - confirm_password

    Features:
    - Validates old password
    - Ensures new passwords match
    - Uses Django password validators
    """

    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
    )

    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )

    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
    )

    def validate_old_password(self, value):
        """
        Check whether the old password is correct.
        """

        user = self.context["request"].user

        if not user.check_password(value):
            raise serializers.ValidationError(
                "Old password is incorrect."
            )

        return value

    def validate(self, attrs):
        """
        Validate new password and confirm password.
        """

        new_password = attrs.get("new_password")
        confirm_password = attrs.get("confirm_password")

        # Check if passwords match
        if new_password != confirm_password:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )

        # Validate password using Django validators
        validate_password(new_password)

        return attrs

    def save(self, **kwargs):
        """
        Change the user's password.
        """

        user = self.context["request"].user
        new_password = self.validated_data["new_password"]

        # Set new password securely
        user.set_password(new_password)
        user.save(update_fields=["password"])

        return user