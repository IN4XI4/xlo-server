from rest_framework import serializers

from .models import Topic, SoftSkill, Monster, Mentor


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = "__all__"


class SoftSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = SoftSkill
        fields = "__all__"


class MonsterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Monster
        fields = "__all__"


class MentorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mentor
        fields = "__all__"
