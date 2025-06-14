from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import OrganizationViewSet, MembershipViewSet

router = DefaultRouter()
router.register("organizations", OrganizationViewSet, basename="organization")
router.register("memberships", MembershipViewSet, basename="membership")

app_name = "organizations"

urlpatterns = [
    path("", include(router.urls)),
] 