from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django_countries.serializer_fields import CountryField
from django.utils.timezone import now
from rest_framework import serializers

from apps.blog.models import Like, Story, Comment, UserStoryView
from apps.spaces.models import Space
from apps.users.models import ProfileColor, Experience, Gender, UserBadge, BadgeLevels, Follow
from apps.users.utils import get_user_level, mask_identifier
from xloserver.constants import get_level, USER_LEVELS


class ProfileColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileColor
        fields = "__all__"


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = "__all__"


class GenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gender
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True, required=True, style={"input_type": "password"})

    class Meta:
        model = get_user_model()
        fields = ("username", "email", "password", "password2")
        extra_kwargs = {"password": {"write_only": True, "style": {"input_type": "password"}}}

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("The password must be at least 8 characters long.")

        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("The password must contain at least one number.")

        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data.pop("password2", None)
        user = get_user_model().objects.create(**validated_data)
        user.set_password(password)
        user.save(update_fields=["password"])
        return user


class UserMeSerializer(serializers.ModelSerializer):
    picture = serializers.SerializerMethodField()
    user_level_display = serializers.SerializerMethodField()
    notifications = serializers.SerializerMethodField()
    profile_color = serializers.ReadOnlyField(source="profile_color.color")
    story_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    views_count = serializers.SerializerMethodField()
    is_creator = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "username",
            "first_name",
            "email",
            "date_joined",
            "picture",
            "user_level_display",
            "profile_color",
            "notifications",
            "coin_balance",
            "points",
            "active_days",
            "story_count",
            "likes_count",
            "views_count",
            "is_creator",
        ]

    def get_picture(self, obj):
        if obj.profile_picture:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.profile_picture.url)
        return None

    def get_user_level_display(self, obj):
        numeric_level, level_name = get_user_level(obj)
        return {"level_value": numeric_level, "level_name": level_name}

    def get_notifications(self, obj):
        unread = obj.notifications.filter(has_viewed=False)
        total_unread = unread.count()
        return {
            "has_unread": total_unread > 0,
            "total_unread": total_unread,
        }

    def get_story_count(self, obj):
        return obj.stories.count()

    def get_likes_count(self, obj):
        return obj.like_set.count()

    def get_views_count(self, obj):
        return obj.userstoryview_set.count()

    def get_is_creator(self, obj):
        if obj.is_anonymous:
            return False
        user_level_value, _ = get_user_level(obj)
        return user_level_value >= get_level("Creator") or obj.is_staff or obj.is_superuser


class CompleteUserSerializer(serializers.ModelSerializer):
    country = CountryField(name_only=True)
    user_level_display = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        exclude = ["password"]
        read_only_fields = [
            "email",
            "username",
            "is_superuser",
            "is_staff",
            "is_active",
            "groups",
            "user_permissions",
            "coin_balance",
            "coin_last_updated_at",
            "points",
            "level",
            "average_score",
            "active_days",
            "date_joined",
            "last_login",
            "reset_code",
            "google_id",
        ]

    def get_user_level_display(self, obj):
        numeric_level, level_name = get_user_level(obj)
        return {"level_value": numeric_level, "level_name": level_name}


class ReadOnlyUserSerializer(serializers.ModelSerializer):
    picture = serializers.SerializerMethodField()
    country = CountryField(name_only=True)
    country_flag = serializers.SerializerMethodField()
    birth_year = serializers.SerializerMethodField()
    badges_count = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "first_name",
            "last_name",
            "country",
            "country_flag",
            "points",
            "average_score",
            "picture",
            "birth_year",
            "profession",
            "level",
            "badges_count",
        ]

    def get_picture(self, obj):
        if obj.profile_picture:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.profile_picture.url)
        return None

    def get_country_flag(self, obj):
        request = self.context.get("request")
        if obj.country and request:
            flag_url = obj.country.flag
            return request.build_absolute_uri(flag_url)
        return None

    def get_birth_year(self, obj):
        return obj.birthday.year if obj.birthday else None

    def get_badges_count(self, obj):
        return obj.badges.count()


