from rest_framework import permissions

from .models import Attempt


class AttemptBasedPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action == "create":
            return request.user.is_authenticated
        # TODO: Solo creator level 4.
        if view.action in ["update", "partial_update", "destroy"]:
            return False

        return True

    def has_object_permission(self, request, view, obj):
        if view.action == "finalize_attempt":
            return obj.user == request.user

        return True
