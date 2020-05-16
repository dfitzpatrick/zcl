import logging
import os
import typing

import requests
from rest_framework import status

from accounts.models import SocialAccount
from websub.models import Subscription
from django.conf import settings

log = logging.getLogger('zcl.services.twitch')

class Helix:

    def __init__(self,
                 social_account: SocialAccount,
                 *,

                 client_id=settings.TWITCH_CLIENT_ID,
                 secret=settings.TWITCH_CLIENT_SECRET,
                 bearer=None,
                 ):
        self.site = settings.SITE_URL
        self.client_id = client_id
        self.secret = secret
        self.root = 'https://api.twitch.tv/helix'
        self._bearer = social_account.extra_data.get('access_token')
        self.social_account = social_account

    def _get_app_token(self) -> typing.Optional[str]:
        url = 'https://id.twitch.tv/oauth2/token'
        payload = {
            'client_id': self.client_id,
            'client_secret': self.secret,
            'grant_type': 'client_credentials'
        }
        resp = requests.post(url, data=payload)
        return resp.get('access_token')


    def request(self, method, endpoint, headers=None, retry=True):
        headers = headers if headers is not None else self.headers
        uri = self.root + endpoint
        id = self.social_account.id
        resp = requests.request(method, uri, headers=headers)
        resp_status = resp.status_code
        desc = resp.text
        if resp.status_code == status.HTTP_401_UNAUTHORIZED:
            if retry:
                self.refresh_token()
                return self.request(method, endpoint, headers=headers, retry=False)
            else:
                log.error(f"Request {method} {endpoint} failed for SocialAccount {id}. {resp_status} {desc} header={headers}")
                return {'data': []}
        return resp

    def refresh_token(self):
        url = 'https://id.twitch.tv/oauth2/token'
        id = self.social_account.id
        payload = {
            'client_id': self.client_id,
            'client_secret': self.secret,
            'grant_type': 'refresh_token',
            'refresh_token': self.social_account.data['refresh_token']
        }
        response = requests.post(url, data=payload)
        status = response.status_code
        desc = response.text
        if status == 200:
            self.social_account.extra_data = response.json()
            self.social_account.save()
        else:
            log.error(f"Twitch Token Refresh on {id} Fails. Status {status} {desc}")

    @property
    def headers(self):
        # How to prevent this call from always happening?
        #if self._bearer is None:
        #    self._bearer = self._get_app_token()
        token_type = self.social_account.extra_data.get('token_type') or 'Bearer'
        token_type = token_type.capitalize()
        access_token = self.social_account.extra_data.get('access_token')
        return {
            'Client-ID': self.client_id,
            'Content-type': 'application/json',
            'Authorization': f'{token_type} {access_token}'
        }

    def get_user(self, username: typing.Optional[str] = None) -> typing.Optional[int]:
        """
        Gets a user id from the supplied username
        Parameters
        ----------
        username

        Returns
        -------

        """
        target = '/users'
        headers = self.headers
        if isinstance(username, str):
            target = '/users?login={0}'.format(username)

        resp = self.request('GET', target, headers=headers)
        print(resp)
        return resp.json()

    def webhook_subscriptions(self):
        resp:requests.Response = self.request('GET', '/webhooks/subscriptions')
        return resp.json()

    def refresh_stream_subscription(self, sub: Subscription):
        """
        Attempts to send 'subscribe' back to twitch stream with the user
        OAUTH tokens
        Parameters
        ----------
        sub

        Returns
        -------

        """
        self.refresh_token()
        headers = self.headers
        sub.refresh(headers=headers)

    def unsubcribe_from_stream(self, sub: Subscription):
        self.refresh_token()
        headers = self.headers
        sub.unsubscribe(headers=headers)

    def subscribe_to_stream(self, id):
        topic = f'{self.root}/streams?user_id={id}'
        hub = 'https://api.twitch.tv/helix/webhooks/hub'
        if self.social_account.token_expiring:
            self.refresh_token()
        headers = self.headers

        sub = Subscription.subscribe(
            hub=hub,
            topic=topic,
            callback_name='streams',
            headers=headers
        )
        return sub







