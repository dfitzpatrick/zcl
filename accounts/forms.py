from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import DiscordUser


class CustomUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm):
        model = DiscordUser
        fields = ('username', 'email')


class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = DiscordUser
        fields = ('username', 'email')