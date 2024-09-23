from django.contrib import admin

from .models import Space, MembershipRequest


@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "access_type", "created_time")
    search_fields = ("name",)
    list_per_page = 100


@admin.register(MembershipRequest)
class MembershipRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "space", "user", "status", "created_time")
    list_filter = ("space", "status")
    search_fields = ("space",)
    list_per_page = 100
