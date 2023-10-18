from django.contrib import admin

from .models import Topic, Monster, GalleryImage, Post, BlockType, Block, Comment, Like


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_per_page = 100


@admin.register(Monster)
class MonsterAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_per_page = 100


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "topic", "monster", "user", "is_active", "created_time",)
    list_filter = ("user__username", "is_active")
    search_fields = ("title", "user__username")
    list_per_page = 50


@admin.register(BlockType)
class BlockTypeAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_per_page = 100


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ("post", "block_type", "post_user")
    list_filter = ("post", "block_type")
    search_fields = ("name",)
    list_per_page = 100

    def post_user(self, obj):
        return obj.post.user
    post_user.short_description = 'Post User'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("comment_text", "post", "user", "is_active", "created_time", "updated_time")
    list_filter = ("user__username", "is_active")
    search_fields = ("comment_text", "user__username")
    list_per_page = 100


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("liked", "user", "is_active", "content_type", "content", "created_time", "updated_time")
    list_filter = ("user__username", "liked", "is_active")
    search_fields = ("user__username",)
    list_per_page = 100


admin.site.register(GalleryImage)
