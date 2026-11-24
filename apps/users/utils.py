import re
import uuid
from collections import defaultdict
from datetime import datetime, time, timedelta

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from xloserver.constants import (
    ACTIVITY_HEATMAP_DAYS,
    ACTIVITY_LEVEL_MIN_POINTS,
    ACTIVITY_POINT_ACTIONS,
    CATEGORY_SCALE_STEPS,
    TOPIC_TAGS_CACHE_KEY,
    TOPIC_TAGS_CACHE_TIMEOUT,
    USER_LEVELS,
)


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

    action = ACTIVITY_POINT_ACTIONS.get(action_key)
    # Actions with variable points are granted by the caller via grant_points.
    if not action or action["points"] is None:
        return

    process_activity_points.delay(user.id, action_key)


def get_profile_stats(user, days):
    """
    Returns the profile stats cards (points, stories viewed, likes received, pass rate)
    of the given user over the last `days` days, today included.
    """
    end = timezone.localdate()
    start = end - timedelta(days=days - 1)
    # All-time history, shared by the points and stories viewed cards; each one takes
    # the days it needs.
    daily_activity = get_daily_activity(user)

    return {
        "days": days,
        "points": get_counter_stats(get_daily_points(daily_activity), start, end, user.points),
        "stories_viewed": get_stories_viewed_stats(user, start, end, daily_activity),
        "likes_received": get_likes_received_stats(user, start, end),
        "pass_rate": get_pass_rate_stats(user, start, end),
    }


def get_daily_activity(user):
    """
    All of the user's ActivityPoints aggregated per day and action:
    {(day, action_key): {"points": ..., "count": ...}}. One row per active day and
    action, so it stays small even for the whole history.
    """
    from apps.users.models import ActivityPoints

    return {
        (row["day"], row["action_key"]): row
        for row in ActivityPoints.objects.filter(user=user)
        .annotate(day=TruncDate("created_at"))
        .values("day", "action_key")
        .annotate(points=Sum("points"), count=Count("id"))
    }


def get_daily_points(daily_activity):
    """
    Total points per day from get_daily_activity: {day: points}.
    """
    daily_points = defaultdict(int)
    for (day, _), row in daily_activity.items():
        daily_points[day] += row["points"]
    return daily_points


def get_activity_stats(user):
    """
    Learning activity of a user (public): a heatmap of the last ACTIVITY_HEATMAP_DAYS
    days (points earned and intensity level per day), current and longest streaks of
    days with points, and the number of distinct cards read and stories viewed.
    """
    from apps.blog.models import UserCardView, UserStoryView

    daily_points = get_daily_points(get_daily_activity(user))
    end = timezone.localdate()
    start = end - timedelta(days=ACTIVITY_HEATMAP_DAYS - 1)
    heatmap = []
    for offset in range(ACTIVITY_HEATMAP_DAYS):
        day = start + timedelta(days=offset)
        points = daily_points.get(day, 0)
        level = sum(points >= min_points for min_points in ACTIVITY_LEVEL_MIN_POINTS)
        heatmap.append({"date": day.isoformat(), "points": points, "level": level})

    active_days = {day for day, points in daily_points.items() if points > 0}

    longest_streak = 0
    for day in active_days:
        if day - timedelta(days=1) not in active_days:  # first day of a streak
            length = 1
            while day + timedelta(days=length) in active_days:
                length += 1
            longest_streak = max(longest_streak, length)

    # A streak still alive today counts until the day ends: start from yesterday if today has no points yet.
    day = end if end in active_days else end - timedelta(days=1)
    current_streak = 0
    while day in active_days:
        current_streak += 1
        day -= timedelta(days=1)

    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "cards_read": UserCardView.objects.filter(user=user).count(),
        "stories_viewed": UserStoryView.objects.filter(user=user).count(),
        "days": heatmap,
    }


def get_categories_stats(user):
    """
    Stories read per category (TopicTag) of a user (public), every category included,
    most read first, plus the scale_max the bars are drawn against.
    """
    from django.core.cache import cache
    from apps.base.models import TopicTag
    from apps.blog.models import UserStoryView

    # Same for every user and rarely changes; invalidated on TopicTag save/delete.
    categories = cache.get_or_set(
        TOPIC_TAGS_CACHE_KEY,
        lambda: list(TopicTag.objects.order_by("id").values("id", "name", "color")),
        TOPIC_TAGS_CACHE_TIMEOUT,
    )
    stories_read = dict(
        UserStoryView.objects.filter(user=user, story__topic__tag__isnull=False)
        .values("story__topic__tag")
        .annotate(total=Count("id"))
        .values_list("story__topic__tag", "total")
    )

    rows = [{**category, "stories_read": stories_read.get(category["id"], 0)} for category in categories]
    rows.sort(key=lambda row: (-row["stories_read"], row["id"]))
    return {
        "scale_max": get_scale_max(max((row["stories_read"] for row in rows), default=0)),
        "categories": rows,
    }


def get_scale_max(value):
    """
    First round number strictly above value (CATEGORY_SCALE_STEPS, then doubling), so
    the longest bar is never drawn full: 43 -> 50, 50 -> 100, 130 -> 200, 0 -> 10.
    """
    for step in CATEGORY_SCALE_STEPS:
        if value < step:
            return step
    scale_max = CATEGORY_SCALE_STEPS[-1]
    while scale_max <= value:
        scale_max *= 2
    return scale_max


