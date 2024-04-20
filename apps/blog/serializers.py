from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from .models import Story, Card, BlockType, Block, Comment, Like, UserStoryView, RecallCard, Notification


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
    soft_skill_monster_profile = serializers.ReadOnlyField(source="soft_skill.monster_profile")
    soft_skill_monster_picture = serializers.ImageField(
        source="soft_skill.monster_picture", required=False, allow_null=True, use_url=True
    )
    soft_skill_name = serializers.ReadOnlyField(source="soft_skill.name")
    soft_skill_description = serializers.ReadOnlyField(source="soft_skill.description")
    soft_skill_logo = serializers.FileField(source="soft_skill.logo", required=False, allow_null=True, use_url=True)
    mentor_color = serializers.ReadOnlyField(source="mentor.color")
    mentor_name = serializers.ReadOnlyField(source="mentor.name")
    mentor_job = serializers.ReadOnlyField(source="mentor.job")
    mentor_profile = serializers.ReadOnlyField(source="mentor.profile")
    mentor_picture = serializers.ImageField(source="mentor.picture", required=False, allow_null=True, use_url=True)
    user_has_recalled = serializers.SerializerMethodField()

    def get_user_has_recalled(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return {"recall": False, "level": None, "recall_id": None}
        recall = RecallCard.objects.filter(user=user, card=obj).first()
        if recall:
            return {"recall": True, "level": recall.importance_level, "recall_id": recall.id}
        else:
            return {"recall": False, "level": None, "recall_id": None}

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


class RecallCardSerializer(serializers.ModelSerializer):

    class Meta:
        model = RecallCard
        fields = "__all__"
        read_only_fields = (
            "created_time",
            "updated_time",
            "user",
        )


class RecallCardDetailSerializer(serializers.ModelSerializer):
    card = CardSerializer(read_only=True)

    class Meta:
        model = RecallCard
        fields = "__all__"
        read_only_fields = (
            "created_time",
            "updated_time",
            "user",
        )


class NotificationSerializer(serializers.ModelSerializer):
    user_action = serializers.SerializerMethodField()
    comment_details = serializers.SerializerMethodField()
    formatted_date = serializers.SerializerMethodField()
    user_picture = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = "__all__"
        read_only_fields = (
            "date",
            "user",
        )

    def get_user_action(self, obj):
        if obj.notification_type == "like":
            like = Like.objects.filter(id=obj.object_id).first()
            if like:
                return (
                    f"{like.user.first_name} {like.user.last_name}"
                    if like.user.first_name and like.user.last_name
                    else like.user.username
                )
        elif obj.notification_type == "reply":
            reply = Comment.objects.filter(id=obj.object_id).first()
            if reply:
                return (
                    f"{reply.user.first_name} {reply.user.last_name}"
                    if reply.user.first_name and reply.user.last_name
                    else reply.user.username
                )
        return None

    def get_comment_details(self, obj):
        details = {"story": None, "story_id": None, "text": None, "parent_text": None}
        if obj.notification_type == "like":
            like = Like.objects.filter(id=obj.object_id).first()
            if like and like.content:
                details["story"] = like.content.story.title if hasattr(like.content, "story") else None
                details["story_id"] = like.content.story.id if hasattr(like.content, "story") else None
                details["text"] = like.content.comment_text if hasattr(like.content, "comment_text") else None
        elif obj.notification_type == "reply":
            reply = Comment.objects.filter(id=obj.object_id).select_related("story", "parent").first()
            if reply:
                details["story"] = reply.story.title if reply.story else None
                details["story_id"] = reply.story.id if reply.story else None
                details["text"] = reply.comment_text if reply else None
                details["parent_text"] = reply.parent.comment_text if reply.parent else None

        return details

    def get_formatted_date(self, obj):
        return obj.date.strftime("%B %d, %Y")

    def get_user_picture(self, obj):
        request = self.context.get("request")
        if obj.notification_type == "like":
            like = Like.objects.filter(id=obj.object_id).first()
            if like and like.user.profile_picture:
                return request.build_absolute_uri(like.user.profile_picture.url)
        elif obj.notification_type == "reply":
            reply = Comment.objects.filter(id=obj.object_id).first()
            if reply and reply.user.profile_picture:
                return request.build_absolute_uri(reply.user.profile_picture.url)
        return None
