from django import forms
from django.db import models
from django.contrib import admin
from ckeditor.widgets import CKEditorWidget

from .models import TopicTag, Topic, SoftSkill, Mentor, EmailSending


@admin.register(TopicTag)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_per_page = 100


class TopicAdminForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ["title", "description", "image", "tag", "slug"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4, "cols": 80})}


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    form = TopicAdminForm
    search_fields = ("name",)
    list_per_page = 100


@admin.register(SoftSkill)
class SoftSkillAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_per_page = 100


@admin.register(Mentor)
class MentorAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "user", "created_by")
    search_fields = ("name",)
    list_per_page = 100


@admin.register(EmailSending)
class EmailSendingAdmin(admin.ModelAdmin):
    list_display = ("subject", "created_time")
    list_per_page = 100
    formfield_overrides = {models.TextField: {"widget": CKEditorWidget()}}
