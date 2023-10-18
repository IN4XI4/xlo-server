from django.urls import path, include
from rest_framework import routers

from .views import (
    TopicsViewSet,
    MonstersViewSet,
    PostsViewSet,
    BlockTypesViewSet,
    BlocksViewSet,
    CommentsViewSet,
    LikesViewSet,
    ContentTypeListView,
)


app_name = "blog"

router = routers.DefaultRouter()
router.register(r"topics", TopicsViewSet, basename="topics")
router.register(r"posts", PostsViewSet, basename="posts")
router.register(r"comments", CommentsViewSet, basename="comments")
router.register(r"likes", LikesViewSet, basename="likes")
router.register(r"monsters", MonstersViewSet, basename="monsters")
router.register(r"blocktypes", BlockTypesViewSet, basename="blocktypes")
router.register(r"blocks", BlocksViewSet, basename="blocks")


urlpatterns = [
    path("", include(router.urls)),
    path("contenttypes/", ContentTypeListView.as_view(), name="contenttype-list"),
]
