from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django_countries.serializer_fields import CountryField
from django.utils.timezone import now
from rest_framework import serializers

from apps.blog.models import Like, Story, Comment, UserStoryView
from .models import ProfileColor, Experience, Gender, UserBadge, BadgeLevels
from apps.users.utils import get_user_level
from xloserver.constants import LEVEL_GROUPS


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
        user.save()
        return user


class UserMeSerializer(serializers.ModelSerializer):
    picture = serializers.SerializerMethodField()
    user_level = serializers.SerializerMethodField()
    notifications = serializers.SerializerMethodField()
    profile_color = serializers.ReadOnlyField(source="profile_color.color")

    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "username",
            "first_name",
            "email",
            "date_joined",
            "picture",
            "user_level",
            "profile_color",
            "notifications",
        ]

    def get_picture(self, obj):
        if obj.profile_picture:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.profile_picture.url)
        return None

    def get_user_level(self, obj):
        return get_user_level(obj)

    def get_notifications(self, obj):
        unread_notifications = obj.notifications.filter(has_viewed=False)
        notification_info = {
            "has_unread": unread_notifications.exists(),
            "like_count": unread_notifications.filter(notification_type="like").count(),
            "reply_count": unread_notifications.filter(notification_type="reply").count(),
        }
        return notification_info


class CompleteUserSerializer(serializers.ModelSerializer):
    country = CountryField(name_only=True)

    class Meta:
        model = get_user_model()
        fields = "__all__"


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
                20: "Bronze",
                30: "Silver",
                40: "Gold",
                55: "Obsidian",
                70: "Mixelo",
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
            "EXPLORER": (UserStoryView.objects.filter(user=obj).count() / max(Story.objects.count(), 1)) * 100,
        }
        for badge_type, levels in badge_requirements.items():
            current_level = (0, None)
            next_level = None
            for requirement, level in levels.items():
                if user_progress[badge_type] >= requirement:
                    current_level = (requirement, level)
                else:
                    next_level = (requirement, level)
                    break
            if next_level is not None:
                progress = user_progress[badge_type] - current_level[0]
                section = (next_level[0] - current_level[0])
                percentage = (progress/ section) * 100
                next_levels[badge_type] = {"next_level": next_level[1],  "percentage": round(percentage, 2)}
            else:
                next_levels[badge_type] =  {"next_level": None, "percentage": 100}
        return next_levels


class UserDetailSerializer(serializers.ModelSerializer):
    country = CountryField(name_only=True)
    birth_year = serializers.SerializerMethodField()
    profile_color_value = serializers.ReadOnlyField(source="profile_color.color")
    experience_value = serializers.ReadOnlyField(source="experience.experience")
    country_flag = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = [
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
        ]

    def get_birth_year(self, obj):
        return obj.birthday.year if obj.birthday else None

    def get_country_flag(self, obj):
        request = self.context.get("request")
        if obj.country and request:
            flag_url = obj.country.flag
            return request.build_absolute_uri(flag_url)
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
