import typing

import requests
from django import http, urls
from django.conf import settings
from django.views import View

from ..models import SocialAccount


class AuthSettings(dict):
    """
    Exists to help with type hinting and to just reinforce required parameters
    from a dictionary that contains the settings. This stores all the config
    needed for OAUTH2 in our AuthView.
    """
    def __init__(self, *args, **kwargs):
        super(AuthSettings, self).__init__(*args, **kwargs)

        # Force error if not defined properly
        self.client_id = self['client_id']
        self.secret = self['secret']
        self.authorization_url = self['authorization_url']
        self.token_url = self['token_url']
        self.redirect_uri = self.get('redirect_uri')
        self.scope = self['scope']

class APICaller:

    def __init__(self, social_account: SocialAccount, auth_settings: AuthSettings):
        if isinstance(auth_settings, dict):
            auth_settings = AuthSettings(auth_settings)
        self.social_account = social_account
        self.settings = auth_settings
        self.api_url = auth_settings.get('api_url')

    @property
    def headers(self):
        # How to prevent this call from always happening?
        # if self._bearer is None:
        #    self._bearer = self._get_app_token()
        token_type = self.social_account.extra_data.get('token_type') or 'Bearer'
        token_type = token_type.capitalize()
        access_token = self.social_account.extra_data.get('access_token')
        headers = {
            'Authorization': f'{token_type} {access_token}'
        }
        print(headers)
        return headers

    def get(self, endpoint: str, refresh: bool = True):
        target = f"{self.api_url}{endpoint}"
        response = requests.get(target, headers=self.headers)
        if response.status_code == 401:
            if not refresh:
                response.raise_for_status()
            self.refresh()
            return self.get(endpoint, refresh=False)
        elif response.status_code != 200:
            response.raise_for_status()
        return response.json()


    def refresh(self):
        refresh_token = self.social_account.extra_data.get('refresh_token')
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        payload = {
            'client_id': self.settings.client_id,
            'client_secret': self.settings.secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'redirect_uri': self.settings.redirect_uri,
            'scope': self.settings.scope.replace('+', ' '),
        }
        response = requests.post(self.settings.token_url, data=payload, headers=headers)
        if response.status_code != 200:
            print("refresh error")
            print(payload)
            response.raise_for_status()
        response = response.json()
        print("refresh response")
        print(response)
        self.social_account.extra_data = response
        self.social_account.save()
        return response.get('access_code')

class AuthView(View):
    """
    Responsible for the OAUTH Authorization Code Flow and callbacks.
    """

    @classmethod
    def as_view(cls, auth_settings:  AuthSettings, callback_url_name: str, **initkwargs):
        cls.settings = auth_settings
        cls.callback_url_name = callback_url_name
        result = super(AuthView, cls).as_view(**initkwargs)
        return result

    def get(self, request: http.HttpRequest):
        """
        Initiate the request
        Parameters
        ----------
        request

        Returns
        -------

        """
        code = request.GET.get('code')
        if code is not None:
            response = self.exchange(request)
            return response
        url = self.generate_auth_url()
        return http.HttpResponseRedirect(url)

    def generate_auth_url(self):
        pass

    @property
    def callback_url(self):
        return "{0}{1}".format(
            settings.SITE_URL,
            urls.reverse(self.callback_url_name)
        )

    def get_exchange_payload(self, request):
        code = request.GET['code']
        payload = {
            'client_id': self.settings.client_id,
            'client_secret': self.settings.secret,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.callback_url,
        }
        return payload

    def exchange(self, request: http.HttpRequest) -> requests.Response:

        payload = self.get_exchange_payload(request)
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        r = requests.post(self.settings.token_url, data=payload, headers=headers)
        if r.status_code == 200:
            response = self.on_exchange_success(request, r)
        else:
            response = self.on_exchange_fail(request, r)

        return response

    def on_exchange_success(self, request: http.HttpRequest, response: requests.Response) -> typing.Union[requests.Response, http.HttpResponse]:
        pass

    def on_exchange_fail(self, request: http.HttpRequest, response: requests.Response) -> typing.Union[requests.Response, http.HttpResponse]:
        pass