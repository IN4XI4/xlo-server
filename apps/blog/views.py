import random

from django.db import transaction
from django.db.models import F, OuterRef, Subquery, Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.generics import CreateAPIView
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, JSONParser, FormParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter

from .models import (
    Story,
    Card,
    Block,
    Comment,
    Like,
    UserStoryView,
    UserCardView,
    RecallCard,
    RecallBlock,
    RecallComment,
    Notification,
)
from .permissions import (
    StoryPermissions,
    CardPermissions,
    IsStaffOrSuperUser,
    BlockPermissions,
    CommentPermissions,
    RecallLikePermissions,
    NotificationPermissions,
)
from .serializers import (
    StorySerializer,
    StoryDetailSerializer,
    CardSerializer,
    CommentSerializer,
    LikeSerializer,
    BlockSerializer,
    BlockDetailSerializer,
    UserStoryViewSerializer,
    RecallCardSerializer,
    RecallCardDetailSerializer,
    RecallBlockSerializer,
    RecallBlockDetailSerializer,
    RecallCommentSerializer,
    NotificationSerializer,
)
from .tasks import send_like_email, send_new_stories_email, send_ask_for_help_email
from .filters import UserOwnedFilterBackend
from apps.base.models import Topic
from apps.users.utils import get_user_level
from xloserver.constants import LEVEL_GROUPS


def clean_data(data):
    return {field: value for field, value in data.items() if value != ""}


class BlocksPagination(PageNumberPagination):
    page_size = 20


