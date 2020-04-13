from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from . import models
from .models import DiscordUser

class CustomUserAdmin(UserAdmin):
    model = DiscordUser
    list_display = ['username', 'created']


admin.site.register(models.DiscordUser, CustomUserAdmin)
admin.site.register(models.SocialAccount)
