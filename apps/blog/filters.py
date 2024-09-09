from rest_framework.filters import BaseFilterBackend


class UserOwnedFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        user_owned = request.query_params.get("user_owned", None)
        if user_owned is not None and user_owned.lower() == "true":
            return queryset.filter(user=request.user)
        return queryset
