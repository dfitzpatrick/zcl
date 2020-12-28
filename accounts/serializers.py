from rest_framework import serializers

from .models import SocialAccount


class SocialAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialAccount
        exclude=('extra_data',)