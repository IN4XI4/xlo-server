from rest_framework import permissions

from apps.assessments.models import Question, Choice
from apps.users.utils import get_user_level
from xloserver.constants import get_level


class AssessmentPermissions(permissions.BasePermission):
    creator_required_level = get_level("Contributor Lvl 2")

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.method == "POST":
            if not request.user.is_authenticated:
                return False
            if view.action in ("create", "create_full"):
                user_level, _ = get_user_level(request.user)
                return (
                    user_level >= self.creator_required_level
                    or request.user.is_staff
                    or request.user.is_superuser
                )
            return True
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.user == request.user


class QuestionChoicePermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Question):
            owner = obj.assessment.user
        elif isinstance(obj, Choice):
            owner = obj.question.assessment.user
        else:
            return False
        return owner == request.user or request.user.is_staff or request.user.is_superuser


class AssessmentDifficultyRatingPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if view.action in ["update", "partial_update", "destroy"]:
            return obj.user == request.user
        return True


class FollowAssessmentPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            return request.user.is_authenticated
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.method == "DELETE":
            return obj.follower == request.user
        return False
