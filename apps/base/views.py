from rest_framework import viewsets

from .models import Topic, SoftSkill, Monster, Mentor
from .serializers import TopicSerializer, SoftSkillSerializer, MonsterSerializer, MentorSerializer


class TopicsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    filterset_fields = {
        "name": ("exact", "icontains"),
    }


class SoftSkillsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SoftSkill.objects.all()
    serializer_class = SoftSkillSerializer
    filterset_fields = {
        "name": ("exact", "icontains"),
    }


class MonstersViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Monster.objects.all()
    serializer_class = MonsterSerializer
    filterset_fields = {
        "name": ("exact", "icontains"),
    }


class MentorsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Mentor.objects.all()
    serializer_class = MentorSerializer
    filterset_fields = {
        "name": ("exact", "icontains"),
    }
