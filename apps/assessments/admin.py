from django.contrib import admin

from apps.assessments.models import Assessment, Question, Choice, AssessmentDifficultyRating, FollowAssessment


@admin.register(Choice)
class Choicedmin(admin.ModelAdmin):
    list_display = ("id", "question", "description", "correct_answer")
    list_filter = ("question",)
    search_fields = ("question",)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("description", "assessment", "is_active", "is_multiple_choice", "created_at", "updated_at")
    list_filter = ("assessment",)
    search_fields = ("assessment",)
    list_per_page = 100


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    readonly_fields = ("user_difficulty_rating", "average_score", "attempts_count")


admin.site.register(AssessmentDifficultyRating)
admin.site.register(FollowAssessment)
