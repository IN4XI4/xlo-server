from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from .models import TopicTag, Topic, SoftSkill, Mentor


class TopicReadOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ["id", "title", "image"]


class TopicTagSerializer(serializers.ModelSerializer):
    topics = TopicReadOnlySerializer(many=True, read_only=True, source="topic_set")

    class Meta:
        model = TopicTag
        fields = "__all__"


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = "__all__"


class SoftSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = SoftSkill
        fields = "__all__"


class MentorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mentor
        fields = "__all__"


class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = ["id", "model"]
