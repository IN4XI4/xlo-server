from django.contrib import admin

# Register your models here.
from .models import CustomUser, Gender, Experience, ProfileColor, UserBadge


admin.site.register(CustomUser)
admin.site.register(Gender)
admin.site.register(Experience)


@admin.register(ProfileColor)
class ProfileColorAdmin(admin.ModelAdmin):
    list_display = ("id", "color")
    list_filter = ("color",)
    search_fields = ("color",)
    list_per_page = 100


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "badge_type", "level")
    list_filter = ("badge_type", "level")
    search_fields = ("user__username",)
    list_per_page = 100