class UserBadgeInfoSerializer(serializers.ModelSerializer):
    next_badge_levels = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ["id", "next_badge_levels"]

    def get_next_badge_levels(self, obj):
        next_levels = {}

        badge_requirements = {
            "VETERAN": {
                3: "Bronze",
                6: "Silver",
                12: "Gold",
                18: "Obsidian",
                24: "Mixelo",
            },
            "STORYTELLER": {
                5: "Bronze",
                20: "Silver",
                50: "Gold",
                100: "Obsidian",
                200: "Mixelo",
            },
            "POPULAR": {
                5: "Bronze",
                20: "Silver",
                50: "Gold",
                100: "Obsidian",
                200: "Mixelo",
            },
            "COLLABORATOR": {
                10: "Bronze",
                30: "Silver",
                70: "Gold",
                130: "Obsidian",
                250: "Mixelo",
            },
            "EXPLORER": {
                15: "Bronze",
                50: "Silver",
                100: "Gold",
                200: "Obsidian",
                400: "Mixelo",
            },
        }

        user_progress = {
            "VETERAN": (now() - obj.date_joined).days // 30,
            "STORYTELLER": obj.stories.count(),
            "POPULAR": Like.objects.filter(
                content_type=ContentType.objects.get_for_model(Story),
                object_id__in=obj.stories.values_list("id", flat=True),
                liked=True,
            ).count()
            + Like.objects.filter(
                content_type=ContentType.objects.get_for_model(Comment),
                object_id__in=Comment.objects.filter(user=obj).values_list("id", flat=True),
                liked=True,
            ).count(),
            "COLLABORATOR": obj.comment_set.count(),
            "EXPLORER": UserStoryView.objects.filter(user=obj).count(),
        }
        earned_set = set(UserBadge.objects.filter(user=obj).values_list("badge_type", "level"))
        earned_current = {}
        for badge_type, levels in badge_requirements.items():
            for requirement, level in levels.items():
                if (badge_type, level) in earned_set:
                    earned_current[badge_type] = (requirement, level)

        for badge_type, levels in badge_requirements.items():
            current_level = earned_current.get(badge_type, (0, None))

            next_level = None
            for requirement, level in levels.items():
                if requirement > current_level[0]:
                    next_level = (requirement, level)
                    break

            if next_level is not None:
                progress = max(user_progress[badge_type] - current_level[0], 0)
                section = next_level[0] - current_level[0]
                percentage = min((progress / section) * 100, 100)
                next_levels[badge_type] = {"next_level": next_level[1], "percentage": round(percentage, 2)}
            else:
                next_levels[badge_type] = {"next_level": None, "percentage": 100}
        return next_levels


class UserDetailSerializer(serializers.ModelSerializer):
    country = CountryField(name_only=True)
    birth_year = serializers.SerializerMethodField()
    profile_color_value = serializers.ReadOnlyField(source="profile_color.color")
    experience_value = serializers.ReadOnlyField(source="experience.experience")
    country_flag = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()
    request_id = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "country",
            "gender",
            "first_name",
            "last_name",
            "email",
            "profile_picture",
            "profession",
            "experience",
            "biography",
            "linkedin_profile",
            "website",
            "birth_year",
            "profile_color_value",
            "country_flag",
            "experience_value",
            "request_id",
        ]

    def get_birth_year(self, obj):
        return obj.birthday.year if obj.birthday else None

    def get_country_flag(self, obj):
        request = self.context.get("request")
        if obj.country and request:
            flag_url = obj.country.flag
            return request.build_absolute_uri(flag_url)
        return None

    def get_profile_picture(self, obj):
        if obj.profile_picture:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.profile_picture.url)
        return None

    def get_request_id(self, obj):
        request_map = self.context.get("request_map", {})
        return request_map.get(obj.id)


class MaskedEmailUserDetailSerializer(UserDetailSerializer):
    """
    Same as UserDetailSerializer but the email is masked: juankrios15@gmail.com -> ju***@gmail.com
    """

    email = serializers.SerializerMethodField()

    def get_email(self, obj):
        return mask_identifier(obj.email)


class ProfileCountsMixin(serializers.Serializer):
    """
    Public counters shown on a user's profile page.
    """

    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    stories_count = serializers.SerializerMethodField()

    def get_followers_count(self, obj):
        return obj.followers.filter(follower__is_active=True).count()

    def get_following_count(self, obj):
        return obj.following.filter(followed__is_active=True).count()

    def get_stories_count(self, obj):
        return obj.stories.filter(is_active=True, is_private=False).count()


