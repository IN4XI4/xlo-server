from rest_framework import permissions

from apps.users.utils import get_user_level
from xloserver.constants import LEVEL_GROUPS


class SpacePermissions(permissions.BasePermission):
    premium_required_level = LEVEL_GROUPS.get("premium", 0)

    def has_permission(self, request, view):
        if view.action in ["list", "retrieve"]:
            return request.user and request.user.is_authenticated

        if view.action == "create":
            user_level, _ = get_user_level(request.user)
            return user_level >= self.premium_required_level or request.user.is_superuser

        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        if view.action == "leave_space":
            return True
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.owner == request.user


class MembershipRequestPermissions(permissions.BasePermission):

    def has_permission(self, request, view):
        if view.action in ["list", "retrieve", "create"]:
            return request.user.is_authenticated

        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        if request.method in permissions.SAFE_METHODS:
            return user.is_authenticated

        if view.action == "destroy":
            return obj.user == user

        if view.action in ["update", "partial_update"]:
            return obj.space.owner == user or obj.space.admins.filter(id=user.id).exists()
        return False


class MembershipInvitationPermissions(permissions.BasePermission):

    def has_permission(self, request, view):
        if view.action in ["list", "retrieve", "create"]:
            return request.user.is_authenticated
        return True

    def has_object_permission(self, request, view, obj):
        user = request.user

        if view.action in ["update", "partial_update"]:
            return obj.user == user

        if view.action == "destroy":
            return obj.space.owner == user or obj.space.admins.filter(id=user.id).exists()

        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        return False
