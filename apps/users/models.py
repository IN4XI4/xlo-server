import os

from django.db import models
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import AbstractUser, UserManager
from rest_framework.authtoken.models import Token


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


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    birthday = models.DateField(auto_now=False, auto_now_add=False, null=True, blank=True)
    profile_picture = models.ImageField(upload_to=content_file_name, null=True, blank=True)
    updated_time = models.DateField(auto_now=True)
    reset_code = models.CharField(max_length=50, null=True, blank=True)

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = MrvUserManager()


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
