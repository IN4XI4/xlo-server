import os

from django.db import models
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import AbstractUser, UserManager
from rest_framework.authtoken.models import Token
from django_countries.fields import CountryField


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
    show_info = models.BooleanField(default=True)
    reset_code = models.CharField(max_length=50, null=True, blank=True)

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = MrvUserManager()


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
