from django.contrib import admin

from apps.avatar.models import Avatar, UserUnlockedItem, UserUnlockedColor, UserUnlockedSkinColor, UserUnlockedEyesColor


@admin.register(UserUnlockedItem)
class UserUnlockedItemAdmin(admin.ModelAdmin):
    list_display = ("user", "item_code", "item_type", "unlocked_at")
    list_filter = ("item_type", "item_code")
    search_fields = ("user__username", "user__email", "item_code")
    list_per_page = 100


@admin.register(UserUnlockedColor)
class UserUnlockedColorAdmin(admin.ModelAdmin):
    list_display = ("user", "color_code", "unlocked_at")
    search_fields = ("user__username", "user__email", "color_code")
    list_per_page = 100


@admin.register(UserUnlockedSkinColor)
class UserUnlockedSkinColorAdmin(admin.ModelAdmin):
    list_display = ("user", "color_code", "unlocked_at")
    search_fields = ("user__username", "user__email", "color_code")
    list_per_page = 100


@admin.register(UserUnlockedEyesColor)
class UserUnlockedEyesColorAdmin(admin.ModelAdmin):
    list_display = ("user", "color_code", "unlocked_at")
    search_fields = ("user__username", "user__email", "color_code")
    list_per_page = 100


@admin.register(Avatar)
class AvatarAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "avatar_type",
        "face_item",
        "hair_item",
        "hair_color",
        "shirt_item",
        "shirt_color",
        "pants_item",
        "pants_color",
        "shoes_item",
        "shoes_color",
        "skin_color",
        "eyes_color",
        "accessory_item",
        "accessory_color",
    )
    list_filter = ("avatar_type",)
    search_fields = ("user__username", "user__email")
    list_select_related = True
    list_per_page = 50
