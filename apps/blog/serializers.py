from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from .models import Story, Card, BlockType, Block, Comment, Like


class StorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Story
        fields = "__all__"
        read_only_fields = ["is_active", "created_time", "updated_time", "user"]


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = "__all__"
        read_only_fields = ["created_time", "updated_time"]


class BlockTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockType
        fields = "__all__"


class BlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = "__all__"


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = "__all__"
        read_only_fields = ["is_active", "created_time", "updated_time", "user"]


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = "__all__"
        read_only_fields = ["is_active", "created_time", "updated_time"]


class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = "__all__"
