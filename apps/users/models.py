import os
import random

from django.db import models
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import AbstractUser, UserManager
from rest_framework.authtoken.models import Token
from django_countries.fields import CountryField

from apps.avatar.items.item_colors import COLORS
from apps.avatar.items.skin_colors import SKIN_COLORS

class MrvUserManager(UserManager):
    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email=email, username=email, password=password, **extra_fields)


def content_file_name(instance, filename):
    return os.path.join("profile_pics", filename)


class ProfileColor(models.Model):
    color = models.CharField(max_length=10)

    def __str__(self):
        return str(self.color)


class Gender(models.Model):
    gender = models.CharField(max_length=50)

    def __str__(self):
        return str(self.gender)


class Experience(models.Model):
    experience = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Experience"
        verbose_name_plural = "Experience"

    def __str__(self):
        return str(self.experience)


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    birthday = models.DateField(auto_now=False, auto_now_add=False, null=True, blank=True)
    profile_picture = models.ImageField(upload_to=content_file_name, null=True, blank=True)
    updated_time = models.DateField(auto_now=True)
    profile_color = models.ForeignKey(ProfileColor, null=True, blank=True, on_delete=models.SET_NULL)
    gender = models.ForeignKey(Gender, null=True, blank=True, on_delete=models.SET_NULL)
    experience = models.ForeignKey(Experience, null=True, blank=True, on_delete=models.SET_NULL)
    biography = models.TextField(null=True, blank=True)
    profession = models.CharField(max_length=50, null=True, blank=True)
    website = models.CharField(max_length=50, null=True, blank=True)
    linkedin_profile = models.CharField(max_length=50, null=True, blank=True)
    country = CountryField(blank=True, null=True)
    reset_code = models.CharField(max_length=50, null=True, blank=True)
    active_days = models.IntegerField(default=0)

    # Settings fields:
    show_info = models.BooleanField(default=True)  # Shows detailed profile info to others
    email_weekly_recalls = models.BooleanField(default=True)  # Every week as a recall reminder
    email_new_stories = models.BooleanField(default=True)  # For liked topics
    email_reply = models.BooleanField(default=True)  # Everytime someone liked or replied your comment
    email_info = models.BooleanField(default=True)  # The admin is allowed to send emails anytime

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = MrvUserManager()


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


@receiver(post_save, sender=CustomUser)
def create_mentor_for_new_user(sender, instance, created, **kwargs):
    if created:
        from apps.base.models import Mentor

        Mentor.objects.create(user=instance, created_by=instance)

@receiver(post_save, sender=CustomUser)
def create_user_avatar(sender, instance, created, **kwargs):    
    if created:
        from apps.avatar.models import (
        Avatar,
        UserUnlockedItem,
        UserUnlockedColor,
        UserUnlockedSkinColor,
        UserUnlockedEyesColor,
    )

        face_item = UserUnlockedItem.objects.create(user=instance, item_code="BOY_FACE_1", item_type="FACE")
        hair_item = UserUnlockedItem.objects.create(user=instance, item_code="BOY_HAIR_1", item_type="HAIR")
        shirt_item = UserUnlockedItem.objects.create(user=instance, item_code="BOY_SHIRT_1", item_type="SHIRT")
        pants_item = UserUnlockedItem.objects.create(user=instance, item_code="BOY_PANT_1", item_type="PANTS")
        shoes_item = UserUnlockedItem.objects.create(user=instance, item_code="BOY_SHOE_1", item_type="SHOES")

        UserUnlockedItem.objects.create(user=instance, item_code="GIRL_FACE_1", item_type="FACE")
        UserUnlockedItem.objects.create(user=instance, item_code="GIRL_HAIR_1", item_type="HAIR")
        UserUnlockedItem.objects.create(user=instance, item_code="GIRL_SHIRT_1", item_type="SHIRT")
        UserUnlockedItem.objects.create(user=instance, item_code="GIRL_PANT_1", item_type="PANTS")
        UserUnlockedItem.objects.create(user=instance, item_code="GIRL_SHOE_1", item_type="SHOES")

        color = UserUnlockedColor.objects.create(user=instance, color_code="BLACK")
        skin_color = UserUnlockedSkinColor.objects.create(user=instance, color_code="SKIN_LIGHT")
        eyes_color = UserUnlockedEyesColor.objects.create(user=instance, color_code="BLACK")

        skin_options = [k for k in SKIN_COLORS.keys() if k != "SKIN_LIGHT"]
        color_options = [k for k in COLORS.keys() if k != "BLACK"]

        random_skin = random.choice(skin_options)
        random_color = random.choice(color_options)

        UserUnlockedSkinColor.objects.create(user=instance, color_code=random_skin)
        UserUnlockedColor.objects.create(user=instance, color_code=random_color)

        Avatar.objects.create(
            user=instance,
            face_item=face_item,
            hair_item=hair_item,
            hair_color=color,
            shirt_item=shirt_item,
            shirt_color=color,
            pants_item=pants_item,
            pants_color=color,
            shoes_item=shoes_item,
            shoes_color=color,
            eyes_color=eyes_color,
            skin_color=skin_color,
        )


class BadgeTypes(models.TextChoices):
    VETERAN = "VETERAN", "Veteran"
    STORYTELLER = "STORYTELLER", "Storyteller"
    POPULAR = "POPULAR", "Popular"
    COLLABORATOR = "COLLABORATOR", "Collaborator"
    EXPLORER = "EXPLORER", "Explorer"


_LEVEL_COLORS = {
    "Bronze": ("#A97142", "#F0DEA4"),
    "Silver": ("#A7A7A7", "#DCDCDC"),
    "Gold": ("#BC9313", "#E4D4A1"),
    "Obsidian": ("#3E2856", "#B2A9BB"),
    "Mixelo": ("#3DB1FF", "#B8E3FF"),
}


class BadgeLevels(models.TextChoices):
    BRONZE = "Bronze", "Bronze"
    SILVER = "Silver", "Silver"
    GOLD = "Gold", "Gold"
    OBSIDIAN = "Obsidian", "Obsidian"
    MIXELO = "Mixelo", "Mixelo"

    @classmethod
    def get_colors(cls, level):
        return _LEVEL_COLORS.get(level, ("#FFFFFF", "#000000"))


class UserBadge(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="badges")
    badge_type = models.CharField(max_length=20, choices=BadgeTypes.choices)
    level = models.CharField(max_length=20, choices=BadgeLevels.choices)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "badge_type", "level")

    def __str__(self):
        return f"{self.user.username} - {self.get_badge_type_display()} ({self.level})"
