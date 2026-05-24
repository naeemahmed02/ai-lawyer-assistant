from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
import logging
from rest_framework.throttling import UserRateThrottle
from .serializers import (RegisterSerializer, UserLoginSerializer, UserSerializer)
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status



logger = logging.getLogger(__name__)

# custom throttle for authentication endpoint
class AuthRateThrottle(UserRateThrottle):
    scope = "auth"


class UserRegistrationAPIView(APIView):
    
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]
    
    def post(self, request):
        serializer = RegisterSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            user = serializer.save()
            
        logger.info(f"User registered successfully: {user.id}")
        
        return Response(
            {
                "success": True,
                "message": "User registered successfully.",
                "data": UserSerializer(user).data
            },
            status=status.HTTP_201_CREATED
        )
        