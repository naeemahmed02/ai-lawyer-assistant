from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import CoversationViewSet, LegalChatAPIView, MessageViewSet

router = DefaultRouter()
router.register(r"conversations", CoversationViewSet, basename="conversations")
router.register(r"chat-messages", MessageViewSet, basename="chat-messages")

# 1. Start with your standard view paths in a list
urlpatterns = [
    path("legal-chat/", LegalChatAPIView.as_view(), name="legal-chat"),
]

# 2. Append the router's auto-generated URLs to that list
urlpatterns += router.urls
