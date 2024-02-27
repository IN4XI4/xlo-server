from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from .models import Story, Card, BlockType, Block, Comment, Like, UserStoryView


class StorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Story
        fields = "__all__"
        read_only_fields = ["is_active", "created_time", "updated_time", "user"]


class StoryDetailSerializer(serializers.ModelSerializer):
    cards_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    card_colors = serializers.SerializerMethodField()
    user_has_liked = serializers.SerializerMethodField()
    user_has_viewed = serializers.SerializerMethodField()
    topic_title = serializers.ReadOnlyField(source="topic.title")
    tag_name = serializers.ReadOnlyField(source="topic.tag.name")

    class Meta:
        model = Story
        fields = "__all__"
        read_only_fields = ["is_active", "created_time", "updated_time", "user"]

    def get_cards_count(self, obj):
        return Card.objects.filter(story=obj).count()

    def get_comments_count(self, obj):
        return Comment.objects.filter(story=obj, is_active=True).count()

    def get_likes_count(self, obj):
        return Like.objects.filter(content_type__model="story", object_id=obj.id, liked=True).count()

    def get_card_colors(self, obj):
        colors = Card.objects.filter(story=obj, soft_skill__isnull=False).values_list("soft_skill__color", flat=True)
        return list(filter(None, colors))

    def get_user_has_liked(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return {"liked": False, "disliked": False, "like_id": None}
        content_type = ContentType.objects.get_for_model(obj)
        like = Like.objects.filter(user=user, content_type=content_type.id, object_id=obj.id, is_active=True).first()
        if like:
            return {"liked": like.liked, "disliked": not like.liked, "like_id": like.id}
        else:
            return {"liked": False, "disliked": False, "like_id": None}

    def get_user_has_viewed(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return UserStoryView.objects.filter(user=user, story=obj).exists()


class CardSerializer(serializers.ModelSerializer):
    soft_skill_color = serializers.ReadOnlyField(source="soft_skill.color")
    soft_skill_monster_name = serializers.ReadOnlyField(source="soft_skill.monster_name")
    soft_skill_monster_picture = serializers.ImageField(
        source="soft_skill.monster_picture", required=False, allow_null=True, use_url=True
    )
    mentor_color = serializers.ReadOnlyField(source="mentor.color")
    mentor_name = serializers.ReadOnlyField(source="mentor.name")
    mentor_job = serializers.ReadOnlyField(source="mentor.job")
    mentor_picture = serializers.ImageField(source="mentor.picture", required=False, allow_null=True, use_url=True)

    class Meta:
        model = Card
        fields = "__all__"
        read_only_fields = ["created_time", "updated_time"]


class BlockTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockType
        fields = "__all__"


class BlockSerializer(serializers.ModelSerializer):
    block_type_name = serializers.ReadOnlyField(source="block_type.name")
    user_has_liked = serializers.SerializerMethodField()

    class Meta:
        model = Block
        fields = "__all__"

    def get_user_has_liked(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        content_type = ContentType.objects.get_for_model(obj)
        like = Like.objects.filter(user=user, content_type=content_type.id, object_id=obj.id, is_active=True).first()
        return like.id if like else False


class CommentSerializer(serializers.ModelSerializer):
    replies_count = serializers.SerializerMethodField()
    user_name = serializers.ReadOnlyField(source="user.first_name")
    user_picture = serializers.ImageField(source="user.profile_picture", required=False, allow_null=True, use_url=True)
    formatted_created_time = serializers.SerializerMethodField()
    user_has_liked = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = "__all__"
        read_only_fields = ["created_time", "updated_time", "user"]

    def get_replies_count(self, obj):
        return Comment.objects.filter(parent=obj, is_active=True).count()

    def get_formatted_created_time(self, obj):
        return obj.created_time.strftime("%H:%M %B %d, %Y")

    def get_user_has_liked(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        content_type = ContentType.objects.get_for_model(obj)
        like = Like.objects.filter(user=user, content_type=content_type.id, object_id=obj.id, is_active=True).first()
        return like.id if like else False


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = "__all__"
        read_only_fields = ["created_time", "updated_time", "user"]


class UserStoryViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserStoryView
        fields = "__all__"
        read_only_fields = ("user",)
