from rest_framework import permissions

from apps.users.utils import get_user_level
from xloserver.constants import LEVEL_GROUPS


class MentorPermissions(permissions.BasePermission):
    creator_lvl_3_required_value = LEVEL_GROUPS.get("creator lvl 3", 0)
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
            return user_level >= self.creator_lvl_3_required_value

        return True

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.created_by == request.user or request.user.is_superuser
