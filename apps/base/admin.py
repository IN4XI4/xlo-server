from django.contrib import admin

from .models import TopicTag, Topic, SoftSkill, Mentor


@admin.register(TopicTag)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_per_page = 100


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_per_page = 100


@admin.register(SoftSkill)
class SoftSkillAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_per_page = 100


@admin.register(Mentor)
class MentorAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_per_page = 100
