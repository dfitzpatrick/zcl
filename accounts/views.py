import requests
from django.conf import settings
from django.contrib import auth
from django.http import HttpResponseRedirect
from rest_framework import permissions
from rest_framework import status
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from api import serializers
from api.permissions import IsOwner
from .models import DiscordUser
from .models import SocialAccount
from .serializers import SocialAccountSerializer
from django.shortcuts import redirect
import logging

log = logging.getLogger('zcl.accounts.views')

class DiscordToLocalToken(APIView):
    """
    This API View allows a rest client to authenticate and retrieve a local
    ZCL token from Discord OAUTH access_codes.
    """

    def post(self, request):
        """
        Retrieves a local user account API Token.
        Parameters
        ----------
        request: The request that contains a "token" body with the user's
            discord token.

        Returns
        -------

        """
        token = request.data.get('token')
        headers = {
            "Authorization": "Bearer {0}".format(token)
        }
        url = 'https://discordapp.com/api/v6/users/@me'
        resp = requests.get(url, headers=headers).json()
        error_message = resp.get('message')
        print(resp)
        if error_message is not None:
            return Response({'error': error_message}, status=401)

        if resp.get('email') and resp.get('verified'):
            # Lookup the user
            id = resp.get('id')
            payload = {
                'user': None,
                'token': None,
            }
            try:
                user = DiscordUser.objects.get(id=id)
                token = Token.objects.get(user=user)
                payload['user'] = serializers.DiscordUserSerializer(user).data
                payload['token'] = token.key
                return Response(payload, status=202)
            except DiscordUser.DoesNotExist:
                return Response({'error': 'no user'},status=404)

            except Token.DoesNotExist:
                # We won't issue new tokens here just in case we wanted to revoke
                # access to the user from posting to the api. Tokens are created
                # on new accounts only.
                return Response(
                    {'error': 'User has no access token to exchange. Contact admin.'},
                    status=401
                )

        return Response({'error': 'unverified discord account'}, status=401)

class me(APIView):
    permission_classes = (IsOwner,)

    def get(self, request):
        user: DiscordUser = request.user
        print(user.id)
        data = serializers.DiscordUserSerializer(user).data
        print(data)
        return Response(data, status=status.HTTP_200_OK)


def logout(request):
    """
    Simple view to clear the session of any login.
    Parameters
    ----------
    request

    Returns
    -------
    HttpResponseRedirect
    """
    auth.logout(request)
    return redirect(settings.SITE_URL)

class Connections(viewsets.ModelViewSet):
    permission_classes = (IsOwner,)
    serializer_class = SocialAccountSerializer

    def get_queryset(self):
        return SocialAccount.objects.filter(user=self.request.user).exclude(provider='discord')

class Connections2(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated, )

    def list(self, request):
        qs = SocialAccount.objects.filter(user=request.user).exclude(provider='discord')
        serialized = SocialAccountSerializer(qs, many=True).data
        return Response(serialized)

    def retrieve(self, request, pk):
        instance = SocialAccount.objects.get(id=pk)
        return Response(SocialAccountSerializer(instance).data)


    def delete(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        print(args)
        try:
            instance = SocialAccount.objects.get(id=pk)
            data = SocialAccountSerializer(instance).data
            instance.delete()
            return Response(data, status=status.HTTP_200_OK)
        except SocialAccount.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)



