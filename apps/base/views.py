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
    ContentTypeSerializer,
)


class CustomPagination(PageNumberPagination):
    page_size = 100


class TopicTagsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TopicTag.objects.all().order_by("id")
    serializer_class = TopicTagSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = {
        "name": ("exact", "icontains"),
    }


class TopicsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Topic.objects.all().order_by("id")
    serializer_class = TopicSerializer
    permission_classes = [IsAuthenticated]
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


class MentorsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Mentor.objects.all().order_by("id")
    serializer_class = MentorSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = {
        "name": ("exact", "icontains"),
    }
    pagination_class = CustomPagination


class ContentTypeListView(generics.ListAPIView):
    queryset = ContentType.objects.all()
    serializer_class = ContentTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
