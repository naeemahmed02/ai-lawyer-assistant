import logging

from django.db import transaction
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    ChangePasswordSerializer,
    RegisterSerializer,
    UserLoginSerializer,
    UserSerializer,
)

# Configure module-level logger
logger = logging.getLogger(__name__)



# Custom Throttle Class
class AuthRateThrottle(UserRateThrottle):
    """
    Custom throttle class for authentication endpoints.

    This helps prevent:
    - Brute-force attacks
    - Login abuse
    - Excessive API requests

    Configure the rate in settings.py:

    REST_FRAMEWORK = {
        "DEFAULT_THROTTLE_RATES": {
            "auth": "5/min"
        }
    }
    """

    scope = "auth"


# User Registration API
class UserRegistrationAPIView(APIView):
    """
    API endpoint for user registration.

    Permissions:
        - Public access allowed

    Throttling:
        - Rate limited using AuthRateThrottle

    Request Body:
    {
        "email": "user@example.com",
        "password": "secure_password",
        ...
    }

    Response:
    {
        "success": true,
        "message": "User registered successfully.",
        "data": {...}
    }
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        """
        Register a new user.
        """

        serializer = RegisterSerializer(data=request.data)

        # Validate incoming request data
        serializer.is_valid(raise_exception=True)

        try:
            # Ensure DB consistency
            with transaction.atomic():
                user = serializer.save()

            logger.info(
                "User registered successfully | user_id=%s",
                user.id
            )

            return Response(
                {
                    "success": True,
                    "message": "User registered successfully.",
                    "data": UserSerializer(user).data,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as exc:
            logger.exception(
                "User registration failed | error=%s",
                str(exc)
            )

            return Response(
                {
                    "success": False,
                    "message": "Registration failed.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# User Login API
class UserLoginAPIView(APIView):
    """
    API endpoint for user login.

    Permissions:
        - Public access allowed

    Throttling:
        - Rate limited using AuthRateThrottle

    Request Body:
    {
        "email": "user@example.com",
        "password": "password"
    }

    Response:
    {
        "success": true,
        "message": "Login successful.",
        "data": {
            "access": "...",
            "refresh": "...",
            "user": {...}
        }
    }
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        """
        Authenticate user and return JWT tokens.
        """

        serializer = UserLoginSerializer(data=request.data)

        # Validate login credentials
        serializer.is_valid(raise_exception=True)

        user_data = serializer.validated_data.get("user")

        logger.info(
            "User login successful | user_id=%s",
            user_data.get("id"),
        )

        return Response(
            {
                "success": True,
                "message": "Login successful.",
                "data": serializer.validated_data,
            },
            status=status.HTTP_200_OK,
        )



# Change Password API
class ChangePasswordAPIView(APIView):
    """
    API endpoint for changing user password.

    Permissions:
        - Authentication required

    Throttling:
        - Rate limited using AuthRateThrottle

    Request Body:
    {
        "old_password": "old_password",
        "new_password": "new_password"
    }

    Response:
    {
        "success": true,
        "message": "Password changed successfully."
    }
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [AuthRateThrottle]

    def put(self, request):
        """
        Change authenticated user's password.
        """

        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )

        # Validate password data
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                serializer.save()

            logger.info(
                "Password changed successfully | user_id=%s",
                request.user.id,
            )

            return Response(
                {
                    "success": True,
                    "message": "Password changed successfully.",
                },
                status=status.HTTP_200_OK,
            )

        except Exception as exc:
            logger.exception(
                "Password change failed | user_id=%s | error=%s",
                request.user.id,
                str(exc),
            )

            return Response(
                {
                    "success": False,
                    "message": "Unable to change password.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )



# Logout API
class LogoutView(APIView):
    """
    API endpoint for user logout.

    This endpoint blacklists the refresh token
    to invalidate future token refresh attempts.

    Permissions:
        - Authentication required

    Throttling:
        - Rate limited using AuthRateThrottle

    Request Body:
    {
        "refresh": "refresh_token"
    }

    Response:
    {
        "success": true,
        "message": "Logged out successfully."
    }
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        """
        Logout user by blacklisting refresh token.
        """

        refresh_token = request.data.get("refresh")

        # Validate refresh token existence
        if not refresh_token:
            logger.warning(
                "Logout attempt without refresh token | user_id=%s",
                request.user.id,
            )

            return Response(
                {
                    "success": False,
                    "message": "Refresh token is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Parse refresh token
            token = RefreshToken(refresh_token)

            # Validate token ownership
            if token["user_id"] != request.user.id:

                logger.warning(
                    (
                        "Token ownership mismatch "
                        "| request_user_id=%s | token_user_id=%s"
                    ),
                    request.user.id,
                    token["user_id"],
                )

                return Response(
                    {
                        "success": False,
                        "message": (
                            "Token does not belong to this user."
                        ),
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Blacklist token
            token.blacklist()

            logger.info(
                "User logged out successfully | user_id=%s",
                request.user.id,
            )

            return Response(
                {
                    "success": True,
                    "message": "Logged out successfully.",
                },
                status=status.HTTP_205_RESET_CONTENT,
            )

        except TokenError:
            logger.warning(
                (
                    "Invalid or expired refresh token used "
                    "| user_id=%s"
                ),
                request.user.id,
            )

            return Response(
                {
                    "success": False,
                    "message": "Invalid or expired token.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as exc:
            logger.exception(
                "Logout failed | user_id=%s | error=%s",
                request.user.id,
                str(exc),
            )

            return Response(
                {
                    "success": False,
                    "message": "Logout failed.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )