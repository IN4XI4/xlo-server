from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets, generics, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination


from .models import TopicTag, Topic, SoftSkill, Mentor
from .serializers import (
    TopicTagSerializer,
    TopicSerializer,
    SoftSkillSerializer,
    MentorSerializer,
    ContentTypeSerializer,
)


class CustomPagination(PageNumberPagination):
    page_size = 50


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


class SoftSkillsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SoftSkill.objects.all().order_by("id")
    serializer_class = SoftSkillSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = {
        "name": ("exact", "icontains"),
    }
    pagination_class = CustomPagination


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
