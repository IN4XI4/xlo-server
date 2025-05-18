from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from .models import Comment, Notification, Like


@receiver(post_delete, sender=Comment)
def delete_comment_notifications(sender, instance, **kwargs):
    Notification.objects.filter(
        content_type=ContentType.objects.get_for_model(instance), object_id=instance.id
    ).delete()


@receiver(post_delete, sender=Like)
def delete_like_notifications(sender, instance, **kwargs):
    Notification.objects.filter(
        content_type=ContentType.objects.get_for_model(instance), object_id=instance.id
    ).delete()
