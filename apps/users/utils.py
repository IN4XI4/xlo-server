from xloserver.constants import LEVEL_GROUPS


def get_user_level(user):
    """
    Returns numeric and text user level value.
    """
    if user.is_superuser or user.is_staff:
        highest_level_value = max(LEVEL_GROUPS.values())
        return highest_level_value, "Admin"

    user_groups = user.groups.values_list("name", flat=True)
    max_level_value = 0
    max_level_name = "Basic"

    for group in user_groups:
        level_value = LEVEL_GROUPS.get(group, 0)
        if level_value > max_level_value:
            max_level_value = level_value
            max_level_name = group

    return max_level_value, max_level_name
