from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from .models import Topic, Monster, Post, BlockType, Block, Comment, Like, GalleryImage


class GalleryImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GalleryImage
        fields = ("file_name",)


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = "__all__"


class MonsterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Monster
        fields = "__all__"


class PostSerializer(serializers.ModelSerializer):
    images = GalleryImageSerializer(many=True, required=False, write_only=True)

    class Meta:
        model = Post
        fields = "__all__"
        read_only_fields = ["is_active", "created_time", "updated_time", "user"]

    def create(self, validated_data):
        images_data = validated_data.pop("images", [])
        post = Post.objects.create(**validated_data)

        for image_data in images_data:
            GalleryImage.objects.create(post=post, **image_data)

        return post


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
