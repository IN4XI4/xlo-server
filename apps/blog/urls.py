from django.urls import path, include
from rest_framework import routers

from .views import (
    StoriesViewSet,
    CardsViewSet,
    BlockTypesViewSet,
    BlocksViewSet,
    CommentsViewSet,
    LikesViewSet,
    UserStoryViewCreate,
    RecallCardViewSet,
    RecallBlockViewSet,
    RecallCommentViewSet,
    NotificationViewSet
)


app_name = "blog"

router = routers.DefaultRouter()
router.register(r"stories", StoriesViewSet, basename="stories")
router.register(r"cards", CardsViewSet, basename="cards")
router.register(r"comments", CommentsViewSet, basename="comments")
router.register(r"likes", LikesViewSet, basename="likes")
router.register(r"blocktypes", BlockTypesViewSet, basename="blocktypes")
router.register(r"blocks", BlocksViewSet, basename="blocks")
router.register(r"recalls", RecallCardViewSet, basename="recalls")
router.register(r"recall-blocks", RecallBlockViewSet, basename="recalls-blocks")
router.register(r"recall-comments", RecallCommentViewSet, basename="recalls-comments")
router.register(r"notifications", NotificationViewSet, basename="notifications")


urlpatterns = [
    path("", include(router.urls)),
    path("user-view-story/", UserStoryViewCreate.as_view(), name="user-view-story"),
]
