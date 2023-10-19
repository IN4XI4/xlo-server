from django.urls import path, include
from rest_framework import routers

from .views import TopicsViewSet, SoftSkillsViewSet, MonstersViewSet, MentorsViewSet


app_name = "base"

router = routers.DefaultRouter()
router.register(r"topics", TopicsViewSet, basename="topics")
router.register(r"softskills", SoftSkillsViewSet, basename="softskills")
router.register(r"monsters", MonstersViewSet, basename="monsters")
router.register(r"mentors", MentorsViewSet, basename="mentors")

urlpatterns = [
    path("", include(router.urls)),
]
