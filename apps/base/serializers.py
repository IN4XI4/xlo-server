from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from .models import TopicTag, Topic, SoftSkill, Mentor
from apps.blog.models import Like, Card, UserCardView
from apps.users.utils import get_user_level
from xloserver.constants import LEVEL_GROUPS


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
        creator_level = LEVEL_GROUPS.get("creator", 0)
        user_level_value, _ = get_user_level(user)
        return user_level_value >= creator_level or user.is_staff or user.is_superuser

    class Meta:
        model = Topic
        fields = "__all__"


class SoftSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = SoftSkill
        fields = "__all__"


class SoftSkillSerializerDetails(serializers.ModelSerializer):
    cards_viewed_percentage = serializers.SerializerMethodField()

    class Meta:
        model = SoftSkill
        fields = "__all__"

    def get_cards_viewed_percentage(self, obj):
        user_id = self.context["request"].user.id
        total_cards = Card.objects.filter(soft_skill=obj).count()
        cards_seen_count = UserCardView.objects.filter(user=user_id, card__soft_skill=obj).count()

        if total_cards > 0:
            percentage = (cards_seen_count / total_cards) * 100
            return round(percentage, 2)
        return 0


class MentorSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    job = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()
    picture = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField()

    class Meta:
        model = Mentor
        fields = "__all__"

    def get_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
        return obj.name

    def get_job(self, obj):
        if obj.user:
            return obj.user.profession
        return obj.job

    def get_color(self, obj):
        if obj.user:
            return obj.user.profile_color.color if obj.user.profile_color else None
        return obj.color

    def get_profile(self, obj):
        if obj.user:
            return obj.user.biography
        return obj.profile

    def get_picture(self, obj):
        request = self.context.get("request")
        if obj.user and obj.user.profile_picture:
            return request.build_absolute_uri(obj.profile_picture.url)
        return request.build_absolute_uri(obj.picture.url) if obj.picture else None


class MentorCreateSerializer(serializers.ModelSerializer):
    picture = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Mentor
        fields = ["name", "job", "color", "profile", "picture"]

    def validate(self, data):
        if not data.get("name"):
            raise serializers.ValidationError("Name is required.")
        if not data.get("job"):
            raise serializers.ValidationError("Job is required.")
        return data


class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = ["id", "model"]
