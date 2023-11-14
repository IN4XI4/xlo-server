from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated


from .models import TopicTag, Topic, SoftSkill, Monster, Mentor
from .serializers import TopicTagSerializer, TopicSerializer, SoftSkillSerializer, MonsterSerializer, MentorSerializer


class TopicTagsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TopicTag.objects.all().order_by('id')
    serializer_class = TopicTagSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = {
        "name": ("exact", "icontains"),
    }


class TopicsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Topic.objects.all().order_by('id')
    serializer_class = TopicSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = {
        "title": ("exact", "icontains"),
        "tag": ("exact", "in"),
    }


class SoftSkillsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SoftSkill.objects.all().order_by('id')
    serializer_class = SoftSkillSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = {
        "name": ("exact", "icontains"),
    }


class MonstersViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Monster.objects.all().order_by('id')
    serializer_class = MonsterSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = {
        "name": ("exact", "icontains"),
    }


class MentorsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Mentor.objects.all().order_by('id')
    serializer_class = MentorSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = {
        "name": ("exact", "icontains"),
    }
