from rest_framework import permissions


class UserUnlockedItemPermissions(permissions.BasePermission):

    def has_permission(self, request, view):
        # Solo autenticados
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Solo lectura: dueño o superuser
        return request.user.is_superuser or obj.user_id == request.user.id
