import requests
from django import http
from django.conf import settings
from django.contrib.auth import login
from rest_framework.authtoken.models import Token

from accounts import models
from accounts.auth.base import AuthView
from django.shortcuts import redirect

class DiscordAuthView(AuthView):
    """
    Responsible for handling Oauth logic for Discord Accounts.
    This flow is special in a few ways regarding ZCL accounts

    - All Discord Users must have their accounts verified by discord to prevent
        any hijacking and to make sure that it is a real(er) person.

    - All ZCL Users are required to have discord. Therefore a user account is
        created if one does not exist with their discord id as their primary key.

    - Upon account creation, an API key is assigned for our standalone client.

    - We update our SocialAccount table with their access_token and refresh_token
        so we may make future API calls (if needed). Currently we get user details.

    - If the account already exists, that user is logged into the user's session
        on their web browser.

    """
    def generate_auth_url(self):
        url = "{auth}?response_type=code&client_id={cid}&scope=identify+email&redirect_uri={ri}".format(
            auth=self.settings.authorization_url,
            cid=self.settings.client_id,
            ri=self.callback_url,
        )
        return url

    def on_exchange_success(self, request: http.HttpRequest, response: requests.Response):
        extra_data = response.json()
        print(extra_data)
        token = extra_data.get('access_token')
        data = discord_api('/users/@me', token).json()
        if data.get('email') is not None and data.get('verified'):
            user, created = models.DiscordUser.objects.update_or_create(
                id=int(data['id']),
                defaults={
                    'avatar': data.get('avatar', ""),
                    'discriminator': int(data['discriminator']),
                    'email':  data['email'],
                    'username': data['username']
                }
            )
            if created:
                # Create a new auth token for the client
                Token.objects.create(user=user)

            # Link a new Social Account
            models.SocialAccount.objects.update_or_create(
                user=user,
                provider='discord',
                defaults={
                    'extra_data': extra_data,
                }
            )
            # Log in the user
            login(request, user)
        else:
            # TODO: Email Unverified/Missing Redirect.
            msg = "Your email address for your discount account must be verified."
            return redirect(f'/error?code=401&msg={msg}')
        return redirect('/account')

def discord_api(endpoint, token) -> requests.Response:
    """
    Makes a api request to discord
    Parameters
    ----------
    endpoint
    token

    Returns
    -------

    """
    base = "https://discordapp.com/api/v6"
    target = f"{base}{endpoint}"
    headers = {
        'Authorization': f'Bearer {token}'
    }
    resp = requests.get(target, headers=headers)
    return resp

