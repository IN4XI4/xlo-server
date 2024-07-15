from django.contrib import admin

from .models import (
    Story,
    Card,
    BlockType,
    Block,
    Comment,
    Like,
    UserStoryView,
    UserCardView,
    RecallCard,
    RecallBlock,
    RecallComment,
    Notification,
)


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "topic", "is_active", "created_time")
    search_fields = ("title",)
    list_filter = ("user__username", "topic")
    list_per_page = 100


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("title", "story", "soft_skill", "mentor", "created_time")
    list_filter = ("story", "soft_skill", "mentor")
    search_fields = ("title",)
    list_per_page = 50


@admin.register(BlockType)
class BlockTypeAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_per_page = 100


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ("card", "block_type")
    list_filter = ("card", "block_type")
    list_per_page = 100


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "comment_text", "story", "user", "is_active", "created_time", "updated_time")
    list_filter = ("user__username", "story", "is_active")
    search_fields = ("comment_text", "user__username")
    list_per_page = 100


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("id", "liked", "user", "is_active", "content_type", "content", "created_time", "updated_time")
    list_filter = ("user__username", "liked", "is_active")
    search_fields = ("user__username",)
    list_per_page = 100


@admin.register(UserStoryView)
class UserStoryViewAdmin(admin.ModelAdmin):
    list_display = ("user", "story")
    list_filter = ("user__username", "story")
    search_fields = ("user", "story")
    list_per_page = 100


@admin.register(UserCardView)
class UserCardViewAdmin(admin.ModelAdmin):
    list_display = ("user", "card")
    list_filter = ("user__username", "card")
    search_fields = ("user", "card")
    list_per_page = 100


@admin.register(RecallCard)
class RecallCardAdmin(admin.ModelAdmin):
    list_display = ("user", "card")
    list_filter = ("user__username", "card", "importance_level")
    search_fields = ("user", "card")
    list_per_page = 100


@admin.register(RecallBlock)
class RecallBlockAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "block")
    list_filter = ("user__username", "block", "importance_level")
    search_fields = ("user", "block")
    list_per_page = 100


@admin.register(RecallComment)
class RecallCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "comment")
    list_filter = ("user__username", "comment", "importance_level")
    search_fields = ("user", "comment")
    list_per_page = 100


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "notification_type")
    list_filter = ("user__username", "date", "notification_type")
    search_fields = ("user",)
    list_per_page = 100
