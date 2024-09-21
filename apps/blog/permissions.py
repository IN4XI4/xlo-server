from rest_framework import permissions

from .models import Story, Card

from apps.users.utils import get_user_level
from xloserver.constants import LEVEL_GROUPS

class IsStaffOrSuperUser(permissions.BasePermission):
    """
    Custom permission to only allow staff or superusers to access a view or action.
    """

    def has_permission(self, request, view):
        return request.user and (request.user.is_staff or request.user.is_superuser)


class StoryPermissions(permissions.BasePermission):
    commentor_required_value = LEVEL_GROUPS.get("commentor", 0)
    creator_required_value = LEVEL_GROUPS.get("creator", 0)
    """
    Custom permission:
    - Require authentication for any action.
    - Only allow owners of an object to edit or delete it.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if view.action == "create":
            user_level = get_user_level(request.user)
            return (
                user_level >= self.creator_required_value
                or request.user.is_staff
                or request.user.is_superuser
            )

        return True

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.user == request.user


class CardPermissions(StoryPermissions):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if view.action == "create":
            user_level = get_user_level(request.user)
            has_create_permission = (
                user_level >= self.creator_required_value
                or request.user.is_staff
                or request.user.is_superuser
            )
            if not has_create_permission:
                return False
            story_id = request.data.get("story")
            if not story_id:
                return False
            try:
                story = Story.objects.get(id=story_id)
                return story.user == request.user
            except Card.DoesNotExist:
                return False

        return True


class BlockPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if view.action == "create":
            user_level = get_user_level(request.user)
            has_create_permission = (
                user_level >= self.creator_required_value
                or request.user.is_staff
                or request.user.is_superuser
            )
            if not has_create_permission:
                return False
            card_id = request.data.get("card")
            if not card_id:
                return False
            try:
                card = Card.objects.get(id=card_id)
                return card.story.user == request.user
            except Card.DoesNotExist:
                return False

        return True

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.card.story.user == request.user


class CommentPermissions(StoryPermissions):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if view.action == "create":
            user_level = get_user_level(request.user)
            return (
                user_level >= self.commentor_required_value
                or request.user.is_staff
                or request.user.is_superuser
            )
        return True


class RecallLikePermissions(permissions.BasePermission):
    """
    Custom permission for RecallLike model:
    - All authenticated users can create data.
    - Only the user who created the data or superusers can edit or delete it.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user or request.user.is_superuser


class NotificationPermissions(permissions.BasePermission):
    """
    Custom permissions for Notification model:
    - Notifications creation is not allowed from the endpoint.
    - Staff or superusers can view all notifications.
    - Regular users can view or delete their own notifications.
    """

    def has_permission(self, request, view):
        if request.method == "POST":
            return False

        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_superuser
