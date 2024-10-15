from rest_framework import serializers

from .models import Space, MembershipRequest


class SpaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Space
        fields = ("name", "description", "image", "color", "owner", "access_type", "created_time", "updated_time")


class SpaceActiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Space
        fields = ("name", "image", "color", "slug")


class SpaceDetailSerializer(serializers.ModelSerializer):
    is_owner = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()
    members_count = serializers.SerializerMethodField()
    stories_count = serializers.SerializerMethodField()

    class Meta:
        model = Space
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "image",
            "color",
            "owner",
            "access_type",
            "created_time",
            "updated_time",
            "is_owner",
            "is_member",
            "members_count",
            "stories_count",
        )

    def get_is_owner(self, obj):
        user = self.context["request"].user
        return user.id == obj.owner.id

    def get_is_member(self, obj):
        user = self.context["request"].user
        return user == obj.owner or user in obj.admins.all() or user in obj.members.all()

    def get_members_count(self, obj):
        return obj.members.count()

    def get_stories_count(self, obj):
        return obj.stories.count()


class MembershipRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipRequest
        fields = "__all__"


class MembershipRequestUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipRequest
        fields = ["status"]
