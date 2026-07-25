import re
import uuid

from xloserver.constants import USER_LEVELS, ACTIVITY_POINT_ACTIONS


def get_user_level(user):
    """
    Returns numeric and text user level value.
    """
    level_data = USER_LEVELS[min(user.level, len(USER_LEVELS) - 1)]
    return level_data["level"], level_data["name"]


def award_activity_points(user, action_key):
    """
    Dispatches a task to award activity points and check for level-up.
    """
    from apps.users.tasks import process_activity_points

    if action_key not in ACTIVITY_POINT_ACTIONS:
        return

    process_activity_points.delay(user.id, action_key)


def apply_level_up_if_needed(user):
    """
    Recalculates the user's level from their current points. If they leveled up,
    awards coins and creates a LEVEL_UP notification.

    Callers must have already locked the user row (select_for_update) within an
    atomic transaction, since level-up grants coins and must not be double-applied
    under concurrent point-earning actions.
    """
    from apps.blog.models import Notification
    from apps.wallet.models import CoinLedgerEntry

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
        idempotency_key=f"level_up_{user.id}_{current_level}_to_{new_level}",
    )

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


def generate_unique_username(email):
    """
    Derives a Django-valid, unique username from an email's local part.
    """
    from apps.users.models import CustomUser

    base = re.sub(r"[^\w.@+-]", "", email.split("@")[0]) or "user"
    username = base
    while CustomUser.objects.filter(username=username).exists():
        username = f"{base}_{uuid.uuid4().hex[:6]}"
    return username
