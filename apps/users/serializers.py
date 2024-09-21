from django.contrib.auth import get_user_model
from django_countries.serializer_fields import CountryField
from rest_framework import serializers

from .models import ProfileColor, Experience, Gender
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
