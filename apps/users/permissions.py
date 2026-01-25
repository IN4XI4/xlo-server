from rest_framework import permissions


class UserPermissions(permissions.BasePermission):
    """
    Custom permission:
    - Require authentication for any action.
    - Only allow owners of an object to edit or delete it.
    """

    def has_permission(self, request, view):
        if view.action in ["create", "send_reset_code", "reset_password"]:
            return True

        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        return obj == request.user


class FollowPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            return request.user.is_authenticated
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.method == "DELETE":
            return obj.follower == request.user or obj.followed == request.user
        return False
