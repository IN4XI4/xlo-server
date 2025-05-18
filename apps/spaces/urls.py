from django.urls import path, include
from rest_framework import routers

from .views import SpaceViewSet, MembershipRequestViewSet, MembershipInvitationViewSet

app_name = "spaces"

router = routers.DefaultRouter()
router.register(r"spaces", SpaceViewSet, basename="spaces")
router.register(r"space-requests", MembershipRequestViewSet, basename="space_requests")
router.register(r"space-invitations", MembershipInvitationViewSet, basename="space-invitations")

urlpatterns = [
    path("", include(router.urls)),
]