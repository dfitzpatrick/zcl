from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from accounts.models import DiscordUser
from api import models


class AnonymousUserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    def get_avatar_url(self):
        return "foo"

    class Meta:
        model = AnonymousUser
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    class Meta:
        model = get_user_model()
        exclude = ('password',)


    def get_avatar_url(self, obj):
        if hasattr(obj, 'avatar'):
            return "https://cdn.discordapp.com/avatars/{0}/{1}.png".format(
                obj.id, obj.avatar
            )
        return None

class TwitchStreamSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = models.TwitchStream
        exclude = ('social_account',)

class UserSerializerWithToken(serializers.ModelSerializer):

    token = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True)

    def get_token(self, obj):
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(obj)
        token = jwt_encode_handler(payload)
        return token

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

    class Meta:
        model = get_user_model()
        fields = ('token', 'username', 'password')


class DiscordUserSerializer(serializers.ModelSerializer):

    # Javascript overflows
    id = serializers.SerializerMethodField()

    def get_id(self, instance):
        return str(instance.id)
    class Meta:
        model = DiscordUser
        fields = ('id', 'created', 'username', 'discriminator', 'avatar', 'client_heartbeat')



class GuildSerializer(serializers.ModelSerializer):
    leagues = serializers.SerializerMethodField()

    def get_leagues(self, guild: models.Guild):
        serializer = LeagueSerializer(guild.leagues.all(), many=True)
        return serializer.data

    class Meta:
        model = models.Guild
        fields = ('id', 'name', 'leagues')


class LeagueSerializer(serializers.ModelSerializer):
    seasons = serializers.SerializerMethodField()

    def get_seasons(self, league: models.League):
        serializer = SeasonSerializer(league.seasons.all(), many=True)
        return serializer.data

    class Meta:
        model = models.League
        fields = ('id', 'name', 'guild', 'description', 'seasons')


class SeasonSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Season
        fields = ('id', 'name', 'description')



class SC2ProfileSerializer(serializers.ModelSerializer):
    #discord_users = DiscordUserSerializer(many=True)
    class Meta:
        model = models.SC2Profile
        fields = ('id', 'created', 'name', 'profile_url', 'avatar_url', 'discord_users')

class ProfileWithUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SC2Profile
        fields = ('id', 'created', 'name', 'profile_url', 'avatar_url', 'discord_users')

class LeaderboardSerializer(serializers.ModelSerializer):
    profile = SC2ProfileSerializer()
    losses = serializers.IntegerField()
    rank = serializers.IntegerField()
    name = serializers.CharField()
    win_rate = serializers.DecimalField(max_digits=7, decimal_places=0)

    class Meta:
        model = models.Leaderboard
        fields = ('id', 'mode', 'name', 'rank', 'created', 'updated', 'profile', 'games', 'wins', 'losses', 'elo', 'win_rate', 'mode')



class RosterSerializer(serializers.ModelSerializer):
    sc2_profile = SC2ProfileSerializer()
    lane = SC2ProfileSerializer()
    class Meta:
        model = models.Roster
        fields = '__all__'



class OLDMatchSerializer(serializers.ModelSerializer):
    #league = LeagueSerializer()
    #season = SeasonSerializer()
    #rosters = RosterSerializer(many=True)
    players = serializers.CharField()
    winners = serializers.CharField()
    profile_ids = serializers.CharField()


    class Meta:
        model = models.Match
        fields = ('id', 'created', 'updated', 'match_date', 'game_id', 'league', 'season', 'players', 'winners', 'profile_ids', )


class ReplaySerializer(serializers.ModelSerializer):
    game_id = serializers.CharField(max_length=100, required=False)
    class Meta:
        model = models.Replay
        fields = "__all__"


class MatchEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MatchEvent
        exclude = ('match', 'raw',)

class UnitStatSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.UnitStat
        fields = '__all__'

class GameEventSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.GameEvent
        fields = '__all__'

class ChartPointSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    game_time = serializers.CharField()
    class Meta:
        model = models.ChartPoints
        fields = '__all__'

class TeamSerializer(serializers.ModelSerializer):
    profiles = SC2ProfileSerializer(many=True)
    team_elo = serializers.DecimalField(max_digits=10, decimal_places=0)
    players = serializers.CharField()
    games = serializers.IntegerField()
    wins = serializers.IntegerField()
    losses = serializers.IntegerField()
    draws = serializers.IntegerField()
    win_rate = serializers.DecimalField(max_digits=10, decimal_places=1)
    class Meta:
        model = models.Team
        fields = '__all__'



class MatchTeamSerializer(serializers.ModelSerializer):
    rosters = RosterSerializer(many=True)

    class Meta:
        model = models.MatchTeam
        fields = '__all__'


class MatchStreamersSerializer(serializers.Serializer):
    profile = SC2ProfileSerializer()
    stream = TwitchStreamSerializer()


class MatchFullSerializer(serializers.ModelSerializer):
    rosters = RosterSerializer(many=True)
    observers = SC2ProfileSerializer(many=True)

    class Meta:
        model = models.Match
        fields = '__all__'

class MatchSerializer(serializers.ModelSerializer):


    class Meta:
        model = models.Match
        fields = '__all__'

class GameEventSerializer(serializers.ModelSerializer):
    profile = SC2ProfileSerializer()
    opposing_profile = SC2ProfileSerializer()

    class Meta:
        model = models.GameEvent
        fields = '__all__'