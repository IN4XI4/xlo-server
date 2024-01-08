from django.contrib import admin

# Register your models here.
from .models import CustomUser, Gender, Experience, ProfileColor


admin.site.register(CustomUser)
admin.site.register(Gender)
admin.site.register(Experience)
admin.site.register(ProfileColor)