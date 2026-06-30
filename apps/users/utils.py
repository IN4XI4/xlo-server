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
