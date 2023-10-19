from rest_framework import permissions

from .models import Story, Card


class IsStaffOrSuperUser(permissions.BasePermission):
    """
    Custom permission to only allow staff or superusers to access a view or action.
    """

    def has_permission(self, request, view):
        return request.user and (request.user.is_staff or request.user.is_superuser)


class StoryPermissions(permissions.BasePermission):
    """
    Custom permission:
    - Require authentication for any action.
    - Only allow owners of an object to edit or delete it.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if view.action == "create":
            return (
                request.user.groups.filter(name="creator").exists()
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
            has_create_permission = (
                request.user.groups.filter(name="creator").exists()
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


class BlockPermissions(StoryPermissions):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if view.action == "create":
            has_create_permission = (
                request.user.groups.filter(name="creator").exists()
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


class CommentPermissions(StoryPermissions):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if view.action == "create":
            return (
                request.user.groups.filter(name__in=["commentor", "creator"]).exists()
                or request.user.is_staff
                or request.user.is_superuser
            )
        return True
