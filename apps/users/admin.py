from django.contrib import admin

from apps.base.admin import ReadOnlyModelAdmin
from .models import ActivityPoints, CustomUser, Gender, Experience, ProfileColor, UserBadge


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    readonly_fields = ("coin_balance", "average_score", "points", "level")


admin.site.register(Gender)
admin.site.register(Experience)


@admin.register(ProfileColor)
class ProfileColorAdmin(admin.ModelAdmin):
    list_display = ("id", "color")
    list_filter = ("color",)
    search_fields = ("color",)
    list_per_page = 100


@admin.register(UserBadge)
class UserBadgeAdmin(ReadOnlyModelAdmin):
    list_display = ("id", "user", "badge_type", "level")
    list_filter = ("badge_type", "level")
    search_fields = ("user__username",)
    list_per_page = 100
    list_select_related = ("user",)
    readonly_fields = ("id", "user", "badge_type", "level")


@admin.register(ActivityPoints)
class ActivityPointsAdmin(ReadOnlyModelAdmin):
    list_display = ("id", "user", "action_key", "points", "created_at")
    list_filter = ("action_key",)
    search_fields = ("user__email",)
    list_per_page = 100
    list_select_related = ("user",)
    readonly_fields = ("id", "user", "action_key", "points", "created_at")
