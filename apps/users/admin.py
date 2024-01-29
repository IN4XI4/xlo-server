from django.contrib import admin

# Register your models here.
from .models import CustomUser, Gender, Experience, ProfileColor


admin.site.register(CustomUser)
admin.site.register(Gender)
admin.site.register(Experience)


@admin.register(ProfileColor)
class ProfileColorAdmin(admin.ModelAdmin):
    list_display = ("id", "color")
    list_filter = ("color",)
    search_fields = ("color",)
    list_per_page = 100
