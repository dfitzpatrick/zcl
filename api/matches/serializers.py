from rest_framework import serializers
from api import models
from ..teams.serializers import TeamSerializer
from ..serializers import RosterSerializer
from ..profiles.serializers import ProfileSerializer

class MatchSerializer(serializers.ModelSerializer):
    #players = serializers.CharField()
    #winners = serializers.CharField()
    #profile_ids = serializers.CharField()
    #winner_ids = serializers.CharField()
    nukes = serializers.IntegerField()
    tanks = serializers.IntegerField()
    turrets = serializers.IntegerField()
    bunkers = serializers.IntegerField()
    scv = serializers.IntegerField()
    sensors = serializers.IntegerField()
    shields = serializers.IntegerField()
    supply_depots = serializers.IntegerField()
    names = serializers.CharField(max_length=300)
    alt_winners = serializers.CharField(max_length=200)
    mid = serializers.BooleanField()
    #elo_average = serializers.IntegerField()

    class Meta:
        model = models.Match
        fields = (
            "id", "created", "updated", "match_date",
            "game_length", 'league', 'season', "nukes", "tanks", "turrets",
             'bunkers', 'scv', 'sensors', 'shields', 'supply_depots',
            'names', 'alt_winners', 'mid',
        )

class MatchTeamRosterSerializer(serializers.ModelSerializer):
    team = TeamSerializer()
    class Meta:
        model = models.MatchTeam
        fields = '__all__'

class RosterSerializer(serializers.ModelSerializer):
    sc2_profile = ProfileSerializer()
    class Meta:
        model = models.Roster
        fields = '__all__'

class MatchTeams(serializers.ModelSerializer):
    rosters = RosterSerializer(many=True)
    teams = MatchTeamRosterSerializer(source='matchteam_set', many=True)
    class Meta:
            model = models.Match
            fields = '__all__'