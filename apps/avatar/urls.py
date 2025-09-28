from django.urls import path, include
from rest_framework import routers

from apps.avatar.views import AvatarViewSet, UserUnlockedItemViewSet

app_name = "avatars"

router = routers.DefaultRouter()
router.register(r"avatars", AvatarViewSet, basename="avatars")
router.register(r"user-items", UserUnlockedItemViewSet, basename="user-items")

urlpatterns = [
    path("", include(router.urls)),
]
