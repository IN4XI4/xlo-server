from django.urls import path, include
from rest_framework import routers

from apps.assessments.views import (
    AssessmentViewSet,
    QuestionViewSet,
    ChoiceViewSet,
    AssessmentDifficultyRatingViewSet,
    FollowAssessmentViewSet,
)


app_name = "assessments"

router = routers.DefaultRouter()
router.register(r"assessments", AssessmentViewSet, basename="assessments")
router.register(r"questions", QuestionViewSet, basename="questions")
router.register(r"choices", ChoiceViewSet, basename="choice")
router.register(r"assessments-difficulty", AssessmentDifficultyRatingViewSet, basename="assessmentsdifficulty")
router.register(r"follow-assessments", FollowAssessmentViewSet, basename="followassessments")


urlpatterns = [
    path("", include(router.urls)),
]