class NotificationsPagination(PageNumberPagination):
    page_size = 10


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
    ordering_fields = ["created_time"]
    ordering = ["created_time"]
    filter_backends = [UserOwnedFilterBackend, DjangoFilterBackend, OrderingFilter]

    def get_serializer_class(self):
        """
        Return the class to use for the serializer.
        """
        if self.action in ["retrieve", "list", "find_by_slug"]:
            return StoryDetailSerializer
        return StorySerializer

    def get_queryset(self):
        """
        Retrieves a queryset of Story objects based on user permissions.
        It returns only the active Story objects.

        Returns:
        - QuerySet: A queryset of Story objects.
        """
        user = self.request.user
        return Story.objects.filter(is_active=True).filter(Q(is_private=False) | Q(user=user))

    def get_permissions(self):
        """
        Get the list of permissions that the current action should be checked against.
        """
        if self.action == "approve_story":
            permission_classes = [IsStaffOrSuperUser()]
        elif self.action == "find_by_slug":
            return [AllowAny()]
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

    @action(detail=False, methods=["get"], url_path="find-by-slug/(?P<slug>[^/.]+)", url_name="find-by-slug")
    def find_by_slug(self, request, slug=None):
        """
        Retrieve a topic by its slug, independent of its ID.
        """
        story = get_object_or_404(Story, slug=slug)
        if not story.free_access and not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided or are invalid."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        serializer = self.get_serializer(story)
        story.views_count += 1
        story.save()
        return Response(serializer.data)

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

    @action(detail=True, methods=["get"], url_path="get-story-full")
    def get_story_full(self, request, pk=None):
        try:
            story = Story.objects.get(id=pk, user=request.user)
        except Story.DoesNotExist:
            return Response({"error": "Story not found."}, status=status.HTTP_404_NOT_FOUND)

        cards = Card.objects.filter(story=story).order_by("id")
        story_data = {
            "title": story.title,
            "subtitle": story.subtitle,
            "slug": story.slug,
            "is_private": story.is_private,
            "free_access": story.free_access,
            "difficulty_level": story.difficulty_level,
            "life_moments": story.life_moment,
            "story_identities": story.identity_type,
            "language": story.language,
            "cards": [],
            "image": request.build_absolute_uri(story.image.url) if story.image else None,
        }
        for card in cards:
            blocks = Block.objects.filter(card=card).order_by("id")
            blocks_data = [
                {
                    "id": block.id,
                    "content": block.content,
                    "content_2": block.content_2,
                    "blockType": block.block_class,
                    "quoted_by": block.quoted_by,
                    "title": block.title,
                    "block_color": block.block_color_id,
                    "block_color_string": block.block_color.color if block.block_color else None,
                    "content_class": block.content_class,
                    "image": request.build_absolute_uri(block.image.url) if block.image else None,
                    "image_2": request.build_absolute_uri(block.image_2.url) if block.image_2 else None,
                }
                for block in blocks
            ]

            story_data["cards"].append(
                {
                    "id": card.id,
                    "cardTitle": card.title,
                    "selectedSoftSkill": card.soft_skill.id if card.soft_skill else None,
                    "selectedMentor": card.mentor.id if card.mentor else None,
                    "blocks": blocks_data,
                }
            )
        return Response(story_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="create-story-full")
    def create_story_full(self, request, *args, **kwargs):
        data = request.data
        data = clean_data(data)
        story_data = {
            "title": data.get("title"),
            "subtitle": data.get("subtitle"),
            "topic": data.get("topic"),
            "difficulty_level": data.get("difficulty_level"),
            "language": data.get("language"),
            "life_moment": data.get("life_moments"),
            "identity_type": data.get("story_identities"),
            "is_private": data.get("is_private"),
            "free_access": data.get("free_access"),
        }
        story_serializer = StorySerializer(data=story_data)
        if story_serializer.is_valid():
            story = story_serializer.save(user=request.user, is_active=True)
            if "image" in request.FILES:
                story.image = request.FILES["image"]
                story.save()
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
                    "content_2": request.data.get(f"cards[{card_index}].blocks[{block_index}].content_2"),
                    "block_class": request.data.get(f"cards[{card_index}].blocks[{block_index}].blockType"),
                    "quoted_by": request.data.get(f"cards[{card_index}].blocks[{block_index}].quoted_by"),
                    "block_color": request.data.get(f"cards[{card_index}].blocks[{block_index}].block_color"),
                    "content_class": request.data.get(f"cards[{card_index}].blocks[{block_index}].content_class"),
                    "title": request.data.get(f"cards[{card_index}].blocks[{block_index}].title"),
                }
                if f"cards[{card_index}].blocks[{block_index}].image" in request.FILES:
                    block_data["image"] = request.FILES[f"cards[{card_index}].blocks[{block_index}].image"]
                if f"cards[{card_index}].blocks[{block_index}].image_2" in request.FILES:
                    block_data["image_2"] = request.FILES[f"cards[{card_index}].blocks[{block_index}].image_2"]
                block_serializer = BlockSerializer(data=block_data)
                if block_serializer.is_valid():
                    block_serializer.save()
                else:
                    return Response(block_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # Send to interested users:
        send_new_stories_email.delay(story.topic.id)

        return Response(story_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["put"], url_path="update-story-full")
    def update_story_full(self, request, pk=None):
        try:
            story = Story.objects.get(id=pk, user=request.user)
        except Story.DoesNotExist:
            return Response({"error": "Story not found."}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        data = clean_data(data)
        story_data = {
            "title": data.get("title"),
            "subtitle": data.get("subtitle"),
            "is_private": data.get("is_private"),
            "free_access": data.get("free_access"),
            "life_moment": data.get("life_moments"),
            "identity_type": data.get("story_identities"),
            "difficulty_level": data.get("difficulty_level"),
            "language": data.get("language"),
        }
        if story.image and not request.FILES.get("image"):
            if not request.data.get("image"):
                story.image = None
        elif "image" in request.FILES:
            story_data["image"] = request.FILES["image"]
        story_serializer = StorySerializer(story, data=story_data, partial=True)
        if story_serializer.is_valid():
            story.edited_time = timezone.now()
            story = story_serializer.save()
        else:
            return Response(story_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        cards_keys = [key for key in request.data.keys() if key.startswith("cards[")]
        cards_count = len(set(key.split("[")[1].split("]")[0] for key in cards_keys))
        existing_card_ids = []

        for card_index in range(cards_count):
            card_id = request.data.get(f"cards[{card_index}].id")
            card_data = {
                "story": story.id,
                "title": request.data.get(f"cards[{card_index}].cardTitle"),
                "soft_skill": request.data.get(f"cards[{card_index}].selectedSoftSkill"),
                "mentor": request.data.get(f"cards[{card_index}].selectedMentor"),
            }
            if card_id:
                try:
                    card = Card.objects.get(id=card_id, story=story)
                    card_serializer = CardSerializer(card, data=card_data, partial=True)
                    existing_card_ids.append(card_id)
                except Card.DoesNotExist:
                    return Response({"error": f"Card with ID {card_id} not found."}, status=status.HTTP_404_NOT_FOUND)
            else:
                card_serializer = CardSerializer(data=card_data)

            if card_serializer.is_valid():
                card = card_serializer.save()
                existing_card_ids.append(card.id)
            else:
                return Response(card_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            self.handle_blocks(request, card, card_index)

        Card.objects.filter(story=story).exclude(id__in=existing_card_ids).delete()
        return Response(story_serializer.data, status=status.HTTP_200_OK)

    def handle_blocks(self, request, card, card_index):
        blocks_keys = [key for key in request.data.keys() if key.startswith(f"cards[{card_index}].blocks[")]
        blocks_count = len(set(key.split("[")[2].split("]")[0] for key in blocks_keys))
        existing_block_ids = []
        for block_index in range(blocks_count):
            block_id = request.data.get(f"cards[{card_index}].blocks[{block_index}].id")
            block_data = {
                "card": card.id,
                "content": request.data.get(f"cards[{card_index}].blocks[{block_index}].content"),
                "content_2": request.data.get(f"cards[{card_index}].blocks[{block_index}].content_2"),
                "block_class": request.data.get(f"cards[{card_index}].blocks[{block_index}].blockType"),
                "quoted_by": request.data.get(f"cards[{card_index}].blocks[{block_index}].quoted_by"),
                "block_color": request.data.get(f"cards[{card_index}].blocks[{block_index}].block_color"),
                "content_class": request.data.get(f"cards[{card_index}].blocks[{block_index}].content_class"),
                "title": request.data.get(f"cards[{card_index}].blocks[{block_index}].title"),
            }
            if block_id:
                try:
                    block = Block.objects.get(id=block_id, card=card)
                    block_serializer = BlockSerializer(block, data=block_data, partial=True)
                    if block.image and not request.FILES.get(f"cards[{card_index}].blocks[{block_index}].image"):
                        if not request.data.get(f"cards[{card_index}].blocks[{block_index}].image"):
                            block.image = None
                    elif f"cards[{card_index}].blocks[{block_index}].image" in request.FILES:
                        block_data["image"] = request.FILES[f"cards[{card_index}].blocks[{block_index}].image"]
                    if block.image_2 and not request.FILES.get(f"cards[{card_index}].blocks[{block_index}].image_2"):
                        if not request.data.get(f"cards[{card_index}].blocks[{block_index}].image_2"):
                            block.image_2 = None
                    elif f"cards[{card_index}].blocks[{block_index}].image_2" in request.FILES:
                        block_data["image_2"] = request.FILES[f"cards[{card_index}].blocks[{block_index}].image_2"]

                    existing_block_ids.append(block_id)
                except Block.DoesNotExist:
                    return Response({"error": f"Block with ID {block_id} not found."}, status=status.HTTP_404_NOT_FOUND)
            else:
                block_serializer = BlockSerializer(data=block_data, context={"request": request})

            if block_serializer.is_valid():
                block = block_serializer.save()
                existing_block_ids.append(block.id)
            else:
                return Response(block_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        Block.objects.filter(card=card).exclude(id__in=existing_block_ids).delete()


class CardsViewSet(viewsets.ModelViewSet):
    serializer_class = CardSerializer
    parser_classes = (MultiPartParser, JSONParser)
    permission_classes = [CardPermissions]
    filterset_fields = {
        "title": ("icontains",),
        "story": ("exact", "in"),
        "soft_skill": ("exact", "in"),
        "soft_skill__name": ("exact",),
        "mentor": ("exact", "in"),
        "created_time": ("gte", "lte"),
        "updated_time": ("gte", "lte"),
    }
    pagination_class = BlocksPagination

    def get_queryset(self):
        """
        Retrieves a queryset of Card objects based on user permissions.
        It returns only the active Card objects.

        Returns:
        - QuerySet: A queryset of Card objects.
        """
        if self.request.user.is_authenticated:
            return Card.objects.all().order_by("id")
        else:
            return Card.objects.filter(story__free_access=True).order_by("id")

    def get_permissions(self):
        if self.action == "list":
            return [AllowAny()]
        return [permission() for permission in self.permission_classes]

    @action(detail=False, methods=["post"], url_path="random-by-softskill")
    def random_by_softskill(self, request):
        soft_skill_name = request.data.get("soft_skill")
        seed = request.data.get("seed")
        if not soft_skill_name:
            return Response({"detail": "soft_skill_name parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not seed:
            return Response({"detail": "seed parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        filtered_cards = Card.objects.filter(soft_skill__name__icontains=soft_skill_name)
        filtered_cards_list = list(filtered_cards)
        random.seed(seed)
        random.shuffle(filtered_cards_list)

        page = self.paginate_queryset(filtered_cards_list)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(filtered_cards_list, many=True)
        return Response(serializer.data)


class BlocksViewSet(viewsets.ModelViewSet):
    serializer_class = BlockSerializer
    permission_classes = [BlockPermissions]
    pagination_class = BlocksPagination
    filterset_fields = {
        "card": ("exact", "in"),
        "card__story": ("exact", "in"),
        "block_class": ("exact", "in"),
    }
    ordering_fields = [
        "order",
    ]
    ordering = ["order", "id"]

    def get_serializer_context(self):
        return {"request": self.request}

    def get_serializer_class(self):
        """
        Return the class to use for the serializer.
        """
        if self.action in ["retrieve"]:
            return BlockDetailSerializer
        return BlockSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Block.objects.all().order_by("id")
        else:
            return Block.objects.filter(card__story__free_access=True).order_by("id")

    def get_permissions(self):
        if self.action == "list":
            return [AllowAny()]
        return [permission() for permission in self.permission_classes]

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if request.user.is_authenticated and "card" in request.query_params:
            card_id = request.query_params.get("card")
            if card_id:
                card = get_object_or_404(Card, id=card_id)
                UserCardView.objects.get_or_create(user=request.user, card=card)
        return response


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
        with transaction.atomic():
            comment = serializer.save(user=self.request.user)
            if comment.parent is not None:
                if comment.parent.user != self.request.user:
                    Notification.objects.create(
                        user=comment.parent.user,
                        notification_type="reply",
                        content_type=ContentType.objects.get_for_model(Comment),
                        object_id=comment.id,
                    )
                    if comment.parent.user.email_reply:
                        send_like_email.delay(
                            comment.parent.user.id, comment.parent.comment_text, True, comment.story.slug
                        )
            if comment.ask_for_help:
                send_ask_for_help_email.delay(
                    comment.user.id, comment.comment_text, comment.story.title, comment.story.slug
                )

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Comment.objects.filter(is_active=True).order_by("id")
        else:
            return Comment.objects.filter(story__free_access=True).order_by("id")

    def get_permissions(self):
        if self.action == "list":
            return [AllowAny()]
        return [permission() for permission in self.permission_classes]

    def get_serializer_context(self):
        return {"request": self.request}


class LikesViewSet(viewsets.ModelViewSet):
    serializer_class = LikeSerializer
    permission_classes = [RecallLikePermissions]
    filterset_fields = {
        "user": ("exact",),
        "created_time": ("gte", "lte"),
        "updated_time": ("gte", "lte"),
    }

    def get_queryset(self):
        return Like.objects.filter(is_active=True)

    def perform_create(self, serializer):
        with transaction.atomic():
            serializer.save(user=self.request.user)
            like_instance = serializer.instance
            if like_instance.liked and like_instance.content_type == ContentType.objects.get_for_model(Comment):
                comment = like_instance.content
                if comment.user != self.request.user:
                    Notification.objects.create(
                        user=comment.user,
                        notification_type="like",
                        content_type=ContentType.objects.get_for_model(Like),
                        object_id=like_instance.id,
                    )
                    if comment.user.email_reply:
                        send_like_email.delay(comment.user.id, comment.comment_text, False, comment.story.slug)


class UserStoryViewCreate(CreateAPIView):
    queryset = UserStoryView.objects.all()
    serializer_class = UserStoryViewSerializer

    def perform_create(self, serializer):
        story_id = self.request.data.get("story")
        story = get_object_or_404(Story, id=story_id)

        UserStoryView.objects.get_or_create(user=self.request.user, story=story)
        user_level = get_user_level(self.request.user)
        commentor_level = LEVEL_GROUPS.get("commentor", 0)
        if self.request.user.is_superuser or self.request.user.is_staff or user_level >= commentor_level:
            return

        views_count = UserStoryView.objects.filter(user=self.request.user).count()
        if views_count >= 3:
            commentor_group, _ = Group.objects.get_or_create(name="commentor")
            self.request.user.groups.add(commentor_group)
            self.request.user.save()


class RecallCardViewSet(viewsets.ModelViewSet):
    serializer_class = RecallCardSerializer
    permission_classes = [RecallLikePermissions]
    queryset = RecallCard.objects.all()
    filterset_fields = {
        "user": ("exact",),
        "card": ("exact",),
        "created_time": ("gte", "lte"),
        "updated_time": ("gte", "lte"),
    }

    def get_serializer_class(self):
        if self.action == "list_user_recall_cards":
            return RecallCardDetailSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"], url_path="user-recall-cards")
    def list_user_recall_cards(self, request, *args, **kwargs):
        user = request.user
        very_important_cards = RecallCard.objects.filter(user=user, importance_level="2").order_by("?")
        important_cards = RecallCard.objects.filter(user=user, importance_level="1").order_by("?")
        combined_cards = list(very_important_cards) + list(important_cards)
        serializer = self.get_serializer(combined_cards, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RecallBlockViewSet(viewsets.ModelViewSet):
    permission_classes = [RecallLikePermissions]
    queryset = RecallBlock.objects.all()
    filterset_fields = {
        "user": ("exact",),
        "block": ("exact",),
        "created_time": ("gte", "lte"),
        "updated_time": ("gte", "lte"),
    }

    ordering_fields = ["importance_level", "created_time"]

    def get_queryset(self):
        return RecallBlock.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return RecallBlockSerializer
        return RecallBlockDetailSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"], url_path="random-recalled-block-ids")
    def random_recalled_block_ids(self, request):
        user = request.user
        very_important_block_ids = list(
            RecallBlock.objects.filter(user=user, importance_level="2")
            .order_by("?")
            .values_list("block__id", flat=True)
        )
        important_block_ids = list(
            RecallBlock.objects.filter(user=user, importance_level="1")
            .order_by("?")
            .values_list("block__id", flat=True)
        )
        combined_ids = very_important_block_ids + important_block_ids
        block_content_type = ContentType.objects.get_for_model(Block).id
        response_data = {"block_ids": combined_ids, "block_content_type": block_content_type}
        return Response(response_data, status=status.HTTP_200_OK)


class RecallCommentViewSet(viewsets.ModelViewSet):
    serializer_class = RecallCommentSerializer
    permission_classes = [RecallLikePermissions]
    queryset = RecallComment.objects.all()
    filterset_fields = {
        "user": ("exact",),
        "comment": ("exact",),
        "created_time": ("gte", "lte"),
        "updated_time": ("gte", "lte"),
    }

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [NotificationPermissions]
    filterset_fields = {
        "user": ("exact",),
        "notification_type": ("exact",),
        "date": ("gte", "lte"),
    }
    pagination_class = NotificationsPagination

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by("-id")
