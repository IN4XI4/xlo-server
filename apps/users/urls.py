from django.urls import path, include
from rest_framework import routers

from .views import UserViewSet, ProfileColorViewSet, ExperienceViewSet, GenderViewSet, CountryListView

app_name = "users"

router = routers.DefaultRouter()
router.register(r"users", UserViewSet, basename="users")
router.register(r"profile_colors", ProfileColorViewSet, basename="profile_colors")
router.register(r"experience", ExperienceViewSet, basename="experience")
router.register(r"genders", GenderViewSet, basename="genders")

urlpatterns = [
    path("", include(router.urls)),
    path('countries/', CountryListView.as_view(), name='countries-list'),
]
