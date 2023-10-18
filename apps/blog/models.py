import os

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from apps.users.models import CustomUser


def content_file_name(instance, filename):
    return os.path.join("gallery", filename)


class GalleryImage(models.Model):
    file_name = models.FileField(upload_to=content_file_name)

    def __str__(self):
        return str(self.file_name)


class Topic(models.Model):
    name = models.CharField(max_length=300)
    color = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name


def content_monster_file_name(instance, filename):
    return os.path.join("monsters_pics", filename)


class Monster(models.Model):
    name = models.CharField(max_length=100)
    biography = models.TextField(blank=True, null=True)
    picture = models.ImageField(upload_to=content_monster_file_name, null=True, blank=True)

    def __str__(self):
        return self.name


class Post(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    monster = models.ForeignKey(Monster, on_delete=models.CASCADE, blank=True, null=True)
    title = models.CharField(max_length=300)
    content = models.TextField()
    images = models.ManyToManyField(GalleryImage, blank=True)
    allow_comments = models.BooleanField(default=True)
    is_active = models.BooleanField(default=False)
    created_time = models.DateField(auto_now=False, auto_now_add=True)
    updated_time = models.DateField(auto_now=True)

    def __str__(self):
        return self.title


class BlockType(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


class Block(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    block_type = models.ForeignKey(BlockType, on_delete=models.CASCADE)
    content = models.TextField()

    def __str__(self):
        return f"{self.post.title} - {self.block_type.name}"


class Comment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    comment_text = models.CharField(max_length=250)
    is_active = models.BooleanField(default=False)
    created_time = models.DateField(auto_now=False, auto_now_add=True)
    updated_time = models.DateField(auto_now=True)

    def __str__(self):
        return self.comment_text


class Like(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    liked = models.BooleanField(default=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content = GenericForeignKey("content_type", "object_id")
    is_active = models.BooleanField(default=False)
    created_time = models.DateField(auto_now=False, auto_now_add=True)
    updated_time = models.DateField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "content_type", "object_id"], name="unique_like"),
        ]

    def __str__(self):
        return str(self.object_id)
