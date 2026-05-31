import random
from datetime import timedelta

from django.db.models import Q, Prefetch
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView

from apps.attempts.models import Attempt, QuestionAttempt, UserPoints
from apps.attempts.serializers import AttemptSerializer, QuestionAttemptSerializer, UserPointsSerializer
from apps.attempts.permissions import AttemptBasedPermissions
from apps.attempts.services import process_finalization, update_assessment_average_score, update_user_average_score
from apps.attempts.tasks import finalize_expired_attempt
from apps.assessments.models import Assessment, Question, Choice


class AttemptViewSet(viewsets.ModelViewSet):
    permission_classes = [AttemptBasedPermissions]
    serializer_class = AttemptSerializer
    filterset_fields = {
        "assessment": ("exact", "in"),
        "user": ("exact", "in"),
        "score": ("exact", "gte", "lte"),
        "approved": ("exact",),
        "start_time": ("exact", "gte", "lte"),
    }
    ordering_fields = ["start_time"]
    ordering = ["start_time"]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Attempt.objects.filter(Q(user=self.request.user) | Q(assessment__user=self.request.user))
        return Attempt.objects.none()

    def perform_create(self, serializer):
        assessment_id = self.request.data.get("assessment")
        try:
            assessment = Assessment.objects.get(pk=assessment_id, is_active=True)
        except Assessment.DoesNotExist:
            raise ValidationError("The specified assessment does not exist or is not active.")
        if assessment.user == self.request.user:
            raise ValidationError("You cannot attempt your own assessment.")

        previous_attempts_count = Attempt.objects.filter(assessment=assessment, user=self.request.user).count()
        perfect_score_exists = Attempt.objects.filter(assessment=assessment, user=self.request.user, score=100).exists()
        if previous_attempts_count >= assessment.allowed_attempts or perfect_score_exists:
            raise ValidationError("You don't have any attempts left for this assessment.")
        assessment.attempts_count = Attempt.objects.filter(assessment=assessment).count() + 1
        update_assessment_average_score(assessment)
        update_user_average_score(self.request.user)
        attempt = serializer.save(user=self.request.user)
        eta = attempt.start_time + timedelta(minutes=assessment.time_limit + 2)
        finalize_expired_attempt.apply_async(args=[attempt.id], eta=eta)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        # Getting random questions for attempt:
        if request.user == instance.user and not instance.questions_provided:
            assessment = instance.assessment
            number_of_questions = assessment.number_of_questions
            random_questions = Question.objects.filter(assessment=assessment).order_by("?")[:number_of_questions]
            random_questions_with_choices = random_questions.prefetch_related(
                Prefetch("choices", queryset=Choice.objects.all(), to_attr="fetched_choices")
            )
            questions_data = [
                {
                    "question_id": q.id,
                    "description": q.description,
                    "choices": [
                        {"choice_id": c.id, "description": c.description}
                        for c in random.sample(q.fetched_choices, len(q.fetched_choices))
                    ],
                }
                for q in random_questions_with_choices
            ]
            response_data = serializer.data
            response_data["questions"] = questions_data
            instance.questions_provided = True
            instance.save(update_fields=["questions_provided"])
            return Response(response_data)
        return Response(serializer.data)

    @action(detail=True, methods=["POST"])
    def finalize_attempt(self, request, pk=None):
        attempt = self.get_object()

        if attempt.is_finished:
            return Response(
                {
                    "detail": "Attempt finalized successfully.",
                    "score": attempt.score,
                    "approved": attempt.approved,
                    "points_obtained": attempt.points_obtained,
                },
                status=status.HTTP_200_OK,
            )

        now = timezone.now()
        expected_end_time = attempt.start_time + timedelta(minutes=attempt.assessment.time_limit, seconds=5)
        if now > expected_end_time:
            return Response(
                {"error": "The attempt exceeded the allowed time limit."}, status=status.HTTP_400_BAD_REQUEST
            )
        if not isinstance(request.data, list):
            return Response({"error": "Expected a list of answers."}, status=status.HTTP_400_BAD_REQUEST)

        attempt.end_time = now
        attempt = process_finalization(attempt, request.data)

        return Response(
            {
                "detail": "Attempt finalized successfully.",
                "score": attempt.score,
                "approved": attempt.approved,
                "points_obtained": attempt.points_obtained,
            },
            status=status.HTTP_200_OK,
        )


class QuestionAttemptViewSet(viewsets.ModelViewSet):
    permission_classes = [AttemptBasedPermissions]
    queryset = QuestionAttempt.objects.all()
    serializer_class = QuestionAttemptSerializer
    filterset_fields = {
        "attempt": ("exact", "in"),
        "question": ("exact", "in"),
        "selected_choices": ("exact", "in"),
        "is_correct": ("exact",),
    }

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return QuestionAttempt.objects.filter(attempt__assessment__user=self.request.user)
        return QuestionAttempt.objects.none()

    def perform_create(self, serializer):
        question = Question.objects.get(pk=self.request.data["question"])

        # Checking if answer is correct:
        correct_choices_ids = set(question.choices.filter(correct_answer=True).values_list("id", flat=True))
        selected_choices_ids = set([int(choice_id) for choice_id in self.request.data["selected_choices"]])

        is_correct = correct_choices_ids == selected_choices_ids
        serializer.save(is_correct=is_correct)


class GlobalStatsAPIView(APIView):
    def get(self, request, format=None):
        total_attempts = Attempt.objects.count()
        total_assessments = Assessment.objects.filter(is_active=True).count()
        stats_data = {"total_attempts": total_attempts, "total_assessments": total_assessments}
        return Response(stats_data, status=status.HTTP_200_OK)


class UserPointsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserPoints.objects.all()
    serializer_class = UserPointsSerializer
    filterset_fields = {
        "user": ("exact", "in"),
        "category": ("exact", "in"),
        "total_points": ("gte", "lte"),
        "average_score": ("gte", "lte"),
    }
    ordering_fields = ["total_points", "average_score"]
