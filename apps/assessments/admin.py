from django.contrib import admin

from apps.assessments.models import Assessment, Question, Choice, AssessmentDifficultyRating, FollowAssessment


@admin.register(Choice)
class Choicedmin(admin.ModelAdmin):
    list_display = ("id", "description", "question", "correct_answer")
    list_filter = ("question__assessment",)
    search_fields = ("description", "question__description", "question__assessment__name")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("description", "assessment", "is_multiple_choice", "created_at", "updated_at")
    list_filter = ("assessment",)
    search_fields = ("description", "assessment__name")
    list_per_page = 100


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    readonly_fields = ("user_difficulty_rating", "average_score", "attempts_count")
    list_display = (
        "name",
        "user",
        "topic",
        "language",
        "difficulty",
        "attempts_count",
        "average_score",
        "created_at",
    )
    list_filter = ("language", "is_private", "created_at", "topic")
    search_fields = ("name", "user__username", "user__first_name", "user__last_name", "user__email")
    list_select_related = ("user", "topic")
    list_per_page = 100


@admin.register(AssessmentDifficultyRating)
class AssessmentDifficultyRatingAdmin(admin.ModelAdmin):
    list_display = ("id", "assessment", "user", "difficulty", "created_at", "updated_at")
    list_filter = ("difficulty", "created_at")
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "assessment__name",
    )
    list_select_related = ("assessment", "user")
    list_per_page = 100


@admin.register(FollowAssessment)
class FollowAssessmentAdmin(admin.ModelAdmin):
    list_display = ("id", "follower", "assessment", "created_at")
    list_filter = ("assessment",)
    search_fields = ("assessment__name", "follower__username", "follower__first_name", "follower__last_name")
    list_select_related = ("follower", "assessment")
    list_per_page = 100
