from api import permissions as custom_permissions
from rest_framework import permissions, viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from accounts.models import DiscordUser
from . import serializers
from ..profiles.serializers import ProfileSerializer
from accounts.models import SocialAccount
from accounts.serializers import SocialAccountSerializer

class UserView(viewsets.ModelViewSet):
    serializer_class = serializers.DiscordUserSerializer
    queryset = DiscordUser.objects.all()
    class Meta:
        model = DiscordUser

    @action(methods=['get'], detail=True, permission_classes=[custom_permissions.IsOwner,])
    def profiles(self, request, pk, *args, **kwargs):
        user: DiscordUser = self.get_object()
        profiles = user.profiles.all()
        return Response(ProfileSerializer(profiles, many=True).data, status.HTTP_200_OK)

    @action(methods=['GET', 'POST', 'DELETE'], detail=True)
    def connections(self, request, pk, *args, **kwargs):
        if request.method == "GET":
            accounts = SocialAccountSerializer(
                SocialAccount
                    .objects
                    .filter(user__id=pk)

                , many=True).data
            return Response(accounts, status=status.HTTP_200_OK)

        print(request.method)