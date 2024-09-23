from rest_framework import serializers

from .models import Space, MembershipRequest


class SpaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Space
        fields = ("name", "description", "image", "color", "owner", "access_type", "created_time", "updated_time")


class MembershipRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipRequest
        fields = "__all__"


class MembershipRequestUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipRequest
        fields = ["status"]
