from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .models import Topic, Monster, Post, BlockType, Block, Comment, Like
from .permissions import PostPermissions, IsStaffOrSuperUser, BlockPermissions, CommentPermissions
from .serializers import (
    TopicSerializer,
    MonsterSerializer,
    PostSerializer,
    CommentSerializer,
    LikeSerializer,
    ContentTypeSerializer,
    BlockTypeSerializer,
    BlockSerializer,
)


class TopicsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    filterset_fields = {
        "name": ("exact", "icontains"),
    }


class MonstersViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Monster.objects.all()
    serializer_class = MonsterSerializer
    filterset_fields = {
        "name": ("exact", "icontains"),
    }


class PostsViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    parser_classes = (MultiPartParser,)
    permission_classes = PostPermissions
    filterset_fields = {
        "title": ("icontains",),
        "topic": (
            "exact",
            "in",
        ),
        "monster": (
            "exact",
            "in",
        ),
        "created_time": (
            "gte",
            "lte",
        ),
        "updated_time": (
            "gte",
            "lte",
        ),
        "user": ("exact",),
        "user__username": ("icontains",),
        "is_active": ("exact",),
    }

    def get_permissions(self):
        """
        Get the list of permissions that the current action should be checked against.
        """
        if self.action == "approve_post":
            permission_classes = [IsStaffOrSuperUser]
        else:
            permission_classes = [permission() for permission in self.permission_classes]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Retrieves a queryset of Post objects based on user permissions.
        It returns only the active Post objects.

        Returns:
        - QuerySet: A queryset of Post objects.
        """
        return Post.objects.filter(is_active=True)

    def create(self, request, *args, **kwargs):
        """
        Overrides the default create method to handle post creation.

        After saving the post, the method checks if the user is a superuser. If so,
        the post's `is_active` attribute is set to True.

        Args:
        - request (Request): The HTTP request object containing post data.
        - *args: Variable length argument list.
        - **kwargs: Arbitrary keyword arguments.

        Returns:
        - Response: Serialized post data with a status of HTTP 201 CREATED.
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = serializer.save()
        if request.user.is_superuser:
            post.is_active = True
        post.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(methods=["post"], detail=True)
    def approve_post(self, request, pk=None):
        """
        Approves a post by setting `is_active` to True.

        Args:
        - request (Request): The HTTP request object.
        - pk (int, optional): The primary key of the post.

        Returns:
        - Response: Message indicating approval with HTTP 202 ACCEPTED status.
        """
        post = self.get_object()
        post.is_active = True
        post.save()
        return Response({"message": "Post approved"}, status=status.HTTP_202_ACCEPTED)


class BlockTypesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BlockType.objects.all()
    serializer_class = BlockTypeSerializer
    filterset_fields = {
        "name": ("exact", "icontains"),
    }


class BlocksViewSet(viewsets.ModelViewSet):
    queryset = Block.objects.all()
    serializer_class = BlockSerializer
    permission_classes = BlockPermissions
    filterset_fields = {
        "post": ("exact", "in"),
        "post__user": ("exact", "in"),
        "block_type": ("exact", "in"),
    }


class CommentsViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = CommentPermissions
    filterset_fields = {
        "comment_text": ("icontains",),
        "post": ("exact", "in"),
        "user": ("exact",),
        "created_time": (
            "gte",
            "lte",
        ),
        "updated_time": (
            "gte",
            "lte",
        ),
        "is_active": ("exact",),
    }

    def get_queryset(self):
        return Comment.objects.filter(is_active=True)


class LikesViewSet(viewsets.ModelViewSet):
    serializer_class = LikeSerializer
    permission_classes = CommentPermissions
    filterset_fields = {
        "user": ("exact",),
        "created_time": (
            "gte",
            "lte",
        ),
        "updated_time": (
            "gte",
            "lte",
        ),
    }

    def get_queryset(self):
        return Like.objects.filter(is_active=True)


class ContentTypeListView(generics.ListAPIView):
    queryset = ContentType.objects.all()
    serializer_class = ContentTypeSerializer
