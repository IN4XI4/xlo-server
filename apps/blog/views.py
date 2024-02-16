from django.db.models import F

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Story, Card, BlockType, Block, Comment, Like
from .permissions import StoryPermissions, CardPermissions, IsStaffOrSuperUser, BlockPermissions, CommentPermissions
from .serializers import (
    StorySerializer,
    StoryDetailSerializer,
    CardSerializer,
    CommentSerializer,
    LikeSerializer,
    BlockTypeSerializer,
    BlockSerializer,
)


class StoriesViewSet(viewsets.ModelViewSet):
    parser_classes = (MultiPartParser,)
    permission_classes = [StoryPermissions]
    filterset_fields = {
        "title": ("icontains",),
        "topic": ("exact", "in"),
        "created_time": ("gte", "lte"),
        "updated_time": ("gte", "lte"),
        "user": ("exact",),
        "user__username": ("icontains",),
        "is_active": ("exact",),
    }
    ordering_fields = [
        "created_time",
    ]
    ordering = [
        "created_time",
    ]

    def get_serializer_class(self):
        """
        Return the class to use for the serializer.
        """
        if self.action in ["retrieve", "list"]:
            return StoryDetailSerializer
        return StorySerializer

    def get_queryset(self):
        """
        Retrieves a queryset of Story objects based on user permissions.
        It returns only the active Story objects.

        Returns:
        - QuerySet: A queryset of Story objects.
        """
        return Story.objects.filter(is_active=True).order_by("id")

    def get_permissions(self):
        """
        Get the list of permissions that the current action should be checked against.
        """
        if self.action == "approve_story":
            permission_classes = [IsStaffOrSuperUser()]
        else:
            permission_classes = [permission() for permission in self.permission_classes]
        return permission_classes

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a specific Story instance.

        Args:
        - request (Request): The HTTP request object.

        Returns:
        - Response: Serialized story data.
        """
        instance = self.get_object()
        Story.objects.filter(pk=instance.pk).update(views_count=F("views_count") + 1)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        After saving the story, the method checks if the user is a superuser. If so,
        the story's `is_active` attribute is set to True.

        Args:
        - request (Request): The HTTP request object containing story data.
        - *args: Variable length argument list.
        - **kwargs: Arbitrary keyword arguments.

        Returns:
        - Response: Serialized story data with a status of HTTP 201 CREATED.
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        story = serializer.save()
        if request.user.is_superuser:
            story.is_active = True
        story.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(methods=["post"], detail=True)
    def approve_story(self, request, pk=None):
        """
        Approves a story by setting `is_active` to True.

        Args:
        - request (Request): The HTTP request object.
        - pk (int, optional): The primary key of the story.

        Returns:
        - Response: Message indicating approval with HTTP 202 ACCEPTED status.
        """
        story = self.get_object()
        story.is_active = True
        story.save()
        return Response({"message": "Story approved"}, status=status.HTTP_202_ACCEPTED)


class CardsViewSet(viewsets.ModelViewSet):
    serializer_class = CardSerializer
    parser_classes = (MultiPartParser,)
    permission_classes = [CardPermissions]
    filterset_fields = {
        "title": ("icontains",),
        "story": ("exact", "in"),
        "soft_skill": ("exact", "in"),
        "mentor": ("exact", "in"),
        "created_time": ("gte", "lte"),
        "updated_time": ("gte", "lte"),
    }

    def get_queryset(self):
        """
        Retrieves a queryset of Card objects based on user permissions.
        It returns only the active Card objects.

        Returns:
        - QuerySet: A queryset of Card objects.
        """
        return Card.objects.all()


class BlockTypesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BlockType.objects.all()
    serializer_class = BlockTypeSerializer
    filterset_fields = {
        "name": ("exact", "icontains"),
    }


class BlocksPagination(PageNumberPagination):
    page_size = 15


class BlocksViewSet(viewsets.ModelViewSet):
    queryset = Block.objects.all()
    serializer_class = BlockSerializer
    permission_classes = [BlockPermissions]
    pagination_class = BlocksPagination
    filterset_fields = {
        "card": ("exact", "in"),
        "card__story": ("exact", "in"),
        "block_type": ("exact", "in"),
    }
    ordering_fields = [
        "order",
    ]
    ordering = [
        "order",
    ]

    def get_serializer_context(self):
        return {"request": self.request}


class CommentsViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [CommentPermissions]
    filterset_fields = {
        "comment_text": ("icontains",),
        "story": ("exact", "in"),
        "user": ("exact",),
        "created_time": ("gte", "lte"),
        "updated_time": ("gte", "lte"),
        "is_active": ("exact",),
        "parent": ("exact", "isnull"),
    }
    ordering_fields = [
        "created_time",
    ]
    ordering = [
        "created_time",
    ]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return Comment.objects.filter(is_active=True).order_by("id")

    def get_serializer_context(self):
        return {"request": self.request}


class LikesViewSet(viewsets.ModelViewSet):
    serializer_class = LikeSerializer
    permission_classes = [CommentPermissions]
    filterset_fields = {
        "user": ("exact",),
        "created_time": ("gte", "lte"),
        "updated_time": ("gte", "lte"),
    }

    def get_queryset(self):
        return Like.objects.filter(is_active=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
