import logging

import requests
from django import http
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin

import services.twitch
from accounts import models
from accounts.auth.base import AuthView
from api.models import TwitchStream

log = logging.getLogger('zcl.accounts.auth.twitch')

class TwitchAuthView(LoginRequiredMixin, AuthView):

    def generate_auth_url(self):
        url = "{auth}?response_type=code&client_id={cid}&scope=clips:edit+user:edit&redirect_uri={ri}&force_verify=true".format(
            auth=self.settings.authorization_url,
            cid=self.settings.client_id,
            ri=self.callback_url,
        )
        return url

    def on_exchange_success(self, request: http.HttpRequest, response: requests.Response) -> http.HttpResponse:
        extra_data = response.json()
        log.debug(extra_data)

        # We create a base account later to make a api call to verify if its a duplicate
        sa = models.SocialAccount.objects.create(
            user=request.user,
            provider='twitch',
            extra_data=extra_data
        )

        helix = services.twitch.Helix(sa)
        user = helix.get_user().get('data')[0]
        username = user['login']
        if models.SocialAccount.objects.filter(provider='twitch', user=request.user, username=username).count() > 0:
            # Duplicate Account.
            sa.delete()
            return http.HttpResponseRedirect(settings.FRONTEND + 'portal/connections')
        else:
            sa.username = username
            sa.save()

        sub = helix.subscribe_to_stream(user['id'])
        TwitchStream.objects.get_or_create(
            uuid=sub.uuid,
            defaults={
                'social_account': sa,
                'username': username,

            }
        )
        return http.HttpResponseRedirect(settings.FRONTEND + 'portal/connections')

    def on_exchange_fail(self, request: http.HttpRequest, response: requests.Response) -> http.HttpResponse:
        print("Fail")
        response.raise_for_status()
