from django.db import models
from django.utils.text import slugify
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation

from apps.users.models import CustomUser
from apps.base.models import Topic, SoftSkill, Mentor


class Like(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    liked = models.BooleanField(default=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content = GenericForeignKey("content_type", "object_id")
    is_active = models.BooleanField(default=False)
    created_time = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "content_type", "object_id"], name="unique_like"),
        ]

    def __str__(self):
        return str(self.object_id)


class Story(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="stories")
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, related_name="stories")
    title = models.CharField(max_length=300)
    subtitle = models.CharField(max_length=300, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
    views_count = models.IntegerField(default=0)
    slug = models.SlugField(max_length=320, blank=True, unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            title_words = self.title.split()[:7]
            short_title = " ".join(title_words)
            self.slug = slugify(short_title)

            original_slug = self.slug
            count = 0
            while Story.objects.filter(slug=self.slug).exists():
                count += 1
                self.slug = f"{original_slug}-{count}"

        super(Story, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Story"
        verbose_name_plural = "Stories"
        ordering = ["id"]


def card_image_upload_path(instance, filename):
    return f"story_{instance.story.id}/{filename}"


class Card(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    soft_skill = models.ForeignKey(SoftSkill, on_delete=models.SET_NULL, blank=True, null=True)
    mentor = models.ForeignKey(Mentor, on_delete=models.SET_NULL, blank=True, null=True)
    title = models.CharField(max_length=300)
    allow_comments = models.BooleanField(default=True)
    created_time = models.DateField(auto_now=False, auto_now_add=True)
    updated_time = models.DateField(auto_now=True)

    def __str__(self):
        return self.title


class BlockType(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


def block_image_upload_path(instance, filename):
    return f"story_{instance.card.story.id}/card_{instance.card.id}/{filename}"


class Block(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    block_type = models.ForeignKey(BlockType, on_delete=models.SET_NULL, blank=True, null=True)
    content = models.TextField()
    image = models.ImageField(upload_to=block_image_upload_path, blank=True, null=True)
    order = models.IntegerField(default=0, blank=True)

    def __str__(self):
        return f"{self.card.title} - {self.block_type.name if self.block_type else 'No BlockType'}"


class Comment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies")
    comment_text = models.CharField(max_length=3000)
    is_active = models.BooleanField(default=False)
    created_time = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
    likes = GenericRelation(Like)

    def __str__(self):
        return self.comment_text


class UserStoryView(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="user_views")

    class Meta:
        unique_together = ("user", "story")


class RecallCard(models.Model):
    IMPORTANCE_LEVELS = [
        ("1", "Important"),
        ("2", "Vert Important"),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="card_to_recall")
    importance_level = models.CharField(max_length=1, choices=IMPORTANCE_LEVELS, default="1")
    created_time = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "card")


class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="notifications")
    date = models.DateTimeField(auto_now_add=True)
    notification_type = models.CharField(max_length=10, choices=(("reply", "Reply"), ("like", "Like")))
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    has_viewed = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user} - Type: {self.notification_type}"
