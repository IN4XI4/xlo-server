from celery import shared_task
from django.db import transaction
from django.db.models import F


@shared_task
def process_activity_points(user_id, action_key):
    from apps.users.models import ActivityPoints, CustomUser
    from apps.wallet.models import CoinLedgerEntry
    from xloserver.constants import ACTIVITY_POINT_ACTIONS, USER_LEVELS

    action = ACTIVITY_POINT_ACTIONS.get(action_key)
    if not action:
        return

    points = action["points"]

    with transaction.atomic():
        user = CustomUser.objects.select_for_update().get(pk=user_id)

        ActivityPoints.objects.create(user=user, action_key=action_key, points=points)
        CustomUser.objects.filter(pk=user_id).update(points=F("points") + points)
        user.refresh_from_db(fields=["points"])

        current_level = user.level
        new_level = 0
        for level_data in reversed(USER_LEVELS):
            if user.points >= level_data["min_points"]:
                new_level = level_data["level"]
                break

        if new_level <= current_level:
            return

        levels_gained = new_level - current_level
        coins_to_award = levels_gained * 10

        user.level = new_level
        user.coin_balance = user.coin_balance + coins_to_award
        user.save(update_fields=["level", "coin_balance"])

        CoinLedgerEntry.objects.create(
            user=user,
            entry_type=CoinLedgerEntry.Type.CREDIT,
            amount=coins_to_award,
            reference_id="level_up",
            idempotency_key=f"level_up_{user_id}_{current_level}_to_{new_level}",
        )

        from apps.blog.models import Notification
        new_level_name = USER_LEVELS[new_level]["name"]
        Notification.objects.create(
            user=user,
            notification_type=Notification.Type.LEVEL_UP,
            metadata={
                "new_level": new_level,
                "new_level_name": new_level_name,
                "coins_awarded": coins_to_award,
            },
        )
