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


def story_image_upload_path(instance, filename):
    return f"story_{instance.id}/{filename}"


class Story(models.Model):
    DIFFICULTY_LEVELS = {
        1: ("Beginner", "#A8E6CF"),
        2: ("Amateur", "#FFD3B6"),
        3: ("Intermediate", "#FF8C42"),
        4: ("Professional", "#4A90E2"),
        5: ("Expert", "#6A0DAD"),
    }

    LANGUAGE_CHOICES = [
        ("EN", "English"),
        ("ES", "Spanish"),
        ("FR", "French"),
        ("DE", "German"),
        ("IT", "Italian"),
        ("PT", "Portuguese"),
        ("OT", "Other"),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="stories")
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, related_name="stories")
    title = models.CharField(max_length=300)
    subtitle = models.CharField(max_length=300, blank=True, null=True)
    image = models.ImageField(upload_to=story_image_upload_path, blank=True, null=True)
    difficulty_level = models.PositiveSmallIntegerField(
        choices=[(key, value[0]) for key, value in DIFFICULTY_LEVELS.items()], default=1
    )
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default="FR")
    is_active = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
    edited_time = models.DateTimeField(null=True, blank=True)
    views_count = models.IntegerField(default=0)
    slug = models.SlugField(max_length=320, blank=True, unique=True)
    free_access = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.edited_time:
            self.edited_time = self.created_time
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


def block_image_upload_path(instance, filename):
    return f"story_{instance.card.story.id}/card_{instance.card.id}/{filename}"


class Block(models.Model):

    BLOCK_TYPES = [
        (1, "STANDARD"),
        (2, "MONSTER"),
        (3, "MENTOR"),
        (4, "HERO"),
        (5, "HIGHLIGHT"),
        (6, "QUOTE"),
        (7, "FLASHCARD"),
        (8, "FACT"),
        (9, "WONDER"),
        (10, "QUESTION"),
        (11, "TESTIMONIAL"),
        (12, "REFLECTION"),
    ]

    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    block_class = models.PositiveSmallIntegerField(choices=BLOCK_TYPES, default=1) 
    content = models.TextField()
    image = models.ImageField(upload_to=block_image_upload_path, blank=True, null=True)
    order = models.IntegerField(default=0, blank=True)

    def __str__(self):
        return f"{self.card.title} - {self.get_block_class_display()}"


class Comment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies")
    comment_text = models.CharField(max_length=3000)
    is_active = models.BooleanField(default=False)
    created_time = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
    ask_for_help = models.BooleanField(default=False)
    likes = GenericRelation(Like)

    def __str__(self):
        return self.comment_text


class UserStoryView(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="user_views")

    class Meta:
        unique_together = ("user", "story")


class UserCardView(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="user_card_views")

    class Meta:
        unique_together = ("user", "card")


class RecallCard(models.Model):
    IMPORTANCE_LEVELS = [
        ("1", "Important"),
        ("2", "Very Important"),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="card_to_recall")
    importance_level = models.CharField(max_length=1, choices=IMPORTANCE_LEVELS, default="1")
    created_time = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "card")


class RecallBlock(models.Model):
    IMPORTANCE_LEVELS = [
        ("1", "Important"),
        ("2", "Vert Important"),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name="block_to_recall")
    importance_level = models.CharField(max_length=1, choices=IMPORTANCE_LEVELS, default="1")
    created_time = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "block")


class RecallComment(models.Model):
    IMPORTANCE_LEVELS = [
        ("1", "Important"),
        ("2", "Vert Important"),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="comment_to_recall")
    importance_level = models.CharField(max_length=1, choices=IMPORTANCE_LEVELS, default="1")
    created_time = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "comment")


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
