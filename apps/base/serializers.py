from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from .models import TopicTag, Topic, SoftSkill, Mentor
from apps.blog.models import Like


class TopicReadOnlySerializer(serializers.ModelSerializer):
    user_has_liked = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = ["id", "title", "image", "user_has_liked", "slug"]

    def get_user_has_liked(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        content_type = ContentType.objects.get_for_model(obj)
        like = Like.objects.filter(user=user, content_type=content_type.id, object_id=obj.id, is_active=True).first()
        return like.id if like else False


class TopicTagSerializer(serializers.ModelSerializer):
    topics = TopicReadOnlySerializer(many=True, read_only=True, source="topic_set")
    topic_content_type_id = serializers.SerializerMethodField()

    class Meta:
        model = TopicTag
        fields = "__all__"

    def get_topic_content_type_id(self, obj):
        content_type = ContentType.objects.get_for_model(Topic)
        return content_type.id


class TopicSerializer(serializers.ModelSerializer):
    topic_content_type_id = serializers.SerializerMethodField()
    user_has_liked = serializers.SerializerMethodField()
    is_creator = serializers.SerializerMethodField()

    def get_topic_content_type_id(self, obj):
        content_type = ContentType.objects.get_for_model(Topic)
        return content_type.id

    def get_user_has_liked(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        content_type = ContentType.objects.get_for_model(obj)
        like = Like.objects.filter(user=user, content_type=content_type.id, object_id=obj.id, is_active=True).first()
        return like.id if like else False

    def get_is_creator(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        if user.groups.filter(name="creator").exists():
            return True
        return user.is_staff or user.is_superuser

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
