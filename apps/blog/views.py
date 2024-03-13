from django.db.models import F, OuterRef, Subquery
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets, status
from rest_framework.generics import CreateAPIView
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, JSONParser, FormParser
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Story, Card, BlockType, Block, Comment, Like, UserStoryView
from .permissions import StoryPermissions, CardPermissions, IsStaffOrSuperUser, BlockPermissions, CommentPermissions
from .serializers import (
    StorySerializer,
    StoryDetailSerializer,
    CardSerializer,
    CommentSerializer,
    LikeSerializer,
    BlockTypeSerializer,
    BlockSerializer,
    UserStoryViewSerializer,
)
from apps.base.models import Topic


class StoriesViewSet(viewsets.ModelViewSet):
    parser_classes = (MultiPartParser, FormParser, JSONParser)
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

    @action(detail=False, methods=["get"])
    def liked_topics_stories(self, request):
        topic_content_type = ContentType.objects.get_for_model(Topic)
        likes_subquery = Like.objects.filter(
            user_id=request.user.id,
            liked=True,
            content_type=topic_content_type,
            object_id=OuterRef("topic_id"),
            is_active=True,
        ).values("created_time")[:1]

        order = request.query_params.get("order", "desc")
        search_query = request.query_params.get("search", None)

        order_criteria = "-created_time" if order == "desc" else "created_time"
        stories_queryset = Story.objects.filter(
            topic_id__in=Like.objects.filter(
                user=request.user, liked=True, content_type=topic_content_type, is_active=True
            ).values_list("object_id", flat=True),
            created_time__gt=Subquery(likes_subquery),
            is_active=True,
        )
        if search_query:
            stories_queryset = stories_queryset.filter(title__icontains=search_query)
        stories_queryset = stories_queryset.order_by(order_criteria)
        page = self.paginate_queryset(stories_queryset)
        if page is not None:
            serializer = StoryDetailSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)

        serializer = StoryDetailSerializer(stories_queryset, many=True, context={"request": request})
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="create-story-full")
    def create_story_full(self, request, *args, **kwargs):
        data = request.data
        story_data = {
            "title": data.get("title"),
            "subtitle": data.get("subtitle"),
            "topic": data.get("topic"),
        }

        story_serializer = StorySerializer(data=story_data)
        if story_serializer.is_valid():
            story = story_serializer.save(user=request.user, is_active=True)
        else:
            return Response(story_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        cards_keys = [key for key in request.data.keys() if key.startswith("cards[")]
        cards_count = len(set(key.split("[")[1].split("]")[0] for key in cards_keys))
        for card_index in range(cards_count):
            card_data = {
                "story": story.id,
                "title": request.data.get(f"cards[{card_index}].cardTitle"),
                "soft_skill": request.data.get(f"cards[{card_index}].selectedSoftSkill"),
                "mentor": request.data.get(f"cards[{card_index}].selectedMentor"),
            }
            card_serializer = CardSerializer(data=card_data)
            if card_serializer.is_valid():
                card = card_serializer.save()
            else:
                return Response(card_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            blocks_keys = [key for key in request.data.keys() if key.startswith(f"cards[{card_index}].blocks[")]
            blocks_count = len(set(key.split("[")[2].split("]")[0] for key in blocks_keys))

            for block_index in range(blocks_count):
                block_data = {
                    "card": card.id,
                    "content": request.data.get(f"cards[{card_index}].blocks[{block_index}].content"),
                    "block_type": request.data.get(f"cards[{card_index}].blocks[{block_index}].blockType"),
                }
                if f"cards[{card_index}].blocks[{block_index}].image" in request.FILES:
                    block_data["image"] = request.FILES[f"cards[{card_index}].blocks[{block_index}].image"]
                block_serializer = BlockSerializer(data=block_data)
                if block_serializer.is_valid():
                    block_serializer.save()
                else:
                    return Response(block_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(story_serializer.data, status=status.HTTP_201_CREATED)


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


class UserStoryViewCreate(CreateAPIView):
    queryset = UserStoryView.objects.all()
    serializer_class = UserStoryViewSerializer

    def perform_create(self, serializer):
        story_id = self.request.data.get("story")
        story = get_object_or_404(Story, id=story_id)

        UserStoryView.objects.get_or_create(user=self.request.user, story=story)
