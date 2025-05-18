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
from apps.users.utils import get_user_level
from xloserver.constants import LEVEL_GROUPS


class CustomPagination(PageNumberPagination):
    page_size = 100


class TopicTagsPagination(PageNumberPagination):
    page_size = 20


class TopicTagsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TopicTag.objects.all().order_by("id")
    serializer_class = TopicTagSerializer
    pagination_class = TopicTagsPagination
    filterset_fields = {
        "name": ("exact", "icontains"),
    }

    def get_queryset(self):
        space_id = self.request.query_params.get("space_id")
        if space_id:
            return TopicTag.objects.filter(spaces__id=space_id).distinct().order_by("id")
        return TopicTag.objects.all().order_by("id")

class TopicsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Topic.objects.all().order_by("id")
    serializer_class = TopicSerializer
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

        if user_level >= LEVEL_GROUPS["creator lvl 2"]:
            queryset = queryset | Mentor.objects.filter(user=user)
        if user_level >= LEVEL_GROUPS["creator lvl 3"]:
            queryset = queryset | Mentor.objects.filter(created_by=user)
        return queryset.order_by("-id")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ContentTypeListView(generics.ListAPIView):
    queryset = ContentType.objects.all()
    serializer_class = ContentTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
