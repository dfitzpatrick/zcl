
from rest_framework import serializers
from .. import models

class StandingsSerializer(serializers.ModelSerializer):
    total_wins = serializers.IntegerField()
    total_losses = serializers.IntegerField()
    total_matches = serializers.IntegerField()
    total_draws = serializers.IntegerField()
    rate = serializers.FloatField()
    win_rate = serializers.FloatField()
    adjusted_win_rate = serializers.FloatField()
    rank = serializers.IntegerField()

    class Meta:
        model = models.SC2Profile
        fields = ('id', 'name', 'total_matches', 'total_wins', 'total_losses', 'total_draws', 'rate', 'win_rate', 'adjusted_win_rate', 'rank', 'avatar_url')
