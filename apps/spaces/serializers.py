from rest_framework import serializers

from apps.base.models import TopicTag
from .models import Space, MembershipRequest


class SpaceSerializer(serializers.ModelSerializer):
    category_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=True, allow_empty=False
    )
    isPrivate = serializers.BooleanField(write_only=True)
    members_count = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()
    has_membership_request = serializers.SerializerMethodField()

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
            "members_count",
            "is_member",
            "has_membership_request",
            "created_time",
            "updated_time",
            "category_ids",
            "isPrivate",
        )
        read_only_fields = ("owner", "created_time", "updated_time")

    def validate_color(self, value):
        if not value:
            raise serializers.ValidationError("This field is required.")
        return value

    def create(self, validated_data):
        category_ids = validated_data.pop("category_ids", [])
        is_private = validated_data.pop("isPrivate", False)
        validated_data["access_type"] = "private" if is_private else "free"
        space = Space.objects.create(**validated_data)
        space.categories.set(TopicTag.objects.filter(id__in=category_ids))
        return space

    def get_members_count(self, obj):
        member_ids = set(obj.members.values_list('id', flat=True))
        admin_ids = set(obj.admins.values_list('id', flat=True))
        member_ids.update(admin_ids)
        member_ids.add(obj.owner_id)
        return len(member_ids)

    def get_is_member(self, obj):
        user = self.context["request"].user
        return user == obj.owner or user in obj.admins.all() or user in obj.members.all()

    def get_has_membership_request(self, obj):
        user = self.context["request"].user
        return MembershipRequest.objects.filter(space=obj, user=user, request_type="request", status="pending").exists()


class SpaceActiveSerializer(serializers.ModelSerializer):
    color_name = serializers.ReadOnlyField(source="color.color")

    class Meta:
        model = Space
        fields = ("name", "image", "color", "slug", "color_name")


class SpaceDetailSerializer(serializers.ModelSerializer):
    color_name = serializers.ReadOnlyField(source="color.color")
    is_owner = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
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
            "color_name",
            "owner",
            "access_type",
            "created_time",
            "updated_time",
            "is_owner",
            "is_member",
            "is_admin",
            "members_count",
            "stories_count",
        )

    def get_is_owner(self, obj):
        user = self.context["request"].user
        return user.id == obj.owner.id

    def get_is_member(self, obj):
        user = self.context["request"].user
        return user == obj.owner or user in obj.admins.all() or user in obj.members.all()

    def get_is_admin(self, obj):
        user = self.context["request"].user
        return user in obj.admins.all()

    def get_members_count(self, obj):
        return obj.members.count()

    def get_stories_count(self, obj):
        return obj.stories.count()


class MembershipRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipRequest
        fields = "__all__"
        read_only_fields = ("user", "status", "request_type")


class MembershipRequestInvitationSerializer(serializers.ModelSerializer):
    space_slug = serializers.ReadOnlyField(source="space.slug")
    space_image = serializers.ImageField(source="space.image", required=False, allow_null=True, use_url=True)
    space_color = serializers.ReadOnlyField(source="space.color.color")
    space_name = serializers.ReadOnlyField(source="space.name")
    space_description = serializers.ReadOnlyField(source="space.description")

    class Meta:
        model = MembershipRequest
        fields = "__all__"


class MembershipRequestUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipRequest
        fields = ["status"]
