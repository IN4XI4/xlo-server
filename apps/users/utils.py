from xloserver.constants import LEVEL_GROUPS


def get_user_level(user):
    """
    Returns numeric user level value.
    """
    if user.is_superuser or user.is_staff:
        return max(LEVEL_GROUPS.values())

    user_groups = user.groups.values_list("name", flat=True)
    max_level_value = 0

    for group in user_groups:
        level_value = LEVEL_GROUPS.get(group, 0)
        max_level_value = max(max_level_value, level_value)
    return max_level_value
