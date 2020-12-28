from rest_framework import serializers
from accounts.models import DiscordUser


class DiscordUserSerializer(serializers.ModelSerializer):

    # Javascript overflows
    id = serializers.SerializerMethodField()

    def get_id(self, instance):
        return str(instance.id)
    class Meta:
        model = DiscordUser
        fields = ('id', 'created', 'username', 'discriminator', 'avatar', 'client_heartbeat')
