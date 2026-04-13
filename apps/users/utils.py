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
