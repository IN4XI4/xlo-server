from celery import shared_task


@shared_task
def finalize_expired_attempt(attempt_id):
    from apps.attempts.models import Attempt
    from apps.attempts.services import process_finalization

    try:
        attempt = Attempt.objects.select_related("assessment", "user", "assessment__topic").get(pk=attempt_id)
    except Attempt.DoesNotExist:
        return

    if attempt.is_finished:
        return

    process_finalization(attempt, answers=[])
