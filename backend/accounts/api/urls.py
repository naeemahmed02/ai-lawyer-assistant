from django.urls import path
from .views import (
    UserLoginAPIView,
    UserRegistrationAPIView,
    ChangePasswordAPIView
)

urlpatterns = [
    path('login', UserLoginAPIView.as_view(), name='user-login'),
    path('register', UserRegistrationAPIView.as_view(), name='user-registrations'),
    path('change-password', ChangePasswordAPIView.as_view(), name='change-password'),
]
