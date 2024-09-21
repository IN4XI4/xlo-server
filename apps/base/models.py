from django.db import models
from django.dispatch import receiver
from django.utils.text import slugify
from django.db.models.signals import post_save
from ckeditor.fields import RichTextField

from .tasks import send_info_emails
from apps.users.models import CustomUser


class TopicTag(models.Model):
    name = models.CharField(max_length=300)
    color = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"


class Topic(models.Model):
    title = models.CharField(max_length=300)
    image = models.ImageField(upload_to="topics/", blank=True, null=True)
    tag = models.ForeignKey(TopicTag, on_delete=models.SET_NULL, null=True, blank=True)
    slug = models.SlugField(max_length=320, blank=True, unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            title_words = self.title.split()[:7]
            short_title = " ".join(title_words)
            self.slug = slugify(short_title)

            original_slug = self.slug
            count = 0
            while Topic.objects.filter(slug=self.slug).exists():
                count += 1
                self.slug = f"{original_slug}-{count}"

        super(Topic, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["id"]


class SoftSkill(models.Model):
    name = models.CharField(max_length=250)
    description = models.CharField(max_length=300)
    color = models.CharField(max_length=50, blank=True, null=True)
    monster_name = models.CharField(max_length=100, blank=True, null=True)
    monster_profile = models.TextField(blank=True, null=True)
    monster_picture = models.ImageField(upload_to="monsters_pics/", null=True, blank=True)
    logo = models.FileField(upload_to="logos/", null=True, blank=True)

    def __str__(self):
        return self.name


class Mentor(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="mentor", null=True, blank=True)
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, related_name="created_mentors", null=True, blank=True
    )
    name = models.CharField(max_length=100, blank=True)
    job = models.CharField(max_length=100, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    profile = models.TextField(blank=True, null=True)
    picture = models.ImageField(upload_to="mentors_pics/", null=True, blank=True)

    def __str__(self):
        return self.name if self.name else ""


class EmailSending(models.Model):
    TEMPLATE_CHOICES = [
        ("send_info_with_username", "Send Info with Username"),
    ]
    subject = models.CharField(max_length=200)
    body = RichTextField()
    template = models.CharField(max_length=50, choices=TEMPLATE_CHOICES, default="send_info_with_username")
    created_time = models.DateTimeField(auto_now=False, auto_now_add=True)

    def send_emails(self):
        send_info_emails.delay(self.subject, self.body, self.template)


@receiver(post_save, sender=EmailSending)
def send_email_on_create(sender, instance, created, **kwargs):
    if created:
        instance.send_emails()