def get_stories_viewed_stats(user, start, end, daily_activity):
    """
    Stories viewed card: distinct stories the user has opened. Each first view logs a
    view_story ActivityPoints entry, which gives the date; the total comes from
    UserStoryView, which also has the views from before ActivityPoints existed.
    """
    from apps.blog.models import UserStoryView

    daily_views = {day: row["count"] for (day, action_key), row in daily_activity.items() if action_key == "view_story"}
    return get_counter_stats(daily_views, start, end, UserStoryView.objects.filter(user=user).count())


def get_likes_received_stats(user, start, end):
    """
    Likes received card: likes from other users on the user's stories and comments.
    """
    from django.contrib.contenttypes.models import ContentType
    from apps.blog.models import Comment, Like, Story

    content_types = ContentType.objects.get_for_models(Story, Comment)
    # All-time likes per day in a single query; the story and comment ids go as subqueries.
    daily_likes = dict(
        Like.objects.filter(liked=True)
        .filter(
            Q(content_type=content_types[Story], object_id__in=Story.objects.filter(user=user).values("id"))
            | Q(content_type=content_types[Comment], object_id__in=Comment.objects.filter(user=user).values("id"))
        )
        .exclude(user=user)
        .annotate(day=TruncDate("created_time"))
        .values("day")
        .annotate(total=Count("id"))
        .values_list("day", "total")
    )

    return get_counter_stats(daily_likes, start, end, sum(daily_likes.values()))


def get_pass_rate_stats(user, start, end):
    """
    Pass rate card: share of the user's finished attempts that were approved (all
    time), plus a daily series of that cumulative pass rate over [start, end].
    """
    from apps.attempts.models import Attempt

    # All-time counts per day in a single query: one row per day with attempts, which
    # stays small since each assessment allows few attempts.
    daily_counts = {
        row["day"]: row
        for row in Attempt.objects.filter(user=user, is_finished=True, end_time__isnull=False)
        .annotate(day=TruncDate("end_time"))
        .values("day")
        .annotate(attempts=Count("id"), passed=Count("id", filter=Q(approved=True)))
    }
    total_attempts = sum(row["attempts"] for row in daily_counts.values())
    total_passed = sum(row["passed"] for row in daily_counts.values())

    # Start from the counts before the period and accumulate day by day.
    attempts = sum(row["attempts"] for day, row in daily_counts.items() if day < start)
    passed = sum(row["passed"] for day, row in daily_counts.items() if day < start)
    series = []
    for offset in range((end - start).days + 1):
        day = start + timedelta(days=offset)
        if day in daily_counts:
            attempts += daily_counts[day]["attempts"]
            passed += daily_counts[day]["passed"]
        series.append({"date": day.isoformat(), "value": get_rate(passed, attempts)})

    return {
        "value": get_rate(total_passed, total_attempts),
        "passed": total_passed,
        "attempts": total_attempts,
        "series": series,
    }


def get_counter_stats(daily_values, start, end, total):
    """
    Card for a counter that only grows (points, stories viewed, likes): the amount in
    [start, end] vs the previous period of the same length, and a daily cumulative
    series that ends at `total`. `daily_values` maps each day to its amount and must
    cover at least both periods.
    """
    previous_start = start - (end - start) - timedelta(days=1)
    in_period = sum(value for day, value in daily_values.items() if start <= day <= end)
    previous_period = sum(value for day, value in daily_values.items() if previous_start <= day < start)

    return {
        "total": total,
        "in_period": in_period,
        "previous_period": previous_period,
        "change_pct": get_change_pct(in_period, previous_period),
        # Clamped at 0 in case the total lost entries the daily log still has (e.g. a deleted story).
        "series": build_cumulative_series(daily_values, start, end, max(total - in_period, 0)),
    }


def build_cumulative_series(daily_values, start, end, baseline):
    """
    Returns one {"date", "value"} entry per day in [start, end], where value is
    baseline plus everything accumulated up to that day. Days without data repeat
    the previous value.
    """
    series = []
    running = baseline
    for offset in range((end - start).days + 1):
        day = start + timedelta(days=offset)
        running += daily_values.get(day, 0)
        series.append({"date": day.isoformat(), "value": running})
    return series


def get_change_pct(current, previous):
    """
    Percentage change between two periods, or None when there is nothing to compare against.
    """
    if not previous:
        return None
    return round((current - previous) / previous * 100, 1)


def get_rate(part, total):
    """
    Percentage of part over total, or None when total is 0.
    """
    if not total:
        return None
    return round(part / total * 100, 1)


def start_of_day(day):
    """
    Aware datetime at 00:00 of the given date, to filter datetime fields by day.
    """
    return timezone.make_aware(datetime.combine(day, time.min))


def grant_points(user_id, action_key, points):
    """
    Logs the points in ActivityPoints and adds them to the user's total.

    Must be called inside an atomic transaction so the log entry and the user's
    total are saved together. Does not check for level-up; callers handle it.
    """
    from django.db.models import F
    from apps.users.models import ActivityPoints, CustomUser

    ActivityPoints.objects.create(user_id=user_id, action_key=action_key, points=points)
    CustomUser.objects.filter(pk=user_id).update(points=F("points") + points)


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


def mask_identifier(value):
    """
    Masks an email or username for display: juankrios15@gmail.com -> ju***@gmail.com, juanrios -> ju***
    """
    local, at, domain = (value or "").partition("@")
    return f"{local[:2]}***{at}{domain}"


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
