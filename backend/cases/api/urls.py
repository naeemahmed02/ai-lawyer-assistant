from rest_framework.routers import DefaultRouter
from .views import CaseViewSet, PartyViewSet

router = DefaultRouter()

router.register("cases", CaseViewSet, basename="case")

router.register("parties", PartyViewSet, basename="party")

urlpatterns = router.urls
