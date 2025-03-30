from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from .models import (
    Story,
    Card,
    Block,
    Comment,
    Like,
    UserStoryView,
    RecallCard,
    RecallBlock,
    RecallComment,
    Notification,
)

from apps.users.models import UserBadge, BadgeLevels
from apps.users.serializers import UserBadgeSerializer

class StorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Story
        fields = [
            "id",
            "user",
            "topic",
            "title",
            "subtitle",
            "is_active",
            "is_private",
            "created_time",
            "updated_time",
            "edited_time",
            "views_count",
            "slug",
            "free_access",
            "is_premium",
        ]
        read_only_fields = ["is_active", "created_time", "updated_time", "user"]


class StoryDetailSerializer(serializers.ModelSerializer):
    topic_title = serializers.ReadOnlyField(source="topic.title")
    topic_slug = serializers.ReadOnlyField(source="topic.slug")
    tag_name = serializers.ReadOnlyField(source="topic.tag.name")
    user_color = serializers.ReadOnlyField(source="user.profile_color.color")
    user_picture = serializers.ImageField(source="user.profile_picture", required=False, allow_null=True, use_url=True)
    is_owner = serializers.SerializerMethodField()
    cards_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    card_colors = serializers.SerializerMethodField()
    user_has_liked = serializers.SerializerMethodField()
    user_has_viewed = serializers.SerializerMethodField()
    previous_story_slug = serializers.SerializerMethodField()
    next_story_slug = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    difficulty_name = serializers.SerializerMethodField()
    language_name = serializers.SerializerMethodField()
    difficulty_color = serializers.SerializerMethodField()

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

    def get_is_owner(self, obj):
        return obj.user == self.context["request"].user

    def get_previous_story_slug(self, obj):
        previous_story = Story.objects.filter(topic=obj.topic, id__lt=obj.id).order_by("-id").first()
        if previous_story:
            return previous_story.slug
        return None

    def get_next_story_slug(self, obj):
        next_story = Story.objects.filter(topic=obj.topic, id__gt=obj.id).order_by("id").first()
        if next_story:
            return next_story.slug
        return None

    def get_owner_name(self, obj):
        user = obj.user
        if user.first_name:
            return f"{user.first_name} {user.last_name}".strip()
        else:
            return user.email.split("@")[0]

    def get_difficulty_color(self, obj):
        return obj.DIFFICULTY_LEVELS[obj.difficulty_level][1] if obj.difficulty_level is not None else None

    def get_difficulty_name(self, obj):
        return obj.get_difficulty_level_display()

    def get_language_name(self, obj):
        return obj.get_language_display()


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
    mentor_color = serializers.SerializerMethodField()
    mentor_name = serializers.SerializerMethodField()
    mentor_job = serializers.SerializerMethodField()
    mentor_profile = serializers.SerializerMethodField()
    mentor_picture = serializers.SerializerMethodField()
    user_has_recalled = serializers.SerializerMethodField()
    owner_picture = serializers.FileField(
        source="story.user.profile_picture", required=False, allow_null=True, use_url=True
    )
    owner_color = serializers.ReadOnlyField(source="story.user.profile_color.color")

    def get_user_has_recalled(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return {"recall": False, "level": None, "recall_id": None}
        recall = RecallCard.objects.filter(user=user, card=obj).first()
        if recall:
            return {"recall": True, "level": recall.importance_level, "recall_id": recall.id}
        else:
            return {"recall": False, "level": None, "recall_id": None}

    def get_mentor_color(self, obj):
        if obj.mentor.user and obj.mentor.user.profile_color:
            return obj.mentor.user.profile_color.color
        return obj.mentor.color

    def get_mentor_name(self, obj):
        if obj.mentor.user:
            user = obj.mentor.user
            return f"{user.first_name} {user.last_name}".strip() or user.username
        return obj.mentor.name

    def get_mentor_job(self, obj):
        if obj.mentor.user and obj.mentor.user.profession:
            return obj.mentor.user.profession
        return obj.mentor.job

    def get_mentor_profile(self, obj):
        if obj.mentor.user:
            return obj.mentor.user.biography
        return obj.mentor.profile

    def get_mentor_picture(self, obj):
        request = self.context.get("request")
        if obj.mentor.user and obj.mentor.user.profile_picture:
            return request.build_absolute_uri(obj.mentor.user.profile_picture.url)
        return request.build_absolute_uri(obj.mentor.picture.url) if obj.mentor.picture else None

    class Meta:
        model = Card
        fields = "__all__"
        read_only_fields = ["created_time", "updated_time"]


class BlockSerializer(serializers.ModelSerializer):
    block_color_string = serializers.ReadOnlyField(source="block_color.color")
    block_type_name = serializers.SerializerMethodField()
    user_has_liked = serializers.SerializerMethodField()
    user_has_recalled = serializers.SerializerMethodField()

    class Meta:
        model = Block
        fields = "__all__"

    def get_block_type_name(self, obj):
        return obj.get_block_class_display()

    def get_user_has_liked(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        content_type = ContentType.objects.get_for_model(obj)
        like = Like.objects.filter(user=user, content_type=content_type.id, object_id=obj.id, is_active=True).first()
        return like.id if like else False

    def get_user_has_recalled(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return {"recall": False, "level": None, "recall_id": None}
        recall = RecallBlock.objects.filter(user=user, block=obj).first()
        if recall:
            return {"recall": True, "level": recall.importance_level, "recall_id": recall.id}
        else:
            return {"recall": False, "level": None, "recall_id": None}

    def validate(self, data):
        if data.get("block_class") == 10:  # Type "QUESTION"
            options = data.get("options", [])
            correct_answers = options.get("correct_answer", [])
            incorrect_answers = options.get("incorrect_answers", [])

            if not correct_answers:
                raise serializers.ValidationError("A question block must have at least one correct answer.")
            if not incorrect_answers:
                raise serializers.ValidationError("A question block must have at least one incorrect answer.")

            if not isinstance(correct_answers, list) or not isinstance(incorrect_answers, list):
                raise serializers.ValidationError("Correct and incorrect answers must be lists.")
        return data


class BlockDetailSerializer(serializers.ModelSerializer):
    block_type_name = serializers.SerializerMethodField()
    block_color_string = serializers.ReadOnlyField(source="block_color.color")
    story_title = serializers.ReadOnlyField(source="card.story.title")
    card_title = serializers.ReadOnlyField(source="card.title")
    soft_skill_description = serializers.ReadOnlyField(source="card.soft_skill.description")
    soft_skill_logo = serializers.FileField(
        source="card.soft_skill.logo", required=False, allow_null=True, use_url=True
    )
    soft_skill_color = serializers.ReadOnlyField(source="card.soft_skill.color")
    soft_skill_name = serializers.ReadOnlyField(source="card.soft_skill.name")
    soft_skill_monster_name = serializers.ReadOnlyField(source="card.soft_skill.monster_name")
    soft_skill_monster_profile = serializers.ReadOnlyField(source="card.soft_skill.monster_profile")
    soft_skill_monster_picture = serializers.ImageField(
        source="card.soft_skill.monster_picture", required=False, allow_null=True, use_url=True
    )
    mentor_color = serializers.ReadOnlyField(source="card.mentor.color")
    mentor_name = serializers.ReadOnlyField(source="card.mentor.name")
    mentor_job = serializers.ReadOnlyField(source="card.mentor.job")
    mentor_profile = serializers.ReadOnlyField(source="card.mentor.profile")
    mentor_picture = serializers.ImageField(source="card.mentor.picture", required=False, allow_null=True, use_url=True)
    user_has_liked = serializers.SerializerMethodField()
    user_has_recalled = serializers.SerializerMethodField()
    owner_picture = serializers.ImageField(
        source="card.story.user.profile_picture", required=False, allow_null=True, use_url=True
    )

    class Meta:
        model = Block
        fields = "__all__"

    def get_block_type_name(self, obj):
        return obj.get_block_class_display()

    def get_user_has_liked(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        content_type = ContentType.objects.get_for_model(obj)
        like = Like.objects.filter(user=user, content_type=content_type.id, object_id=obj.id, is_active=True).first()
        return like.id if like else False

    def get_user_has_recalled(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return {"recall": False, "level": None, "recall_id": None}
        recall = RecallBlock.objects.filter(user=user, block=obj).first()
        if recall:
            return {"recall": True, "level": recall.importance_level, "recall_id": recall.id}
        else:
            return {"recall": False, "level": None, "recall_id": None}


class CommentSerializer(serializers.ModelSerializer):
    replies_count = serializers.SerializerMethodField()
    user_name = serializers.ReadOnlyField(source="user.first_name")
    user_picture = serializers.ImageField(source="user.profile_picture", required=False, allow_null=True, use_url=True)
    formatted_created_time = serializers.SerializerMethodField()
    user_has_liked = serializers.SerializerMethodField()
    user_has_recalled = serializers.SerializerMethodField()
    commentor_last_badge = serializers.SerializerMethodField()

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

    def get_user_has_recalled(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return {"recall": False, "level": None, "recall_id": None}
        recall = RecallComment.objects.filter(user=user, comment=obj).first()
        if recall:
            return {"recall": True, "level": recall.importance_level, "recall_id": recall.id}
        else:
            return {"recall": False, "level": None, "recall_id": None}

    def get_commentor_last_badge(self, obj):
        user = obj.user
        last_badge = UserBadge.objects.filter(user=user).order_by("-awarded_at").first()
        if last_badge:
            badge_data = UserBadgeSerializer(last_badge).data
            badge_data["level_colors"] = BadgeLevels.get_colors(last_badge.level)
            return badge_data

        return None


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


class RecallBlockSerializer(serializers.ModelSerializer):

    class Meta:
        model = RecallBlock
        fields = "__all__"
        read_only_fields = (
            "created_time",
            "updated_time",
            "user",
        )


class RecallBlockDetailSerializer(serializers.ModelSerializer):
    block = BlockDetailSerializer()

    class Meta:
        model = RecallBlock
        fields = "__all__"
        read_only_fields = (
            "created_time",
            "updated_time",
            "user",
        )


class RecallCommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = RecallComment
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
                details["story_slug"] = like.content.story.slug if hasattr(like.content, "story") else None
                details["text"] = like.content.comment_text if hasattr(like.content, "comment_text") else None
        elif obj.notification_type == "reply":
            reply = Comment.objects.filter(id=obj.object_id).select_related("story", "parent").first()
            if reply:
                details["story"] = reply.story.title if reply.story else None
                details["story_id"] = reply.story.id if reply.story else None
                details["story_slug"] = reply.story.slug if reply.story else None
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
