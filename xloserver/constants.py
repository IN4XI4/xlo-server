USER_LEVELS = [
    # Basic
    {"level": 0, "name": "Basic", "nickname": "", "min_points": 0},
    # Commentor tier
    {"level": 1, "name": "Commentor", "nickname": "", "min_points": 100},
    {"level": 2, "name": "Commentor Lvl 2", "nickname": "", "min_points": 250},
    {"level": 3, "name": "Commentor Lvl 3", "nickname": "", "min_points": 450},
    # Creator tier
    {"level": 4, "name": "Creator", "nickname": "", "min_points": 700},
    {"level": 5, "name": "Creator Lvl 2", "nickname": "", "min_points": 1050},
    {"level": 6, "name": "Creator Lvl 3", "nickname": "", "min_points": 1500},
    # Contributor tier
    {"level": 7, "name": "Contributor", "nickname": "", "min_points": 2100},
    {"level": 8, "name": "Contributor Lvl 2", "nickname": "", "min_points": 2900},
    {"level": 9, "name": "Contributor Lvl 3", "nickname": "", "min_points": 3900},
    # Expert tier (5 levels)
    {"level": 10, "name": "Expert", "nickname": "", "min_points": 5200},
    {"level": 11, "name": "Expert Lvl 2", "nickname": "", "min_points": 6800},
    {"level": 12, "name": "Expert Lvl 3", "nickname": "", "min_points": 8800},
    {"level": 13, "name": "Expert Lvl 4", "nickname": "", "min_points": 11200},
    {"level": 14, "name": "Expert Lvl 5", "nickname": "", "min_points": 14000},
    # Mentor tier (5 levels)
    {"level": 15, "name": "Mentor", "nickname": "", "min_points": 17500},
    {"level": 16, "name": "Mentor Lvl 2", "nickname": "", "min_points": 21500},
    {"level": 17, "name": "Mentor Lvl 3", "nickname": "", "min_points": 26000},
    {"level": 18, "name": "Mentor Lvl 4", "nickname": "", "min_points": 31200},
    {"level": 19, "name": "Mentor Lvl 5", "nickname": "", "min_points": 37200},
    # Sage tier (5 levels)
    {"level": 20, "name": "Sage", "nickname": "", "min_points": 44000},
    {"level": 21, "name": "Sage Lvl 2", "nickname": "", "min_points": 52000},
    {"level": 22, "name": "Sage Lvl 3", "nickname": "", "min_points": 61000},
    {"level": 23, "name": "Sage Lvl 4", "nickname": "", "min_points": 71500},
    {"level": 24, "name": "Sage Lvl 5", "nickname": "", "min_points": 83500},
    # Mixelo tier (5 levels)
    {"level": 25, "name": "Mixelo", "nickname": "", "min_points": 97000},
    {"level": 26, "name": "Mixelo Lvl 2", "nickname": "", "min_points": 112000},
    {"level": 27, "name": "Mixelo Lvl 3", "nickname": "", "min_points": 129000},
    {"level": 28, "name": "Mixelo Lvl 4", "nickname": "", "min_points": 148000},
    {"level": 29, "name": "Mixelo Lvl 5", "nickname": "", "min_points": 170000},
]


def get_level(name):
    """Return the level number for a given level name (case-insensitive)."""
    name_lower = name.lower()
    return next((lvl["level"] for lvl in USER_LEVELS if lvl["name"].lower() == name_lower), 0)


ACTIVITY_POINT_ACTIONS = {
    "view_story": {"points": 5, "description": "View a story"},
    "comment_story": {"points": 25, "description": "Comment on a story"},
    "create_story": {"points": 90, "description": "Create a story"},
}
