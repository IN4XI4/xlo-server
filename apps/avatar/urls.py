from django.urls import path, include
from rest_framework import routers

from apps.avatar.views import (
    AvatarViewSet,
    AvatarColorCatalogViewSet,
    AvatarItemCatalogViewSet,
    AvatarSkinColorCatalogViewSet,
    UserUnlockedColorViewSet,
    UserUnlockedItemViewSet,
    UserUnlockedSkinColorViewSet,
)

app_name = "avatars"

router = routers.DefaultRouter()
router.register(r"avatars", AvatarViewSet, basename="avatars")
router.register(r"user-items", UserUnlockedItemViewSet, basename="user-items")
router.register(r"user-colors", UserUnlockedColorViewSet, basename="user-colors")
router.register(r"user-skin-colors", UserUnlockedSkinColorViewSet, basename="user-skin-colors")
router.register(r"item-catalog", AvatarItemCatalogViewSet, basename="item-catalog")
router.register(r"color-catalog", AvatarColorCatalogViewSet, basename="color-catalog")
router.register(r"skin-color-catalog", AvatarSkinColorCatalogViewSet, basename="skin-color-catalog")

urlpatterns = [
    path("", include(router.urls)),
]
