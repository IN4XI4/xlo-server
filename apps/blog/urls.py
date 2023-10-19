from django.urls import path, include
from rest_framework import routers

from .views import (
    StoriesViewSet,
    CardsViewSet,
    BlockTypesViewSet,
    BlocksViewSet,
    CommentsViewSet,
    LikesViewSet,
    ContentTypeListView,
)


app_name = "blog"

router = routers.DefaultRouter()
router.register(r"stories", StoriesViewSet, basename="stories")
router.register(r"cards", CardsViewSet, basename="cards")
router.register(r"comments", CommentsViewSet, basename="comments")
router.register(r"likes", LikesViewSet, basename="likes")
router.register(r"blocktypes", BlockTypesViewSet, basename="blocktypes")
router.register(r"blocks", BlocksViewSet, basename="blocks")


urlpatterns = [
    path("", include(router.urls)),
    path("contenttypes/", ContentTypeListView.as_view(), name="contenttype-list"),
]
