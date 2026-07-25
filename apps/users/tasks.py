from celery import shared_task
from django.db import transaction
from django.db.models import F


@shared_task
def process_activity_points(user_id, action_key):
    from apps.users.models import ActivityPoints, CustomUser
    from apps.users.utils import apply_level_up_if_needed
    from xloserver.constants import ACTIVITY_POINT_ACTIONS

    action = ACTIVITY_POINT_ACTIONS.get(action_key)
    if not action:
        return

    points = action["points"]

    with transaction.atomic():
        user = CustomUser.objects.select_for_update().get(pk=user_id)

        ActivityPoints.objects.create(user=user, action_key=action_key, points=points)
        CustomUser.objects.filter(pk=user_id).update(points=F("points") + points)
        user.refresh_from_db(fields=["points"])

        apply_level_up_if_needed(user)


@shared_task
def check_level_up(user_id):
    from apps.users.models import CustomUser
    from apps.users.utils import apply_level_up_if_needed

    with transaction.atomic():
        user = CustomUser.objects.select_for_update().get(pk=user_id)
        apply_level_up_if_needed(user)
