from rest_framework import serializers
from ..serializers import SC2ProfileSerializer
from .. import models





class TeamSerializer(serializers.ModelSerializer):


    class Meta:
        model = models.Team
        fields = '__all__'

class TeamSerializerWithAnnotations(TeamSerializer):
    profiles = SC2ProfileSerializer(many=True)
    team_elo = serializers.DecimalField(max_digits=10, decimal_places=0)
    players = serializers.CharField()
    games = serializers.IntegerField()
    wins = serializers.IntegerField()
    losses = serializers.IntegerField()
    draws = serializers.IntegerField()
    win_rate = serializers.DecimalField(max_digits=10, decimal_places=1)
    profile_ids = serializers.CharField()