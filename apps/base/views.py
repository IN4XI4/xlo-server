from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets, generics, permissions
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import TopicTag, Topic, SoftSkill, Mentor
from .serializers import (
    TopicTagSerializer,
    TopicSerializer,
    SoftSkillSerializer,
    SoftSkillSerializerDetails,
    MentorSerializer,
    MentorCreateSerializer,
    ContentTypeSerializer,
)
from .permissions import MentorPermissions
from apps.blog.models import Like
from apps.spaces.models import Space
from apps.users.utils import get_user_level
from xloserver.constants import get_level


class CustomPagination(PageNumberPagination):
    page_size = 100


class StandardPagination(PageNumberPagination):
    page_size = 20


class TopicTagsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TopicTag.objects.all().order_by("id")
    serializer_class = TopicTagSerializer
    pagination_class = StandardPagination
    filterset_fields = {
        "name": ("exact", "icontains"),
    }

    def get_queryset(self):
        space_id = self.request.query_params.get("space_id")
        topics = Topic.objects.annotate(
            story_count=Count("stories", filter=self.story_count_filter(space_id))
        ).order_by("id")
        queryset = TopicTag.objects.all()
        if space_id:
            queryset = queryset.filter(spaces__id=space_id)
        return (
            queryset.annotate(topic_count=Count("topic"))
            .prefetch_related(Prefetch("topic_set", queryset=topics))
            .order_by("id")
        )

    def story_count_filter(self, space_id):
        """
        Approximate story count per topic: the space's active stories for its members,
        otherwise the public active stories.
        """
        if space_id and Space.user_is_member(self.request.user, space_id):
            return Q(stories__spaces__id=space_id, stories__is_active=True)
        return Q(stories__is_private=False, stories__is_active=True)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        if user.is_authenticated:
            context["liked_topic_ids"] = dict(
                Like.objects.filter(
                    user=user, content_type=ContentType.objects.get_for_model(Topic), is_active=True
                ).values_list("object_id", "id")
            )
        return context


class TopicsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Topic.objects.all().order_by("id")
    serializer_class = TopicSerializer
    pagination_class = StandardPagination
    filterset_fields = {
        "title": ("exact", "icontains"),
        "tag": ("exact", "in"),
    }

    @action(detail=False, methods=["get"], url_path="find-by-slug/(?P<slug>[^/.]+)", url_name="find-by-slug")
    def find_by_slug(self, request, slug=None):
        """
        Retrieve a topic by its slug, independent of its ID.
        """
        topic = get_object_or_404(Topic, slug=slug)
        serializer = self.get_serializer(topic)
        return Response(serializer.data)


class SoftSkillsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SoftSkill.objects.all().order_by("id")
    serializer_class = SoftSkillSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = {
        "name": ("exact", "icontains"),
    }
    pagination_class = CustomPagination

    @action(detail=False, methods=["get"])
    def detailed_list(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = SoftSkillSerializerDetails(queryset, many=True, context={"request": request})
        return Response(serializer.data)


class MentorsViewSet(viewsets.ModelViewSet):
    permission_classes = [MentorPermissions]
    filterset_fields = {
        "name": ("exact", "icontains"),
        "user": ("exact",),
        "created_by": ("exact",),
    }
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == "create":
            return MentorCreateSerializer
        return MentorSerializer

    def get_queryset(self):
        user = self.request.user
        user_level, _ = get_user_level(user)
        queryset = Mentor.objects.filter(user__isnull=True)

        if user_level >= get_level("Creator Lvl 2"):
            queryset = queryset | Mentor.objects.filter(user=user)
        if user_level >= get_level("Creator Lvl 3"):
            queryset = queryset | Mentor.objects.filter(created_by=user)
        return queryset.order_by("-id")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ContentTypeListView(generics.ListAPIView):
    queryset = ContentType.objects.all()
    serializer_class = ContentTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
