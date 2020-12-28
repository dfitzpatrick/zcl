from rest_framework import serializers
from ..serializers import SC2ProfileSerializer
from .. import models

class LeaderboardSerializer(serializers.ModelSerializer):
    profile = SC2ProfileSerializer()
    losses = serializers.IntegerField()
    rank = serializers.IntegerField()
    name = serializers.CharField()
    win_rate = serializers.DecimalField(max_digits=7, decimal_places=0)

    class Meta:
        model = models.Leaderboard
        fields = ('id', 'mode', 'name', 'rank', 'created', 'updated', 'profile', 'games', 'wins', 'losses', 'elo', 'win_rate', 'mode')