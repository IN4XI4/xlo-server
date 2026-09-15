from datetime import timedelta

from django.contrib import admin

from apps.attempts.models import Attempt, QuestionAttempt, UserPoints


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = (
        "assessment",
        "user",
        "score",
        "approved",
        "duration",
        "start_time",
        "end_time",
        "is_finished",
    )
    list_filter = ("assessment",)
    search_fields = (
        "assessment__name",
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
    )
    list_select_related = ("assessment", "user")
    list_per_page = 100

    @admin.display(description="Duration")
    def duration(self, obj):
        if obj.duration_seconds is None:
            return ""
        return timedelta(seconds=round(obj.duration_seconds))


@admin.register(QuestionAttempt)
class QuestionAttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "attempt", "question", "is_correct")
    list_filter = ("attempt__assessment",)
    search_fields = ("question__description", "attempt__assessment__name")
    list_select_related = ("attempt", "question", "attempt__assessment")
    list_per_page = 100


@admin.register(UserPoints)
class UserPointsAdmin(admin.ModelAdmin):
    list_display = ("user", "category", "total_points", "average_score")
    list_filter = ("category",)
    search_fields = ("user__username", "user__first_name", "user__last_name", "user__email")
    list_select_related = ("user", "category")
    list_per_page = 100
