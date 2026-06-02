from django.db import transaction
from django.db.models import Avg
from django.utils import timezone


def calculate_points(assessment, score):
    D_teacher = assessment.difficulty
    D_students = assessment.user_difficulty_rating or D_teacher
    return round(score * ((D_teacher + D_students) / 20.0))


def update_assessment_average_score(assessment):
    from apps.attempts.models import Attempt

    avg_score = Attempt.objects.filter(assessment=assessment).aggregate(avg_score=Avg("score"))["avg_score"]
    assessment.average_score = avg_score or 0
    assessment.save()


def update_user_average_score(user, user_points=None):
    from apps.attempts.models import Attempt

    user.average_score = Attempt.objects.filter(user=user).aggregate(avg_score=Avg("score"))["avg_score"] or 0
    user.save()
    if user_points:
        category_attempts = Attempt.objects.filter(user=user, assessment__topic=user_points.category)
        user_points.average_score = category_attempts.aggregate(Avg("score"))["score__avg"] or 0
        user_points.save()


def process_finalization(attempt, answers):
    """
    Core finalization logic shared between the user-triggered endpoint and
    the auto-expiry Celery task. Pass answers=[] to finalize with score 0.
    Returns the finalized attempt, or the already-finished attempt if called twice.
    """
    from apps.assessments.models import Question
    from apps.attempts.models import Attempt, QuestionAttempt, UserPoints

    with transaction.atomic():
        attempt = Attempt.objects.select_for_update().get(pk=attempt.pk)

        if attempt.is_finished:
            return attempt

        question_attempts_to_create = []
        for answer in answers:
            question_id = answer.get("question_id")
            selected_choices = set(answer.get("choices", []))
            try:
                question = Question.objects.get(pk=question_id)
            except Question.DoesNotExist:
                continue
            correct_choices_ids = set(question.choices.filter(correct_answer=True).values_list("id", flat=True))
            is_correct = correct_choices_ids == selected_choices
            question_attempts_to_create.append(
                QuestionAttempt(attempt=attempt, question_id=question_id, is_correct=is_correct)
            )

        QuestionAttempt.objects.bulk_create(question_attempts_to_create)
        for qa, answer in zip(question_attempts_to_create, answers):
            qa.selected_choices.set(answer.get("choices", []))

        total_questions = attempt.assessment.number_of_questions
        correct_answers_count = attempt.question_attempts.filter(is_correct=True).count()
        attempt.score = (correct_answers_count / total_questions) * 100 if total_questions else 0
        attempt.approved = attempt.score >= attempt.assessment.min_score
        best_attempt = (
            Attempt.objects.filter(assessment=attempt.assessment, user=attempt.user)
            .exclude(pk=attempt.pk)
            .order_by("-score")
            .first()
        )

        raw_points = calculate_points(attempt.assessment, attempt.score)
        best_raw = calculate_points(attempt.assessment, best_attempt.score) if best_attempt else 0
        attempt.points_obtained = max(0, raw_points - best_raw)

        user_points = None
        if attempt.assessment.topic:
            user_points, _ = UserPoints.objects.get_or_create(
                user=attempt.user, category=attempt.assessment.topic, defaults={"total_points": 0}
            )

        if attempt.points_obtained > 0:
            attempt.user.points += attempt.points_obtained
            if user_points:
                user_points.total_points += attempt.points_obtained
            attempt.user.save()
            if user_points:
                user_points.save()

        attempt.is_finished = True
        attempt.end_time = attempt.end_time or timezone.now()
        attempt.save()

        update_user_average_score(attempt.user, user_points)
        update_assessment_average_score(attempt.assessment)

    return attempt
