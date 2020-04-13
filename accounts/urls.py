from django.conf import settings
from django.urls import path

from accounts.auth.base import AuthSettings
from accounts.auth.discord import DiscordAuthView
from accounts.auth.twitch import TwitchAuthView
from . import views

urlpatterns = [
    path('exchange/', views.DiscordToLocalToken.as_view(), name='exchange'),
    path('logout', views.logout, name='logout'),
    path('login',
        DiscordAuthView.as_view(AuthSettings(settings.OAUTH2_DISCORD), 'discord-auth'),
        name='discord-auth',
    ),
    path('twitch/connect',
         TwitchAuthView.as_view(AuthSettings(settings.OAUTH2_TWITCH), 'twitch-connect'),
         name='twitch-connect',
    ),


]
