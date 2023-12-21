from django.urls import path, include
from rest_framework import routers

from .views import TopicTagsViewSet, TopicsViewSet, SoftSkillsViewSet, MentorsViewSet, ContentTypeListView


app_name = "base"

router = routers.DefaultRouter()
router.register(r"topictags", TopicTagsViewSet, basename="topictags")
router.register(r"topics", TopicsViewSet, basename="topics")
router.register(r"softskills", SoftSkillsViewSet, basename="softskills")
router.register(r"mentors", MentorsViewSet, basename="mentors")

urlpatterns = [
    path("", include(router.urls)),
    path("contenttypes/", ContentTypeListView.as_view(), name="contenttype-list"),
]