class UserProfileDetailSerializer(ProfileCountsMixin, UserDetailSerializer):
    """
    Profile page of any user, seen by an authenticated user. Hides the email.
    """

    level_progress = serializers.SerializerMethodField()

    class Meta(UserDetailSerializer.Meta):
        fields = [field for field in UserDetailSerializer.Meta.fields if field != "email"] + [
            "date_joined",
            "followers_count",
            "following_count",
            "stories_count",
            "level_progress",
        ]

    def get_level_progress(self, obj):
        level_index = min(obj.level, len(USER_LEVELS) - 1)
        current_level = USER_LEVELS[level_index]
        next_level = USER_LEVELS[level_index + 1] if level_index + 1 < len(USER_LEVELS) else None
        return {
            "level_value": current_level["level"],
            "level_name": current_level["name"],
            "points": obj.points,
            "next_level_name": next_level["name"] if next_level else None,
            "next_level_points": next_level["min_points"] if next_level else None,
        }


class OwnerUserProfileSerializer(UserProfileDetailSerializer):
    """
    Profile page of the authenticated user, seen by themselves.
    """

    attempts_count = serializers.SerializerMethodField()
    spaces_count = serializers.SerializerMethodField()

    class Meta(UserProfileDetailSerializer.Meta):
        fields = UserProfileDetailSerializer.Meta.fields + [
            "coin_balance",
            "attempts_count",
            "spaces_count",
        ]

    def get_attempts_count(self, obj):
        return obj.attempts.filter(is_finished=True).count()

    def get_spaces_count(self, obj):
        return Space.objects.filter(Q(owner=obj) | Q(admins=obj) | Q(members=obj)).distinct().count()


class PublicUserSerializer(ProfileCountsMixin, serializers.ModelSerializer):
    """
    Limited profile page of any user, seen by anonymous visitors.
    """

    country = CountryField(name_only=True)
    country_flag = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "first_name",
            "last_name",
            "profile_picture",
            "country",
            "country_flag",
            "profession",
            "date_joined",
            "followers_count",
            "following_count",
            "stories_count",
        ]

    def get_country_flag(self, obj):
        request = self.context.get("request")
        if obj.country and request:
            return request.build_absolute_uri(obj.country.flag)
        return None

    def get_profile_picture(self, obj):
        if obj.profile_picture:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.profile_picture.url)
        return None


class PasswordResetSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = ("password", "password2", "reset_code")


class UserBadgeSerializer(serializers.ModelSerializer):
    level_colors = serializers.SerializerMethodField()

    class Meta:
        model = UserBadge
        fields = "__all__"

    def get_level_colors(self, obj):
        return BadgeLevels.get_colors(obj.level)


class FollowSerializer(serializers.ModelSerializer):
    follower_username = serializers.SerializerMethodField()
    followed_username = serializers.SerializerMethodField()
    follower_first_name = serializers.ReadOnlyField(source="follower.first_name")
    followed_first_name = serializers.ReadOnlyField(source="followed.first_name")
    follower_last_name = serializers.ReadOnlyField(source="follower.last_name")
    followed_last_name = serializers.ReadOnlyField(source="followed.last_name")
    follower_profile_picture = serializers.SerializerMethodField()
    followed_profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = "__all__"
        read_only_fields = ["follower", "created_at"]

    def validate(self, data):
        user = self.context["request"].user
        if "followed" in data:
            if data["followed"] == user:
                raise serializers.ValidationError("A user cannot follow themselves.")
        else:
            raise serializers.ValidationError("'followed' field is required.")
        return data

    def get_follower_username(self, obj):
        return mask_identifier(obj.follower.username)

    def get_followed_username(self, obj):
        return mask_identifier(obj.followed.username)

    def get_follower_profile_picture(self, obj):
        if obj.follower.profile_picture:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.follower.profile_picture.url)
        return None

    def get_followed_profile_picture(self, obj):
        if obj.followed.profile_picture:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.followed.profile_picture.url)
        return None
