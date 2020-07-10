import os
import typing
from accounts.models import AppToken
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta, timezone
import logging

log = logging.getLogger('zcl.services.blizzard')
class BlizzardAPI:

    def __init__(self,
                 *,
                 client_id=os.environ.get('BLIZZARD_CLIENT_ID'),
                 secret=os.environ.get('BLIZZARD_CLIENT_SECRET'),
                 ):
        self.client_id = client_id
        self.secret = secret
        self._extra_data = {}
        self.api_base = 'https://{region}.api.blizzard.com'
        self.REGION_REALM = {
            11: 'us',
            12: 'us',
            21: 'eu',
            22: 'eu',
            31: 'kr',
            32: 'tw'
        }

    def base_url(self, region_id, realm_id):
        key = int(f'{region_id}{realm_id}')
        region = self.REGION_REALM.get(key, 'us')
        self.api_base = f'https://{region}.api.blizzard.com'
        return self.api_base

    def _token_request(self) -> typing.Optional[dict]:
        target = 'https://us.battle.net/oauth/token'
        auth = HTTPBasicAuth(self.client_id, self.secret)
        payload = {'grant_type': 'client_credentials'}
        response = requests.post(target, auth=auth, data=payload)

        if response.status_code == 200:
            data = response.json()
            obj, created = AppToken.objects.update_or_create(
                provider='blizzard',
                defaults={
                    'extra_data': data
                }
            )
            return obj.data
        log.error(f' {target} returns {response.status_code}: {response.text}')
        return {}

    @property
    def auth_header(self):
        extra_data = self.extra_data
        bearer = extra_data.get('token_type', 'Bearer').capitalize()
        token = extra_data['access_token']
        return {'Authorization': f'{bearer} {token}'}

    @property
    def extra_data(self):
        try:
            now = datetime.now(timezone.utc)
            if not self._extra_data:
                self._extra_data = AppToken.objects.get(provider='blizzard').data
            # 7/10 attempt to resolve access_token authentication issues with name resolution.
            if self._extra_data.get('access_token') is None:
                self._extra_data = self._token_request()
            if self._extra_data.get('expires_at', now) - now < timedelta(seconds=120):
                self._extra_data = self._token_request()
            return self._extra_data

        except AppToken.DoesNotExist:
            self._extra_data = self._token_request()
            return self._extra_data

    def get_profile(self, profile_string) -> typing.Optional[typing.Dict[str, typing.Any]]:
        # 6/29 reorder due to handle strings being slightly different from bnet url order.
        realm, game, region, profile = profile_string.split('-')
        return self._get_profile(region, realm, profile)

    def _get_profile(self, region_id, realm_id, profile_id) -> typing.Optional[typing.Dict[str, typing.Any]]:
        base = self.base_url(region_id, realm_id)
        target = f'{base}/sc2/profile/{region_id}/{realm_id}/{profile_id}'

        auth = self.auth_header

        response = requests.get(url=target, headers=auth)

        if response.status_code == 200:
            return response.json()
        else:
            log.warning(f"{target} returns {response.status_code} {response.text} {auth}")
            return
