from django.db import models
from django.conf import settings
from django.utils.text import slugify

from apps.users.models import ProfileColor, CustomUser
from apps.base.models import TopicTag


class Space(models.Model):
    ACCESS_CHOICES = [
        ("free", "Free"),
        ("premium", "Premium"),
    ]

    name = models.CharField(max_length=250, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="spaces/images/", blank=True, null=True)
    color = models.ForeignKey(ProfileColor, on_delete=models.SET_NULL, null=True, blank=True, related_name="spaces")
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="owned_spaces")
    admins = models.ManyToManyField(CustomUser, related_name="admin_spaces", blank=True)
    members = models.ManyToManyField(CustomUser, related_name="member_spaces", blank=True)
    access_type = models.CharField(max_length=10, choices=ACCESS_CHOICES, default="free")
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
    categories = models.ManyToManyField(TopicTag, related_name="spaces", blank=True)
    slug = models.SlugField(max_length=320, blank=True, unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            name_words = self.name.split()[:4]
            short_name = " ".join(name_words)
            self.slug = slugify(short_name)

            original_slug = self.slug
            count = 0
            while Space.objects.filter(slug=self.slug).exists():
                count += 1
                self.slug = f"{original_slug}-{count}"
        super(Space, self).save(*args, **kwargs)

class MembershipRequest(models.Model):
    REQUEST_TYPE_CHOICES = [
        ("request", "User Request"),
        ("invite", "Space Invitation"),
    ]

    space = models.ForeignKey(Space, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    request_type = models.CharField(max_length=10, choices=REQUEST_TYPE_CHOICES)
    status = models.CharField(
        max_length=10, choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")]
    )
    created_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("space", "user")
