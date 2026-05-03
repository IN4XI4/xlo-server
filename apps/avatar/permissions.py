from rest_framework import permissions


class UserUnlockedItemPermissions(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.user.is_superuser or obj.user_id == request.user.id


class AvatarPermissions(permissions.BasePermission):

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if view.action == "create":
            return False
        if view.action == "destroy":
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if view.action == "destroy":
            return False
        if view.action in ["update", "partial_update"]:
            return request.user.is_superuser or request.user.is_staff or obj.user_id == request.user.id
        return True
