import collections

import collections
import logging
from decimal import Decimal

import requests
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.postgres.aggregates import StringAgg
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models import Avg, Count, When, Case
from django.db.models import FloatField, DecimalField
from django.db.models import Q, F
from django.db.models.functions import Cast
from django.http import HttpResponse
from rest_framework import parsers
from rest_framework import permissions
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.views import APIView
from zclreplay import Replay, NotZCReplay, IncompleteReplay

import services.match
from accounts.models import DiscordUser as DiscordUserModel
from accounts.models import SocialAccount
from accounts.serializers import SocialAccountSerializer
from api import annotations, filters
from api.tasks import parse_replay
from . import serializers, models
from . import utils
import json


# Create your views here.

log = logging.getLogger('zcl.api.views')

@api_view(['POST'])
def exchange_discord_token(request):
    """
    The client authorizes via their front-end app with a the Discord oauth
    provider. They then send a request to the api where this will validate,
    and create the user if needed and supply our own JWT.

    Parameters
    ----------
    request

    Returns
    -------

    """

    token = request.POST.get('token')
    if token is None:
        # TODO: Error handling here
        return
    header = {'Authorization': f'Bearer {token}'}


    # Check for token validity
    response = requests.get(settings.DISCORD_API_BASE_URL + '/users/@me', headers=header).json()
    if response.get('email'):
        defaults = {
            'id': response['id'],
            'discriminator': response['discriminator'],
            'avatar': response['avatar'],
            'username': response['username']
        }
        user, created = DiscordUserModel.objects.update_or_create(
            email=response['email'],
            defaults=defaults
        )
        serialized_user = serializers.UserSerializer(user)
        return Response(
            {
                'token': user.token,
                'user': serialized_user.data,
            }
        )
    return Response("Error")


class DiscordUserView(viewsets.ModelViewSet):
    serializer_class = serializers.DiscordUserSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = models.DiscordUser.objects.all()

    @action(methods=['GET', 'POST'], detail=True)
    def toons(self, request, *args, **kwargs):
        if request.method == "POST":
            id = request.data.get('id')
            print(f"id is {id}")
            if isinstance(id, str):
                profile = utils.get_or_create_profile(id)
                print(profile)
                profile.discord_users.add(request.user)
                profile.save()
                return Response(status=status.HTTP_200_OK)
            return Response(status=status.HTTP_400_BAD_REQUEST)

        user: DiscordUserModel = self.get_object()
        toons = user.profiles.all()

        serializer = serializers.SC2ProfileSerializer(toons, many=True)

        return Response(serializer.data)

    @action(methods=['GET', 'POST', 'DELETE'], detail=True)
    def connections(self, request, pk, *args, **kwargs):
        if request.method == "GET":
            accounts = SocialAccountSerializer(
                SocialAccount
                .objects
                .filter(user__id=pk)
                .exclude(provider='discord')
                , many=True).data
            return Response(accounts, status=status.HTTP_200_OK)
        print(request.method)




class SC2ProfileUserView(viewsets.ModelViewSet):
    serializer_class = serializers.SC2ProfileSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = annotations.leaderboards.qs_with_ranking()

    @action(methods=['GET'], detail=True)
    def users(self, request, *args, **kwargs):
        profile: models.SC2Profile = self.get_object()
        users = profile.discord_users.all()

        serializer = serializers.DiscordUserSerializer(users, many=True)
        return Response(serializer.data)


class GuildView(viewsets.ModelViewSet):
    serializer_class = serializers.GuildSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = models.Guild.objects.all()

class LeagueView(viewsets.ModelViewSet):

    serializer_class = serializers.LeagueSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = models.League.objects.all()

class LeaderboardView(viewsets.ModelViewSet):
    serializer_class = serializers.LeaderboardSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = annotations.leaderboards.qs_with_ranking()
    filterset_class = filters.LeaderboardFilter



class MatchEventView(viewsets.ModelViewSet):
    serializer_class = serializers.MatchEventSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = models.MatchEvent.objects.all()


class MatchView(viewsets.ModelViewSet):
    serializer_class = serializers.MatchSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filterset_class = filters.MatchFilter
    queryset = (models.Match
                .objects
                .select_related('guild')
                .prefetch_related(
                    'rosters__sc2_profile__leaderboards',

                    'matchteam_set',
                    'matchteam_set__rosters__sc2_profile__leaderboards',

                    'matchteam_set__rosters__lane__leaderboards',
                )
                .annotate(players=StringAgg(
                    'rosters__sc2_profile__name',
                    delimiter=', ',
                    distinct=True,
                ))
                .annotate(winners=StringAgg(
                    'match_winners__profile__name',
                    delimiter=', ',
                    distinct=True
                ))

                .order_by('-match_date')
                .all()
    )

    @action(methods=['GET'], detail=True)
    def events(self, request, *args, **kwargs):
        match: models.Match = self.get_object()
        events = (
            match
            .game_events
            .select_related('match', 'profile', 'opposing_profile')
            .prefetch_related(
                'profile__leaderboards',
                'opposing_profile__leaderboards',
            )

            .all().order_by('game_time')
        )

        serializer = serializers.GameEventSerializer(events, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=True)
    def yourmom(self, request, *args, **kwargs):
        return Response(self.get_object().details, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True)
    def details(self, request, *args, **kwargs):
        match: models.Match = self.get_object()
        rosters = (
            models.Roster
                .objects
                .select_related('sc2_profile')
                .filter(match=match)
                .order_by('team_number', 'position_number')
        )
        basic_match_data = serializers.MatchSerializer(match).data
        # leaderboards = {l.toon.id:l for l in list(annotations.leaderboards.qs_with_ranking())}
        teams = collections.defaultdict(dict)
        for r in rosters:
            key = utils.position_number_to_team_string(r.position_number)
            if teams[key].get('players') is None:
                teams[key]['players'] = []
            teams[key]['name'] = key

            teams[key]['players'].append(serializers.SC2ProfileSerializer(r.sc2_profile).data)
            teams[key]['players'][-1]['position_number'] = r.position_number
            elo = 'n/a'
            num_games = 'n/a'
            joined = 'n/a'
            replay = 'n/a'
            if hasattr(r.sc2_profile, 'leaderboard'):
                elo = r.sc2_profile.leaderboard.elo
                num_games = r.sc2_profile.leaderboard.games
                joined = r.sc2_profile.leaderboard.created
            if hasattr(match, 'replay'):
                replay = match.replay.file.url

            teams[key]['players'][-1]['elo'] = elo
            teams[key]['players'][-1]['num_games'] = num_games
            teams[key]['players'][-1]['joined'] = joined
            winners = [x.strip() for x in basic_match_data['winners'].split(',')]
            teams[key]['winner'] = r.sc2_profile.name in winners

        example = [
            {
                'name': 'Toxicpanda',
                'vs': [
                    {
                        'name': 'Fred',
                        'units': [
                            {
                                'name': 'MercReaper',
                                'made': 6,
                                'killed': 5,
                                'lost': 6,
                            }
                        ]
                    }
                ]
            }
        ]
        teams = [v for v in teams.values()]
        stats = {}
        container = []
        vs = {}
        player = {}
        last_opponent = ""
        globals = {}
        for s in (
                models.UnitStat.objects
                        .select_related('sc2_profile', 'opposing_profile', 'unit')
                        .filter(match=match).order_by('sc2_profile', '-opposing_profile', 'unit')):
            s: models.UnitStat
            p_name = s.sc2_profile.name
            op_name = s.opposing_profile.name if s.opposing_profile else "Global"
            u_name = s.unit.name

            if op_name != last_opponent:
                if vs:
                    player['vs'].append(vs)
                vs = {'name': op_name, 'units': []}

            if player.get('name') != p_name:
                if player:
                    container.append(player)
                player = {'name': p_name, 'vs': []}
                player['avatar'] = s.sc2_profile.avatar_url if s.sc2_profile else None
                globals = {}

            if op_name == 'Global':
                globals[u_name] = s.made
            # print(p_name, op_name, u_name, globals[u_name])
            unit = {'name': u_name, 'made': globals.get(u_name, 0), 'killed': s.killed, 'lost': s.lost}
            vs['units'].append(unit)

            last_opponent = op_name

        player['vs'].append(vs)
        container.append(player)  # Append last player

        # player_list = serializers.SC2ProfileSerializer(players, many=True).data
        return Response({'basic': basic_match_data, 'teams': teams, 'stats': container, 'replay': replay})


class OLDMatchView(viewsets.ModelViewSet):
    serializer_class = serializers.MatchSerializer
    filterset_class = filters.MatchFilter
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = annotations.matches.qs_with_players()

    def get_queryset(self):
        """
        Add Querystring parameters

        league : league to use
        ranked: Ranking to use
        Returns
        -------

        """

        obj = annotations.matches.qs_with_players()
        #if self.request.query_params:
        #    # TODO A better way?
        #    params = utils.make_filter_params(self.request.query_params)
        #    obj = obj.filter(**params)
        return obj



    @action(methods=['GET'], detail=True)
    def events(self, request, *args, **kwargs):
        match: models.Match = self.get_object()
        events = match.events.all()

        serializer = serializers.MatchEventSerializer(events, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=True)
    def details(self, request, *args, **kwargs):
        match: models.Match = self.get_object()
        rosters = (
            models.Roster
            .objects
            .select_related('sc2_profile')
            .filter(match=match)
            .order_by('team_number', 'position_number')
        )
        basic_match_data = serializers.MatchSerializer(match).data
        #leaderboards = {l.toon.id:l for l in list(annotations.leaderboards.qs_with_ranking())}
        teams = collections.defaultdict(dict)
        for r in rosters:
            key = utils.position_number_to_team_string(r.position_number)
            if teams[key].get('players') is None:
                teams[key]['players'] = []
            teams[key]['name'] = key

            teams[key]['players'].append(serializers.SC2ProfileSerializer(r.sc2_profile).data)
            teams[key]['players'][-1]['position_number'] = r.position_number
            elo = 'n/a'
            num_games = 'n/a'
            joined = 'n/a'
            replay = 'n/a'
            if hasattr(r.sc2_profile, 'leaderboard'):
                elo = r.sc2_profile.leaderboard.elo
                num_games = r.sc2_profile.leaderboard.games
                joined = r.sc2_profile.leaderboard.created
            if hasattr(match, 'replay'):
                replay = match.replay.file.url

            teams[key]['players'][-1]['elo'] = elo
            teams[key]['players'][-1]['num_games'] = num_games
            teams[key]['players'][-1]['joined'] = joined
            winners = [x.strip() for x in basic_match_data['winners'].split(',')]
            teams[key]['winner'] = r.sc2_profile.name in winners

        example = [
            {
                'name': 'Toxicpanda',
                'vs': [
                    {
                        'name': 'Fred',
                        'units': [
                            {
                                'name': 'MercReaper',
                                'made': 6,
                                'killed': 5,
                                'lost': 6,
                            }
                        ]
                    }
                ]
            }
        ]
        teams = [v for v in teams.values()]
        stats = {}
        container = []
        vs = {}
        player = {}
        last_opponent = ""
        globals = {}
        for s in (
                models.UnitStat.objects
                .select_related('sc2_profile', 'opposing_profile', 'unit')
                .filter(match=match).order_by('sc2_profile', '-opposing_profile', 'unit')):
            s:models.UnitStat
            p_name = s.sc2_profile.name
            op_name = s.opposing_profile.name if s.opposing_profile else "Global"
            u_name = s.unit.name





            if op_name != last_opponent:
                if vs:
                    player['vs'].append(vs)
                vs = {'name': op_name, 'units': []}


            if player.get('name') != p_name:
                if player:
                    container.append(player)
                player = {'name': p_name, 'vs': []}
                player['avatar'] = s.sc2_profile.avatar_url if s.sc2_profile else None
                globals = {}

            if op_name == 'Global':
                globals[u_name] = s.made
            #print(p_name, op_name, u_name, globals[u_name])
            unit = {'name': u_name, 'made': globals.get(u_name, 0), 'killed': s.killed, 'lost': s.lost}
            vs['units'].append(unit)





            last_opponent = op_name


        player['vs'].append(vs)
        container.append(player) # Append last player




        #player_list = serializers.SC2ProfileSerializer(players, many=True).data
        return Response({'basic': basic_match_data, 'teams': teams, 'stats': container, 'replay': replay})

class AutoMatch(viewsets.ViewSet):
    permission_classes = (permissions.AllowAny,)


    def create(self, request):
        cache = {}
        #services.match.create(request.user, request.data)
        # TODO: Process signal and move code after viability
        data = request.data
        print(data.get('players'))
        players = [
            utils.fetch_or_create_profile(p['handle'], cache)
            for p in data.get('players', [])
        ]

        # Find streamers. A bit harder with all the relationships.

        users = [p.discord_users.all() for p in players]
        users = [u for sublist in users for u in sublist]

        stream_container = []
        streamers = models.TwitchStream.objects.filter(active=True, user__in=users)
        for s in streamers.all():
            for p in players:
                if s.user in p.discord_users.all():
                    stream_container.append({
                        'profile': serializers.SC2ProfileSerializer(p).data,
                        'stream': serializers.TwitchStreamSerializer(s).data,
                    })
        result = {
            'players': serializers.SC2ProfileSerializer(players, many=True).data,
            'streamers': stream_container
        }
        print(result)
        print([p.keys() for p in result['players']])
        print(json.dumps(result))
        import ws
        ws.send_notification(ws.types.NEW_MATCH_STREAM, result)



        return Response(status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def clients(self, request, *args, **kwargs):
        services.match.remove_client(request.data)
        return Response(status=status.HTTP_200_OK)


class ReplayView(viewsets.ModelViewSet):
    serializer_class = serializers.ReplaySerializer
    permission_classes = (permissions.AllowAny,)
    queryset = models.Replay.objects.annotate(game_id=F("match__game_id"))

    def create(self, request, *args, **kwargs):
        serializer = serializers.ReplaySerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            instance = serializer.save()
            parse_replay.delay(file_or_path=instance.id)
            return Response(status=status.HTTP_202_ACCEPTED)
        return Response(status=status.HTTP_400_BAD_REQUEST)
        # Parse the replay

        # Create the object if parse successfully

class CurrentUser(APIView):
    #permission_classes = (permissions.IsAuthenticated,)



    def get(self, request):
        response = {
            'authorized': False,
            'details': {},
            'token': None
        }
        user = request.user
        try:
            response['token'] = user.auth_token.key
            response['authorized'] = response['token'] is not None
        except:
            pass

        if not isinstance(user, AnonymousUser):
            response['details'] = serializers.UserSerializer(user).data

        return Response(response)


class ReplayUpload(APIView):
    parser_classes = (parsers.FileUploadParser,)


    def _process(self, request):
        user = request.user
        file: InMemoryUploadedFile = request.FILES['file']
        try:
            tmp_replay = Replay(file)
            game_id = tmp_replay.game_id
            file.name = str(game_id)

            if models.Match.objects.filter(id=game_id).count() > 0:
                log.debug(f"Uploaded Match Exists ({game_id})")
                return

            replay = models.Replay.objects.create(
                file=file,
                user=request.user,
                description='Auto Uploaded',
            )
            parse_replay.delay(pk=replay.id)

        except (NotZCReplay, IncompleteReplay) as e:
            log.debug(f'Received Invalid Replay: {e}')
            return


    def post(self, request):
        """
        This is used by our client to send a replay after its created.
        We will do some non-expensive checks if this is a valid replay.
        If so, we will offload the file to S3 and have our celery worker process it.


        Parameters
        ----------
        request

        Returns
        -------

        """
        self._process(request)
        return Response(status.HTTP_202_ACCEPTED)


class GameEventView(viewsets.ModelViewSet):
    serializer_class = serializers.GameEventSerializer
    filterset_class = filters.GameEventFilter
    queryset = models.GameEvent.objects.all().order_by('game_time')

class ChartPointView(APIView):
    """
    Custom API View to restrict to details for a given match id
    """

    def get(self, request, match_id):
        points = (
            models.ChartPoints
            .objects
            .select_related('profile')
            .filter(match=match_id)
            .annotate(name=F('profile__name'))
            .annotate(game_time=Cast('game_event__game_time', FloatField()))
            .order_by('game_event')

        )
        data = serializers.ChartPointSerializer(points, many=True).data
        return Response(data, status.HTTP_200_OK)

class ChartsView(APIView):
    def get(self, request, match_id):
        # Retrieve charts from API
        charts = self.request.query_params.get('charts')
        data = {}
        if charts is None:
            err = {'error': 'charts querystring is required'}
            return Response(err, status=status.HTTP_400_BAD_REQUEST)

        for c in charts.split(','):
            data[c] = utils.get_chart_from_s3(match_id, c)

        return Response(data, status=status.HTTP_200_OK)

class TeamView(viewsets.ModelViewSet):
    serializer_class = serializers.TeamSerializer
    queryset = (
        models
        .Team
        .objects
        .prefetch_related(
            'profiles__leaderboards'
        )
        .annotate(players=StringAgg(
            'profiles__name',
            delimiter=', '
        ))
        .annotate(team_elo=Avg(
            'profiles__leaderboards__elo'
        ))
        .annotate(games=Count(
            'matchteam'
        ))
        .annotate(wins=Count(
            'matchteam',
            filter=Q(matchteam__outcome='win')
        ))
        .annotate(losses=Count(
            'matchteam',
            filter=Q(matchteam__outcome='loss')
        ))
        .annotate(draws=Count(
            'matchteam',
            filter=Q(matchteam__outcome='draw')
        ))
        .annotate(win_rate=Case(
            When(games=0, then=0),
            default=(Decimal('1.0') * F("wins") / F("games")) * 100,
            output_field=DecimalField(),
        ))
        .all()
        .order_by('-team_elo')
    )


def lobbytest(request):
    data = """[{"bnetBucketId":1574816994,"bnetRecordId":16831055,"createdAt":"2020-02-26T02:25:50.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Special Forces","mapVariantCategory":"Other","lobbyTitle":"brutal, go two","hostName":"MAJOR","slotsHumansTotal":11,"slotsHumansTaken":1,"region":{"code":"EU","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":3,"headerHash":null,"documentHash":null,"iconHash":"6fcf7af240f69dc7637d1c592bb10c0b5f67ea3fa87d4b1914028fe305f6d86a","document":{"bnetId":197387,"type":"map","name":"Special Forces Elite 5 [Release]"}},"players":[{"joinedAt":"2020-02-26T02:25:50.000Z","leftAt":null,"name":"MAJOR"},{"joinedAt":"2020-02-26T02:36:04.000Z","leftAt":"2020-02-26T02:37:43.000Z","name":"тимофей"},{"joinedAt":"2020-02-26T02:48:44.000Z","leftAt":"2020-02-26T02:48:46.000Z","name":"Taiwann"},{"joinedAt":"2020-02-26T02:58:57.000Z","leftAt":"2020-02-26T02:59:21.000Z","name":"echolon"}]},{"bnetBucketId":1574794309,"bnetRecordId":16373823,"createdAt":"2020-02-26T02:35:16.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Custom","mapVariantCategory":"Other","lobbyTitle":null,"hostName":"Tricky","slotsHumansTotal":12,"slotsHumansTaken":11,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":57,"headerHash":null,"documentHash":null,"iconHash":"e90ca2bd8bbcb8dd3b7fb95fa4531858930f523b406ff2caf533127e8b392074","document":{"bnetId":306970,"type":"map","name":"Island Defense V2.1"}},"players":[{"joinedAt":"2020-02-26T02:35:16.000Z","leftAt":null,"name":"Tricky"},{"joinedAt":"2020-02-26T02:35:48.000Z","leftAt":"2020-02-26T02:36:13.000Z","name":"Reiuss"},{"joinedAt":"2020-02-26T02:36:13.000Z","leftAt":"2020-02-26T02:43:43.000Z","name":"AceSnwFlk"},{"joinedAt":"2020-02-26T02:44:10.000Z","leftAt":"2020-02-26T02:49:34.000Z","name":"AdmiralAkbar"},{"joinedAt":"2020-02-26T02:45:49.000Z","leftAt":null,"name":"DeathScythe"},{"joinedAt":"2020-02-26T02:46:31.000Z","leftAt":"2020-02-26T02:48:24.000Z","name":"Testaclease"},{"joinedAt":"2020-02-26T02:47:47.000Z","leftAt":null,"name":"ILIKEPIE"},{"joinedAt":"2020-02-26T02:55:13.000Z","leftAt":"2020-02-26T03:00:05.000Z","name":"FatassBrian"},{"joinedAt":"2020-02-26T02:55:48.000Z","leftAt":"2020-02-26T03:00:41.000Z","name":"QcKennyTrap"},{"joinedAt":"2020-02-26T02:57:52.000Z","leftAt":null,"name":"LostZergling"},{"joinedAt":"2020-02-26T02:58:24.000Z","leftAt":"2020-02-26T03:00:41.000Z","name":"benjalel"},{"joinedAt":"2020-02-26T02:58:24.000Z","leftAt":"2020-02-26T03:00:41.000Z","name":"Shadevar"},{"joinedAt":"2020-02-26T02:59:32.000Z","leftAt":"2020-02-26T03:04:29.000Z","name":"Tarkor"},{"joinedAt":"2020-02-26T03:00:41.000Z","leftAt":"2020-02-26T03:04:29.000Z","name":"SnakeJuggler"},{"joinedAt":"2020-02-26T03:02:26.000Z","leftAt":"2020-02-26T03:02:55.000Z","name":"Cinder"},{"joinedAt":"2020-02-26T03:04:29.000Z","leftAt":"2020-02-26T03:05:37.000Z","name":"AzeMile"},{"joinedAt":"2020-02-26T03:07:02.000Z","leftAt":"2020-02-26T03:07:33.000Z","name":"Caveman"},{"joinedAt":"2020-02-26T03:09:15.000Z","leftAt":null,"name":"Najdorf"},{"joinedAt":"2020-02-26T03:10:32.000Z","leftAt":null,"name":"YuhBoyBrando"},{"joinedAt":"2020-02-26T03:11:30.000Z","leftAt":null,"name":"MystiCDeath"},{"joinedAt":"2020-02-26T03:11:50.000Z","leftAt":null,"name":"UnGenius"},{"joinedAt":"2020-02-26T03:11:50.000Z","leftAt":null,"name":"PcLegend"},{"joinedAt":"2020-02-26T03:11:50.000Z","leftAt":null,"name":"Alien"},{"joinedAt":"2020-02-26T03:13:19.000Z","leftAt":null,"name":"Zodiac"}]},{"bnetBucketId":1574794309,"bnetRecordId":16374604,"createdAt":"2020-02-26T02:39:06.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Deception","mapVariantCategory":"Other","lobbyTitle":null,"hostName":"JasonM","slotsHumansTotal":12,"slotsHumansTaken":4,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":58,"headerHash":null,"documentHash":null,"iconHash":"e92d868c652ee6718bfc709894b507aa2ac3ab39478cc3589a05333923db4ae9","document":{"bnetId":312011,"type":"map","name":"Fall of Aphaidia"}},"players":[{"joinedAt":"2020-02-26T02:39:06.000Z","leftAt":"2020-02-26T03:11:16.000Z","name":"Aahz"},{"joinedAt":"2020-02-26T02:39:07.000Z","leftAt":null,"name":"JasonM"},{"joinedAt":"2020-02-26T02:40:45.000Z","leftAt":null,"name":"MrBrunoh"},{"joinedAt":"2020-02-26T02:48:27.000Z","leftAt":null,"name":"Fire"},{"joinedAt":"2020-02-26T03:05:22.000Z","leftAt":"2020-02-26T03:12:35.000Z","name":"VILLAINMAKER"},{"joinedAt":"2020-02-26T03:05:53.000Z","leftAt":null,"name":"One"},{"joinedAt":"2020-02-26T03:06:49.000Z","leftAt":"2020-02-26T03:09:57.000Z","name":"KilledJoy"},{"joinedAt":"2020-02-26T03:09:04.000Z","leftAt":"2020-02-26T03:11:16.000Z","name":"dudeitsdan"}]},{"bnetBucketId":1574816994,"bnetRecordId":16831531,"createdAt":"2020-02-26T02:42:40.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Standard Mode","mapVariantCategory":"Other","lobbyTitle":"GOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO","hostName":"Mamiso","slotsHumansTotal":14,"slotsHumansTaken":1,"region":{"code":"EU","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":102,"headerHash":null,"documentHash":null,"iconHash":"18505ae19d786dfe838d4c6ab9a14f1bb7b653be241fac5b9cce98ffbd13c7dc","document":{"bnetId":165576,"type":"map","name":"[Probes vs Zealot 2]"}},"players":[{"joinedAt":"2020-02-26T02:42:40.000Z","leftAt":"2020-02-26T02:42:59.000Z","name":"Barret"},{"joinedAt":"2020-02-26T02:42:40.000Z","leftAt":null,"name":"Mamiso"},{"joinedAt":"2020-02-26T02:42:47.000Z","leftAt":"2020-02-26T02:43:06.000Z","name":"Blacksquad"},{"joinedAt":"2020-02-26T02:42:54.000Z","leftAt":"2020-02-26T02:43:02.000Z","name":"CrocDog"},{"joinedAt":"2020-02-26T02:43:02.000Z","leftAt":"2020-02-26T02:43:22.000Z","name":"defaultPl"},{"joinedAt":"2020-02-26T02:43:04.000Z","leftAt":"2020-02-26T02:43:13.000Z","name":"Killabone"}]},{"bnetBucketId":1574802246,"bnetRecordId":11071752,"createdAt":"2020-02-26T02:53:34.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"General","mapVariantCategory":"Strategy","lobbyTitle":"빨리 들어와 겜좀 하자","hostName":"나는빠크빠크박임","slotsHumansTotal":9,"slotsHumansTaken":2,"region":{"code":"KR","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":83,"headerHash":null,"documentHash":null,"iconHash":"3dcb8298337ca667884da018880d7212a67b7519ed80b1419f5df8995a3c59c9","document":{"bnetId":136342,"type":"map","name":"중세 전쟁 4.0 (Europe) +"}},"players":[{"joinedAt":"2020-02-26T02:53:34.000Z","leftAt":"2020-02-26T02:54:52.000Z","name":"전쟁강림"},{"joinedAt":"2020-02-26T02:53:35.000Z","leftAt":null,"name":"나는빠크빠크박임"},{"joinedAt":"2020-02-26T02:57:51.000Z","leftAt":"2020-02-26T03:05:17.000Z","name":"미스미소우"},{"joinedAt":"2020-02-26T03:02:35.000Z","leftAt":"2020-02-26T03:03:03.000Z","name":"ADHD"},{"joinedAt":"2020-02-26T03:10:10.000Z","leftAt":"2020-02-26T03:10:49.000Z","name":"간디"},{"joinedAt":"2020-02-26T03:11:30.000Z","leftAt":"2020-02-26T03:13:38.000Z","name":"park"},{"joinedAt":"2020-02-26T03:12:41.000Z","leftAt":null,"name":"카멜레온"}]},{"bnetBucketId":1574802246,"bnetRecordId":11071928,"createdAt":"2020-02-26T02:55:16.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"[기본모드]","mapVariantCategory":"Hero Battle","lobbyTitle":null,"hostName":"카친스키","slotsHumansTotal":8,"slotsHumansTaken":2,"region":{"code":"KR","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":181,"headerHash":null,"documentHash":null,"iconHash":"fe03628e1dda7e6b598381af7eb3430d3410c4e0be142ac70377853aabda816b","document":{"bnetId":135581,"type":"map","name":"파오캐 리마스터 수정맵"}},"players":[{"joinedAt":"2020-02-26T02:55:16.000Z","leftAt":null,"name":"카친스키"},{"joinedAt":"2020-02-26T03:09:40.000Z","leftAt":null,"name":"Unji"},{"joinedAt":"2020-02-26T03:12:02.000Z","leftAt":"2020-02-26T03:13:03.000Z","name":"남조선레오"}]},{"bnetBucketId":1574802246,"bnetRecordId":11072148,"createdAt":"2020-02-26T02:58:46.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Death Match","mapVariantCategory":"Hero Battle","lobbyTitle":null,"hostName":"背叛","slotsHumansTotal":10,"slotsHumansTaken":4,"region":{"code":"KR","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":992,"headerHash":null,"documentHash":null,"iconHash":"c4b23bd4c063745943126d19ff56f02f6be73326bc197c29fc679e65afab017f","document":{"bnetId":101915,"type":"map","name":"동방월령전 프로토타입"}},"players":[{"joinedAt":"2020-02-26T02:58:46.000Z","leftAt":null,"name":"背叛"},{"joinedAt":"2020-02-26T02:59:06.000Z","leftAt":"2020-02-26T03:00:22.000Z","name":"PlusMinus"},{"joinedAt":"2020-02-26T02:59:06.000Z","leftAt":null,"name":"산과내"},{"joinedAt":"2020-02-26T03:04:24.000Z","leftAt":null,"name":"BTK"},{"joinedAt":"2020-02-26T03:05:08.000Z","leftAt":"2020-02-26T03:08:43.000Z","name":"천사표전사"},{"joinedAt":"2020-02-26T03:05:51.000Z","leftAt":null,"name":"onriCnoogarD"},{"joinedAt":"2020-02-26T03:05:51.000Z","leftAt":"2020-02-26T03:07:01.000Z","name":"밀크림"},{"joinedAt":"2020-02-26T03:06:17.000Z","leftAt":"2020-02-26T03:08:17.000Z","name":"인간실격"},{"joinedAt":"2020-02-26T03:08:17.000Z","leftAt":"2020-02-26T03:08:43.000Z","name":"dddddddddddd"}]},{"bnetBucketId":1574794309,"bnetRecordId":16378797,"createdAt":"2020-02-26T02:59:35.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"All Pick Standard","mapVariantCategory":"Hero Battle","lobbyTitle":null,"hostName":"Mars","slotsHumansTotal":12,"slotsHumansTaken":5,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":5,"minorVersion":86,"headerHash":null,"documentHash":null,"iconHash":"15bdbd051f2a02ec8b2fbece286264caf36911abf4056a29f40ca9483e666921","document":{"bnetId":275359,"type":"map","name":"Baseship Commanders 5.0"}},"players":[{"joinedAt":"2020-02-26T02:59:35.000Z","leftAt":null,"name":"Cole"},{"joinedAt":"2020-02-26T03:03:09.000Z","leftAt":null,"name":"Mars"},{"joinedAt":"2020-02-26T03:08:33.000Z","leftAt":null,"name":"Weyoun"},{"joinedAt":"2020-02-26T03:11:07.000Z","leftAt":"2020-02-26T03:13:22.000Z","name":"Doctordabz"},{"joinedAt":"2020-02-26T03:11:07.000Z","leftAt":"2020-02-26T03:11:58.000Z","name":"JBtheGamer"},{"joinedAt":"2020-02-26T03:12:26.000Z","leftAt":null,"name":"deeepwater"},{"joinedAt":"2020-02-26T03:12:51.000Z","leftAt":null,"name":"Dragon"}]},{"bnetBucketId":1574794309,"bnetRecordId":16378820,"createdAt":"2020-02-26T02:59:53.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"1v10","mapVariantCategory":"Other","lobbyTitle":null,"hostName":"ChuckNorris","slotsHumansTotal":11,"slotsHumansTaken":2,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":50,"headerHash":null,"documentHash":null,"iconHash":"d542138878698dd4bb2baa80b97eb964826a454a90594795500fae1146951882","document":{"bnetId":311589,"type":"map","name":"Dungeon Master 2.0"}},"players":[{"joinedAt":"2020-02-26T02:59:53.000Z","leftAt":null,"name":"ChuckNorris"},{"joinedAt":"2020-02-26T03:12:38.000Z","leftAt":null,"name":"VILLAINMAKER"}]},{"bnetBucketId":1574816994,"bnetRecordId":16832016,"createdAt":"2020-02-26T03:00:11.000Z","closedAt":null,"status":"open","mapVariantIndex":2,"mapVariantMode":"2v2","mapVariantCategory":"Miscellaneous","lobbyTitle":null,"hostName":"YuraHo","slotsHumansTotal":4,"slotsHumansTaken":1,"region":{"code":"EU","name":""},"mapDocumentVersion":{"majorVersion":0,"minorVersion":11,"headerHash":null,"documentHash":null,"iconHash":"952ece51ec97c9a408c1e788b934ef093cc3ec78e180f1e47e5d51e388a81d35","document":{"bnetId":160652,"type":"map","name":"Nexus Wars - Center Bridge (Updated)"}},"players":[{"joinedAt":"2020-02-26T03:00:11.000Z","leftAt":null,"name":"YuraHo"},{"joinedAt":"2020-02-26T03:04:06.000Z","leftAt":"2020-02-26T03:04:49.000Z","name":"TotalEclipse"},{"joinedAt":"2020-02-26T03:04:06.000Z","leftAt":"2020-02-26T03:04:49.000Z","name":"Nogahfergi"}]},{"bnetBucketId":1574802246,"bnetRecordId":11072240,"createdAt":"2020-02-26T03:00:15.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Cooperative","mapVariantCategory":"Action","lobbyTitle":null,"hostName":"joonJuL","slotsHumansTotal":7,"slotsHumansTaken":1,"region":{"code":"KR","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":109,"headerHash":null,"documentHash":null,"iconHash":"38eef9fc3c022fbebe6f6011af1ddb1441f894b3e46d17d1d281d382350b5522","document":{"bnetId":124307,"type":"map","name":"Oh No It's Zombies NEW"}},"players":[{"joinedAt":"2020-02-26T03:00:15.000Z","leftAt":null,"name":"joonJuL"},{"joinedAt":"2020-02-26T03:10:54.000Z","leftAt":"2020-02-26T03:11:09.000Z","name":"간디"}]},{"bnetBucketId":1574794309,"bnetRecordId":16379149,"createdAt":"2020-02-26T03:01:17.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Standard","mapVariantCategory":"Strategy","lobbyTitle":"l337 PSIONIC PROTOSS CQC QUARTERS COMBAT KILLFEST NO CENSORSHIP","hostName":"cwal","slotsHumansTotal":12,"slotsHumansTaken":1,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":3,"headerHash":null,"documentHash":null,"iconHash":"6f4321e2bdc92cd11b8e99a5dc583c2b77ffbafa7801767de367d54db025dff1","document":{"bnetId":311094,"type":"map","name":"Planet Protoss Tribes - Forgotten Isles"}},"players":[{"joinedAt":"2020-02-26T03:01:17.000Z","leftAt":null,"name":"cwal"}]},{"bnetBucketId":1574802246,"bnetRecordId":11072424,"createdAt":"2020-02-26T03:02:55.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"공개게임용","mapVariantCategory":"Puzzle","lobbyTitle":null,"hostName":"SEUAI","slotsHumansTotal":8,"slotsHumansTaken":4,"region":{"code":"KR","name":""},"mapDocumentVersion":{"majorVersion":0,"minorVersion":469,"headerHash":null,"documentHash":null,"iconHash":"f62f33dfadde0123864872188f41323a5f3bcd6538d0a09393332738d159643c","document":{"bnetId":86515,"type":"map","name":"뱅!"}},"players":[{"joinedAt":"2020-02-26T03:02:55.000Z","leftAt":null,"name":"SEUAI"},{"joinedAt":"2020-02-26T03:06:47.000Z","leftAt":null,"name":"물뜨겁"},{"joinedAt":"2020-02-26T03:07:39.000Z","leftAt":null,"name":"하삼"},{"joinedAt":"2020-02-26T03:09:43.000Z","leftAt":"2020-02-26T03:12:04.000Z","name":"때재배"},{"joinedAt":"2020-02-26T03:12:04.000Z","leftAt":null,"name":"블루카리"}]},{"bnetBucketId":1574802246,"bnetRecordId":11072444,"createdAt":"2020-02-26T03:03:16.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"일반 매칭","mapVariantCategory":"Other","lobbyTitle":null,"hostName":"StarShip","slotsHumansTotal":10,"slotsHumansTaken":5,"region":{"code":"KR","name":""},"mapDocumentVersion":{"majorVersion":0,"minorVersion":404,"headerHash":null,"documentHash":null,"iconHash":"af4c3227401467cdb88dd8a54952934557989a650958d55c07c50ef87815bc77","document":{"bnetId":126840,"type":"map","name":"NEW 배틀쉽"}},"players":[{"joinedAt":"2020-02-26T03:03:16.000Z","leftAt":null,"name":"StarShip"},{"joinedAt":"2020-02-26T03:03:42.000Z","leftAt":"2020-02-26T03:04:09.000Z","name":"SIN"},{"joinedAt":"2020-02-26T03:04:37.000Z","leftAt":null,"name":"Rolex"},{"joinedAt":"2020-02-26T03:05:19.000Z","leftAt":"2020-02-26T03:05:46.000Z","name":"리버풀"},{"joinedAt":"2020-02-26T03:10:08.000Z","leftAt":null,"name":"소사"},{"joinedAt":"2020-02-26T03:10:59.000Z","leftAt":null,"name":"환웅"},{"joinedAt":"2020-02-26T03:11:41.000Z","leftAt":null,"name":"불한당"},{"joinedAt":"2020-02-26T03:13:49.000Z","leftAt":null,"name":"샤애나"}]},{"bnetBucketId":1574816994,"bnetRecordId":16832099,"createdAt":"2020-02-26T03:03:31.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Normal","mapVariantCategory":"Survival","lobbyTitle":null,"hostName":"jaggerjake","slotsHumansTotal":8,"slotsHumansTaken":2,"region":{"code":"EU","name":""},"mapDocumentVersion":{"majorVersion":3,"minorVersion":30,"headerHash":null,"documentHash":null,"iconHash":"81fddefd0e199c3f57cbdd3fd4a408b11afcc2c92809863384b4d84a883cc79b","document":{"bnetId":201419,"type":"map","name":"Zerg Hex"}},"players":[{"joinedAt":"2020-02-26T03:03:31.000Z","leftAt":null,"name":"jaggerjake"},{"joinedAt":"2020-02-26T03:04:44.000Z","leftAt":"2020-02-26T03:04:49.000Z","name":"Midnight"},{"joinedAt":"2020-02-26T03:04:58.000Z","leftAt":"2020-02-26T03:10:09.000Z","name":"Selemon"},{"joinedAt":"2020-02-26T03:06:17.000Z","leftAt":null,"name":"TheRealTerra"},{"joinedAt":"2020-02-26T03:09:03.000Z","leftAt":"2020-02-26T03:09:08.000Z","name":"Clody"}]},{"bnetBucketId":1574794309,"bnetRecordId":16379716,"createdAt":"2020-02-26T03:04:04.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Lobby 1","mapVariantCategory":"Other","lobbyTitle":null,"hostName":"DarkKnight","slotsHumansTotal":14,"slotsHumansTaken":4,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":4,"headerHash":null,"documentHash":null,"iconHash":"7ddf80f0daf4fc4de640a6cf02879b42e614744964896ad6d6c5ec5d302e10fe","document":{"bnetId":307542,"type":"map","name":"Apex Roleplay - Interplanetary"}},"players":[{"joinedAt":"2020-02-26T03:04:04.000Z","leftAt":null,"name":"DarkKnight"},{"joinedAt":"2020-02-26T03:04:41.000Z","leftAt":null,"name":"Matzerg"},{"joinedAt":"2020-02-26T03:09:23.000Z","leftAt":null,"name":"ericthree"},{"joinedAt":"2020-02-26T03:09:23.000Z","leftAt":null,"name":"strikerbeast"}]},{"bnetBucketId":1574794309,"bnetRecordId":16379748,"createdAt":"2020-02-26T03:04:13.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"3v3v3v3","mapVariantCategory":"Other","lobbyTitle":null,"hostName":"Gavi","slotsHumansTotal":12,"slotsHumansTaken":1,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":392,"headerHash":null,"documentHash":null,"iconHash":"f0c37a3d2c163990f97d1551a249859eef93b7d8b7e8becab4af49f932d70f63","document":{"bnetId":181076,"type":"map","name":"Zealot_Frenzy"}},"players":[{"joinedAt":"2020-02-26T03:04:13.000Z","leftAt":null,"name":"Gavi"},{"joinedAt":"2020-02-26T03:09:58.000Z","leftAt":"2020-02-26T03:10:52.000Z","name":"ShadowMan"},{"joinedAt":"2020-02-26T03:11:19.000Z","leftAt":"2020-02-26T03:13:37.000Z","name":"Skeixrya"},{"joinedAt":"2020-02-26T03:11:19.000Z","leftAt":"2020-02-26T03:13:37.000Z","name":"Sogera"},{"joinedAt":"2020-02-26T03:12:11.000Z","leftAt":"2020-02-26T03:13:37.000Z","name":"Osiristar"},{"joinedAt":"2020-02-26T03:12:38.000Z","leftAt":"2020-02-26T03:13:12.000Z","name":"VivisectionX"}]},{"bnetBucketId":1574794309,"bnetRecordId":16379749,"createdAt":"2020-02-26T03:04:13.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Cooperative","mapVariantCategory":"Action","lobbyTitle":null,"hostName":"Zomana","slotsHumansTotal":7,"slotsHumansTaken":1,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":132,"headerHash":null,"documentHash":null,"iconHash":"38eef9fc3c022fbebe6f6011af1ddb1441f894b3e46d17d1d281d382350b5522","document":{"bnetId":309215,"type":"map","name":"Oh No It's Zombies Arctic Updated"}},"players":[{"joinedAt":"2020-02-26T03:04:13.000Z","leftAt":null,"name":"Zomana"},{"joinedAt":"2020-02-26T03:09:10.000Z","leftAt":"2020-02-26T03:10:53.000Z","name":"benjalel"}]},{"bnetBucketId":1574794309,"bnetRecordId":16379742,"createdAt":"2020-02-26T03:04:13.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Blind Pick","mapVariantCategory":"Hero Battle","lobbyTitle":null,"hostName":"KrnkasaursRx","slotsHumansTotal":10,"slotsHumansTaken":4,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":2,"minorVersion":73,"headerHash":null,"documentHash":null,"iconHash":"3900c9eefbc48ad5613d57fc6627f1952e1f9f26a672884e51ee72ff39db6763","document":{"bnetId":175600,"type":"map","name":"Aeon of Storms"}},"players":[{"joinedAt":"2020-02-26T03:04:13.000Z","leftAt":null,"name":"KrnkasaursRx"},{"joinedAt":"2020-02-26T03:07:21.000Z","leftAt":null,"name":"TyRaNt"},{"joinedAt":"2020-02-26T03:11:08.000Z","leftAt":null,"name":"Trogdor"},{"joinedAt":"2020-02-26T03:11:58.000Z","leftAt":null,"name":"Worker"}]},{"bnetBucketId":1574794309,"bnetRecordId":16379845,"createdAt":"2020-02-26T03:04:37.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Classic MM","mapVariantCategory":"Strategy","lobbyTitle":null,"hostName":"Aragorn","slotsHumansTotal":10,"slotsHumansTaken":3,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":21,"headerHash":null,"documentHash":null,"iconHash":"8b2fdf850a9899a15ba7f6d461828560d5000c694f3da17fa77f86879fd602f2","document":{"bnetId":305697,"type":"map","name":"LoZ: Majora's Mask"}},"players":[{"joinedAt":"2020-02-26T03:04:37.000Z","leftAt":null,"name":"Aragorn"},{"joinedAt":"2020-02-26T03:05:15.000Z","leftAt":null,"name":"Derkdeberk"},{"joinedAt":"2020-02-26T03:11:07.000Z","leftAt":null,"name":"KilledJoy"},{"joinedAt":"2020-02-26T03:12:30.000Z","leftAt":"2020-02-26T03:12:57.000Z","name":"Spruance"}]},{"bnetBucketId":1574794309,"bnetRecordId":16379958,"createdAt":"2020-02-26T03:05:05.000Z","closedAt":null,"status":"open","mapVariantIndex":2,"mapVariantMode":"1V1","mapVariantCategory":"Tug Of War","lobbyTitle":"","hostName":"iMVegeta","slotsHumansTotal":2,"slotsHumansTaken":1,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":36,"headerHash":null,"documentHash":null,"iconHash":"9e73d66c93c0f74b7ab1bb6584efb0ba72034448286ba6c3c1dae067f05bb749","document":{"bnetId":276093,"type":"map","name":"Desert Strike Azure"}},"players":[{"joinedAt":"2020-02-26T03:05:05.000Z","leftAt":null,"name":"iMVegeta"}]},{"bnetBucketId":1574794309,"bnetRecordId":16380046,"createdAt":"2020-02-26T03:05:45.000Z","closedAt":null,"status":"open","mapVariantIndex":3,"mapVariantMode":"4V4","mapVariantCategory":"Melee","lobbyTitle":"Level 2.5 hard","hostName":"BlueTango","slotsHumansTotal":8,"slotsHumansTaken":5,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":0,"minorVersion":2,"headerHash":null,"documentHash":null,"iconHash":"bb8465c2d867792de5347b43551d0ef9df4a451905bd0ce367bda0bc818f4322","document":{"bnetId":308960,"type":"map","name":"Golden Micro Jail 2"}},"players":[{"joinedAt":"2020-02-26T03:05:45.000Z","leftAt":null,"name":"BlueTango"},{"joinedAt":"2020-02-26T03:06:15.000Z","leftAt":null,"name":"SpaceJanitor"},{"joinedAt":"2020-02-26T03:06:41.000Z","leftAt":null,"name":"FLIPIC"},{"joinedAt":"2020-02-26T03:07:37.000Z","leftAt":"2020-02-26T03:10:10.000Z","name":"ManuGames"},{"joinedAt":"2020-02-26T03:10:37.000Z","leftAt":null,"name":"Willybeast"},{"joinedAt":"2020-02-26T03:13:21.000Z","leftAt":null,"name":"SoNiC"}]},{"bnetBucketId":1574816994,"bnetRecordId":16832147,"createdAt":"2020-02-26T03:05:51.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"3x Select","mapVariantCategory":"Tower Defense","lobbyTitle":null,"hostName":"Rayko","slotsHumansTotal":8,"slotsHumansTaken":2,"region":{"code":"EU","name":""},"mapDocumentVersion":{"majorVersion":8,"minorVersion":9,"headerHash":null,"documentHash":null,"iconHash":"b5ac77f95f6fcb98aac8dd3ff188bd6344f589f88613ce1845b7ae4605c471ad","document":{"bnetId":185304,"type":"map","name":"Squadron TD Beta"}},"players":[{"joinedAt":"2020-02-26T03:05:51.000Z","leftAt":null,"name":"Sharo"},{"joinedAt":"2020-02-26T03:06:57.000Z","leftAt":"2020-02-26T03:12:50.000Z","name":"mrpula"},{"joinedAt":"2020-02-26T03:08:22.000Z","leftAt":null,"name":"Rayko"},{"joinedAt":"2020-02-26T03:10:24.000Z","leftAt":"2020-02-26T03:10:25.000Z","name":"Theshame"},{"joinedAt":"2020-02-26T03:10:34.000Z","leftAt":"2020-02-26T03:13:38.000Z","name":"elmacho"},{"joinedAt":"2020-02-26T03:11:06.000Z","leftAt":"2020-02-26T03:13:01.000Z","name":"Selemon"}]},{"bnetBucketId":1574794309,"bnetRecordId":16380277,"createdAt":"2020-02-26T03:06:53.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Siege","mapVariantCategory":"Strategy","lobbyTitle":null,"hostName":"Reaper","slotsHumansTotal":10,"slotsHumansTaken":2,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":46,"headerHash":null,"documentHash":null,"iconHash":"706f6c835842420d7da01d197c34b51468e6fcc4d0ed1832ed0eddf5abaa79ac","document":{"bnetId":277057,"type":"map","name":"Heaven Besieged: Ultimate"}},"players":[{"joinedAt":"2020-02-26T03:06:53.000Z","leftAt":null,"name":"Reaper"},{"joinedAt":"2020-02-26T03:06:55.000Z","leftAt":"2020-02-26T03:12:34.000Z","name":"twentysixxx"},{"joinedAt":"2020-02-26T03:07:26.000Z","leftAt":null,"name":"Anna"},{"joinedAt":"2020-02-26T03:08:17.000Z","leftAt":"2020-02-26T03:11:42.000Z","name":"amjake"},{"joinedAt":"2020-02-26T03:10:23.000Z","leftAt":"2020-02-26T03:13:03.000Z","name":"Guy"}]},{"bnetBucketId":1574802246,"bnetRecordId":11072728,"createdAt":"2020-02-26T03:07:24.000Z","closedAt":null,"status":"open","mapVariantIndex":1,"mapVariantMode":"플레이어 10명","mapVariantCategory":"Other","lobbyTitle":null,"hostName":"MilkyWay","slotsHumansTotal":10,"slotsHumansTaken":3,"region":{"code":"KR","name":""},"mapDocumentVersion":{"majorVersion":0,"minorVersion":232,"headerHash":null,"documentHash":null,"iconHash":"20f055c29db2989f1f8529760e4bc68f506b830c7d7d8e61c69fe36c8fba647c","document":{"bnetId":133092,"type":"map","name":"유닛 골라 키우기"}},"players":[{"joinedAt":"2020-02-26T03:07:24.000Z","leftAt":"2020-02-26T03:13:05.000Z","name":"송하나"},{"joinedAt":"2020-02-26T03:07:25.000Z","leftAt":"2020-02-26T03:13:24.000Z","name":"CfC"},{"joinedAt":"2020-02-26T03:09:13.000Z","leftAt":null,"name":"MilkyWay"},{"joinedAt":"2020-02-26T03:11:04.000Z","leftAt":"2020-02-26T03:13:50.000Z","name":"커신이커엽"},{"joinedAt":"2020-02-26T03:11:18.000Z","leftAt":null,"name":"한번더해요"},{"joinedAt":"2020-02-26T03:11:44.000Z","leftAt":null,"name":"ehdgks"},{"joinedAt":"2020-02-26T03:13:50.000Z","leftAt":null,"name":"crossfire"}]},{"bnetBucketId":1574802246,"bnetRecordId":11072753,"createdAt":"2020-02-26T03:07:33.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Zeta","mapVariantCategory":"Other","lobbyTitle":null,"hostName":"ALEPH","slotsHumansTotal":12,"slotsHumansTaken":12,"region":{"code":"KR","name":""},"mapDocumentVersion":{"majorVersion":3,"minorVersion":64,"headerHash":null,"documentHash":null,"iconHash":"b076eecd5deb758f69860284cd983bc49706ecc7bcb4cb39ae49aff5ae0ffab3","document":{"bnetId":127526,"type":"map","name":"P A R A S I T E - ZETA"}},"players":[{"joinedAt":"2020-02-26T03:07:33.000Z","leftAt":null,"name":"ALEPH"},{"joinedAt":"2020-02-26T03:07:45.000Z","leftAt":null,"name":"개빠아진"},{"joinedAt":"2020-02-26T03:07:45.000Z","leftAt":null,"name":"늠마"},{"joinedAt":"2020-02-26T03:07:45.000Z","leftAt":null,"name":"봉추선생"},{"joinedAt":"2020-02-26T03:08:23.000Z","leftAt":null,"name":"드라군"},{"joinedAt":"2020-02-26T03:08:49.000Z","leftAt":null,"name":"뽀스뤠"},{"joinedAt":"2020-02-26T03:09:37.000Z","leftAt":null,"name":"metol"},{"joinedAt":"2020-02-26T03:09:37.000Z","leftAt":null,"name":"자네나에게오게나"},{"joinedAt":"2020-02-26T03:09:51.000Z","leftAt":null,"name":"벽짓살장인"},{"joinedAt":"2020-02-26T03:10:39.000Z","leftAt":null,"name":"우한폐렴숙주"},{"joinedAt":"2020-02-26T03:12:59.000Z","leftAt":"2020-02-26T03:13:12.000Z","name":"NightOwl"},{"joinedAt":"2020-02-26T03:13:12.000Z","leftAt":null,"name":"명탐정"},{"joinedAt":"2020-02-26T03:13:44.000Z","leftAt":null,"name":"함정이다"}]},{"bnetBucketId":1574794309,"bnetRecordId":16380373,"createdAt":"2020-02-26T03:07:52.000Z","closedAt":null,"status":"open","mapVariantIndex":3,"mapVariantMode":"1 vs 1","mapVariantCategory":"Survival","lobbyTitle":"1v1!  Come Play!","hostName":"ArcticRhino","slotsHumansTotal":2,"slotsHumansTaken":1,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":2,"minorVersion":12,"headerHash":null,"documentHash":null,"iconHash":"5b6bdaaf5d964ef18e4d79fb2a60d5dbed07fe33da102f541904e8348f507525","document":{"bnetId":314700,"type":"map","name":"Zerg Wars (Updated)"}},"players":[{"joinedAt":"2020-02-26T03:07:52.000Z","leftAt":null,"name":"ArcticRhino"}]},{"bnetBucketId":1574802246,"bnetRecordId":11072805,"createdAt":"2020-02-26T03:08:25.000Z","closedAt":null,"status":"open","mapVariantIndex":1,"mapVariantMode":"소녀 (보통)","mapVariantCategory":"Survival","lobbyTitle":"","hostName":"이카신","slotsHumansTotal":6,"slotsHumansTaken":3,"region":{"code":"KR","name":""},"mapDocumentVersion":{"majorVersion":0,"minorVersion":60,"headerHash":null,"documentHash":null,"iconHash":"c8ccd630e943fcdf2bde5a035033967ebbee2aa59ef66f54cd6396edd110fe56","document":{"bnetId":107369,"type":"map","name":"꿈꾸는 소녀"}},"players":[{"joinedAt":"2020-02-26T03:08:25.000Z","leftAt":null,"name":"이카신"},{"joinedAt":"2020-02-26T03:08:28.000Z","leftAt":null,"name":"지나가던천사"},{"joinedAt":"2020-02-26T03:08:28.000Z","leftAt":null,"name":"유메사"}]},{"bnetBucketId":1574794309,"bnetRecordId":16380652,"createdAt":"2020-02-26T03:08:34.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Standard","mapVariantCategory":"Arena","lobbyTitle":"Marine ARena","hostName":"Spriteisgood","slotsHumansTotal":8,"slotsHumansTaken":5,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":10,"minorVersion":15,"headerHash":null,"documentHash":null,"iconHash":"b6b9ba32a3b7b7ba58c6bd5e721cd876c3eae60e2fc50a09e4d24b7942191bfe","document":{"bnetId":217289,"type":"map","name":"Marine Arena US"}},"players":[{"joinedAt":"2020-02-26T03:08:34.000Z","leftAt":null,"name":"Spriteisgood"},{"joinedAt":"2020-02-26T03:09:02.000Z","leftAt":"2020-02-26T03:09:26.000Z","name":"natus"},{"joinedAt":"2020-02-26T03:10:18.000Z","leftAt":null,"name":"Daniel"},{"joinedAt":"2020-02-26T03:10:45.000Z","leftAt":null,"name":"DEMONIC"},{"joinedAt":"2020-02-26T03:13:00.000Z","leftAt":null,"name":"McDangles"}]},{"bnetBucketId":1574794309,"bnetRecordId":16380660,"createdAt":"2020-02-26T03:08:35.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Coop","mapVariantCategory":"Tower Defense","lobbyTitle":null,"hostName":"stealthwatch","slotsHumansTotal":4,"slotsHumansTaken":3,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":1,"headerHash":null,"documentHash":null,"iconHash":"cfb1ba498f222fbc48931a9168826845cd91678672263bb8bbaeb5002a6a383b","document":{"bnetId":314683,"type":"map","name":"Red Circle Fixed"}},"players":[{"joinedAt":"2020-02-26T03:08:35.000Z","leftAt":null,"name":"stealthwatch"},{"joinedAt":"2020-02-26T03:09:26.000Z","leftAt":"2020-02-26T03:10:19.000Z","name":"TheDarkOne"},{"joinedAt":"2020-02-26T03:11:41.000Z","leftAt":null,"name":"NOTmini"},{"joinedAt":"2020-02-26T03:13:33.000Z","leftAt":null,"name":"LTass"}]},{"bnetBucketId":1574802246,"bnetRecordId":11072835,"createdAt":"2020-02-26T03:08:55.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"술래잡기","mapVariantCategory":"Other","lobbyTitle":null,"hostName":"곰돌이","slotsHumansTotal":8,"slotsHumansTaken":1,"region":{"code":"KR","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":6,"headerHash":null,"documentHash":null,"iconHash":"34a1cebc7706a7dfce25a1d7d658c8ba301876db6d2da1001508717bfe15c131","document":{"bnetId":127248,"type":"map","name":"경찰과 도둑 Season6"}},"players":[{"joinedAt":"2020-02-26T03:08:55.000Z","leftAt":null,"name":"곰돌이"},{"joinedAt":"2020-02-26T03:11:23.000Z","leftAt":"2020-02-26T03:11:48.000Z","name":"남조선레오"}]},{"bnetBucketId":1574794309,"bnetRecordId":16380912,"createdAt":"2020-02-26T03:09:54.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Standard","mapVariantCategory":"Survival","lobbyTitle":"You did this to us Phant","hostName":"dragon","slotsHumansTotal":12,"slotsHumansTaken":9,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":2,"minorVersion":63,"headerHash":null,"documentHash":null,"iconHash":"ab055e3334e317a0ba8010a2870b6f2c77bb0ea3fe0dfd552373fdb111349ed7","document":{"bnetId":285940,"type":"map","name":"Undead Assault 3: Dasdan"}},"players":[{"joinedAt":"2020-02-26T03:09:54.000Z","leftAt":null,"name":"dragon"},{"joinedAt":"2020-02-26T03:10:23.000Z","leftAt":null,"name":"HealPlox"},{"joinedAt":"2020-02-26T03:10:50.000Z","leftAt":null,"name":"Caveman"},{"joinedAt":"2020-02-26T03:10:50.000Z","leftAt":null,"name":"cjk"},{"joinedAt":"2020-02-26T03:10:50.000Z","leftAt":null,"name":"Hacker"},{"joinedAt":"2020-02-26T03:11:17.000Z","leftAt":null,"name":"Phant"},{"joinedAt":"2020-02-26T03:11:17.000Z","leftAt":null,"name":"VeryWinter"},{"joinedAt":"2020-02-26T03:11:17.000Z","leftAt":"2020-02-26T03:12:38.000Z","name":"ZomboCom"},{"joinedAt":"2020-02-26T03:12:11.000Z","leftAt":null,"name":"lagseeing"},{"joinedAt":"2020-02-26T03:12:38.000Z","leftAt":null,"name":"fatman"}]},{"bnetBucketId":1574794309,"bnetRecordId":16380759,"createdAt":"2020-02-26T03:09:54.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Hero Defense","mapVariantCategory":"Arena","lobbyTitle":"Custom Hero Defense","hostName":"Astrocoroce","slotsHumansTotal":6,"slotsHumansTaken":2,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":3,"minorVersion":22,"headerHash":null,"documentHash":null,"iconHash":"9b6a86088c13a62beb53cc5fc4bd01f2403e7f13897ceac4be7c1ab70e249ef1","document":{"bnetId":219654,"type":"map","name":"Custom Hero Defense"}},"players":[{"joinedAt":"2020-02-26T03:09:54.000Z","leftAt":null,"name":"Astrocoroce"},{"joinedAt":"2020-02-26T03:11:14.000Z","leftAt":null,"name":"Passdatdooby"}]},{"bnetBucketId":1574794309,"bnetRecordId":16380887,"createdAt":"2020-02-26T03:09:54.000Z","closedAt":null,"status":"open","mapVariantIndex":1,"mapVariantMode":"1V1","mapVariantCategory":"Melee","lobbyTitle":"ladder map gogo","hostName":"TYTY","slotsHumansTotal":2,"slotsHumansTaken":1,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":0,"minorVersion":19,"headerHash":null,"documentHash":null,"iconHash":"f5d6f7e2bfb4133811339a1e76b538c92fd70787a565b3f914ec5ce47624bc63","document":{"bnetId":311728,"type":"map","name":"Ephemeron LE"}},"players":[{"joinedAt":"2020-02-26T03:09:54.000Z","leftAt":null,"name":"TYTY"},{"joinedAt":"2020-02-26T03:12:33.000Z","leftAt":"2020-02-26T03:13:02.000Z","name":"Rabbit"}]},{"bnetBucketId":1574794309,"bnetRecordId":16380947,"createdAt":"2020-02-26T03:09:54.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Cooperative","mapVariantCategory":"Action","lobbyTitle":"","hostName":"dathong","slotsHumansTotal":7,"slotsHumansTaken":1,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":405,"headerHash":null,"documentHash":null,"iconHash":"38eef9fc3c022fbebe6f6011af1ddb1441f894b3e46d17d1d281d382350b5522","document":{"bnetId":298114,"type":"map","name":"Oh No It's Zombies NEW"}},"players":[{"joinedAt":"2020-02-26T03:09:54.000Z","leftAt":null,"name":"dathong"}]},{"bnetBucketId":1574794309,"bnetRecordId":16380978,"createdAt":"2020-02-26T03:10:02.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Ranked 3v3","mapVariantCategory":"Tug Of War","lobbyTitle":null,"hostName":"Underscore","slotsHumansTotal":6,"slotsHumansTaken":5,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":4,"minorVersion":27,"headerHash":null,"documentHash":null,"iconHash":"50f9137f51d0ef4af3c858780952949a77d7060205a614ff2a511925fde89505","document":{"bnetId":296511,"type":"map","name":"KeyStone Card Game"}},"players":[{"joinedAt":"2020-02-26T03:10:02.000Z","leftAt":null,"name":"Underscore"},{"joinedAt":"2020-02-26T03:10:30.000Z","leftAt":null,"name":"Jinxz"},{"joinedAt":"2020-02-26T03:11:30.000Z","leftAt":null,"name":"Wolf"},{"joinedAt":"2020-02-26T03:13:20.000Z","leftAt":null,"name":"internet"},{"joinedAt":"2020-02-26T03:13:20.000Z","leftAt":null,"name":"Thox"},{"joinedAt":"2020-02-26T03:13:32.000Z","leftAt":null,"name":"Hannibal"}]},{"bnetBucketId":1574794309,"bnetRecordId":16380973,"createdAt":"2020-02-26T03:10:02.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Special Forces","mapVariantCategory":"Action","lobbyTitle":null,"hostName":"hades","slotsHumansTotal":6,"slotsHumansTaken":2,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":10,"headerHash":null,"documentHash":null,"iconHash":"57a95f6fab37ff18dc05ef9e231cf412cfb51e83061969424dd8a60315a52a4c","document":{"bnetId":183106,"type":"map","name":"Special Forces Elite 4: Shared Income"}},"players":[{"joinedAt":"2020-02-26T03:10:02.000Z","leftAt":null,"name":"hades"},{"joinedAt":"2020-02-26T03:12:17.000Z","leftAt":null,"name":"Infected"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381001,"createdAt":"2020-02-26T03:10:14.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Standard","mapVariantCategory":"Survival","lobbyTitle":null,"hostName":"Tayah","slotsHumansTotal":10,"slotsHumansTaken":6,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":1085,"headerHash":null,"documentHash":null,"iconHash":"55364d1afae9de4a43b596a083729a11f41b329f941483c1f124a9f7bbbba15c","document":{"bnetId":280165,"type":"map","name":"Kerrigan Survival 2"}},"players":[{"joinedAt":"2020-02-26T03:10:14.000Z","leftAt":null,"name":"Tayah"},{"joinedAt":"2020-02-26T03:10:16.000Z","leftAt":null,"name":"cypher"},{"joinedAt":"2020-02-26T03:10:41.000Z","leftAt":null,"name":"Carr"},{"joinedAt":"2020-02-26T03:12:56.000Z","leftAt":null,"name":"aleassins"},{"joinedAt":"2020-02-26T03:12:56.000Z","leftAt":null,"name":"WhiteCat"},{"joinedAt":"2020-02-26T03:13:49.000Z","leftAt":null,"name":"RuN"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381015,"createdAt":"2020-02-26T03:10:15.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Custom","mapVariantCategory":"Other","lobbyTitle":null,"hostName":"Joboxr","slotsHumansTotal":15,"slotsHumansTaken":4,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":1259,"headerHash":null,"documentHash":null,"iconHash":"30ba3168b608503246a29aa45d751146a420d2bacf2e199070198232bf8961ea","document":{"bnetId":100184,"type":"map","name":"-Mafia-"}},"players":[{"joinedAt":"2020-02-26T03:10:15.000Z","leftAt":null,"name":"Joboxr"},{"joinedAt":"2020-02-26T03:10:42.000Z","leftAt":"2020-02-26T03:13:30.000Z","name":"Lutheen"},{"joinedAt":"2020-02-26T03:10:42.000Z","leftAt":null,"name":"Omicron"},{"joinedAt":"2020-02-26T03:10:42.000Z","leftAt":null,"name":"WillSmith"},{"joinedAt":"2020-02-26T03:12:32.000Z","leftAt":null,"name":"ComputerAI"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381023,"createdAt":"2020-02-26T03:10:23.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Survival","mapVariantCategory":"Other","lobbyTitle":null,"hostName":"DarkKing","slotsHumansTotal":11,"slotsHumansTaken":8,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":2,"headerHash":null,"documentHash":null,"iconHash":"6ac90a1f95eb0dd520e806e4ff24023c5f1a81825cc1d9a91d3cd76fbee733cf","document":{"bnetId":316720,"type":"map","name":"Eras Zombie Invasion (NA) PT"}},"players":[{"joinedAt":"2020-02-26T03:10:23.000Z","leftAt":null,"name":"DarkKing"},{"joinedAt":"2020-02-26T03:11:17.000Z","leftAt":null,"name":"AuricDrobble"},{"joinedAt":"2020-02-26T03:11:43.000Z","leftAt":"2020-02-26T03:13:37.000Z","name":"niranoo"},{"joinedAt":"2020-02-26T03:12:10.000Z","leftAt":null,"name":"dragster"},{"joinedAt":"2020-02-26T03:12:10.000Z","leftAt":null,"name":"MMM"},{"joinedAt":"2020-02-26T03:12:10.000Z","leftAt":null,"name":"Tormidal"},{"joinedAt":"2020-02-26T03:13:12.000Z","leftAt":null,"name":"SilentRADAR"},{"joinedAt":"2020-02-26T03:13:12.000Z","leftAt":null,"name":"Triton"},{"joinedAt":"2020-02-26T03:13:37.000Z","leftAt":null,"name":"BobbyBobs"}]},{"bnetBucketId":1574802246,"bnetRecordId":11072959,"createdAt":"2020-02-26T03:10:45.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"협동모드","mapVariantCategory":"Survival","lobbyTitle":null,"hostName":"채민이담당일찐","slotsHumansTotal":6,"slotsHumansTaken":6,"region":{"code":"KR","name":""},"mapDocumentVersion":{"majorVersion":0,"minorVersion":33,"headerHash":null,"documentHash":null,"iconHash":"b8ae68249c40fab71a3b85e89a821c1b2d6812748b6013c6f40b939612311d27","document":{"bnetId":133159,"type":"map","name":"생존왕 - 무인도"}},"players":[{"joinedAt":"2020-02-26T03:10:45.000Z","leftAt":null,"name":"채민이담당일찐"},{"joinedAt":"2020-02-26T03:10:46.000Z","leftAt":null,"name":"기린울음소리두릅"},{"joinedAt":"2020-02-26T03:12:16.000Z","leftAt":null,"name":"시형"},{"joinedAt":"2020-02-26T03:13:01.000Z","leftAt":null,"name":"그냥커피"},{"joinedAt":"2020-02-26T03:13:31.000Z","leftAt":null,"name":"악당세균맨"},{"joinedAt":"2020-02-26T03:13:31.000Z","leftAt":null,"name":"여왕충"}]},{"bnetBucketId":1574802246,"bnetRecordId":11072957,"createdAt":"2020-02-26T03:10:45.000Z","closedAt":null,"status":"open","mapVariantIndex":1,"mapVariantMode":"Standard","mapVariantCategory":"Strategy","lobbyTitle":"워크 땅따먹기","hostName":"IIIlllIIIllI","slotsHumansTotal":7,"slotsHumansTaken":2,"region":{"code":"KR","name":""},"mapDocumentVersion":{"majorVersion":0,"minorVersion":37,"headerHash":null,"documentHash":null,"iconHash":"d6d13b1b335d334082d455ba39142ce10de961ff364521f8c8af7cd2194c1f14","document":{"bnetId":100290,"type":"map","name":"Lordaeron Conquest"}},"players":[{"joinedAt":"2020-02-26T03:10:45.000Z","leftAt":null,"name":"IIIlllIIIllI"},{"joinedAt":"2020-02-26T03:12:43.000Z","leftAt":null,"name":"kerocero"}]},{"bnetBucketId":1574802246,"bnetRecordId":11072607,"createdAt":"2020-02-26T03:10:55.000Z","closedAt":null,"status":"open","mapVariantIndex":1,"mapVariantMode":"난이도: 보통","mapVariantCategory":"Survival","lobbyTitle":"12시협동","hostName":"배틀그라운드","slotsHumansTotal":4,"slotsHumansTaken":3,"region":{"code":"KR","name":""},"mapDocumentVersion":{"majorVersion":2,"minorVersion":110,"headerHash":null,"documentHash":null,"iconHash":"aeb1ea4281e3f96f3671af0ffc12fb3f32f8127908d0c5fb0e3033785458096d","document":{"bnetId":101446,"type":"map","name":"극한 벽짓고 살아남기 Remaster"}},"players":[{"joinedAt":"2020-02-26T03:10:55.000Z","leftAt":null,"name":"배틀그라운드"},{"joinedAt":"2020-02-26T03:13:04.000Z","leftAt":null,"name":"괴물꺽기"},{"joinedAt":"2020-02-26T03:13:23.000Z","leftAt":null,"name":"새마을호"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381142,"createdAt":"2020-02-26T03:10:56.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Team vs Team","mapVariantCategory":"Tower Defense","lobbyTitle":null,"hostName":"Belmont","slotsHumansTotal":8,"slotsHumansTaken":2,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":0,"minorVersion":467,"headerHash":null,"documentHash":null,"iconHash":"134cd2d7432516e610e23f8356fc9c404f77de0d6fbd10830d985a017b93ca1d","document":{"bnetId":223843,"type":"map","name":"Mines and Magic"}},"players":[{"joinedAt":"2020-02-26T03:10:56.000Z","leftAt":null,"name":"Belmont"},{"joinedAt":"2020-02-26T03:13:15.000Z","leftAt":null,"name":"KevmanX"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381180,"createdAt":"2020-02-26T03:10:56.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"4V4","mapVariantCategory":"Tug Of War","lobbyTitle":"","hostName":"Dospostmann","slotsHumansTotal":8,"slotsHumansTaken":2,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":3,"minorVersion":22,"headerHash":null,"documentHash":null,"iconHash":"0844050761c26bf567c1e54cd9b5acb38ec50db841ea191d0ae06bebbdf7b4b0","document":{"bnetId":155,"type":"map","name":"Nexus Wars"}},"players":[{"joinedAt":"2020-02-26T03:10:56.000Z","leftAt":null,"name":"Dospostmann"},{"joinedAt":"2020-02-26T03:10:57.000Z","leftAt":null,"name":"PCPrincipal"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381179,"createdAt":"2020-02-26T03:10:56.000Z","closedAt":null,"status":"open","mapVariantIndex":1,"mapVariantMode":"Annihilation","mapVariantCategory":"Other","lobbyTitle":null,"hostName":"THEBOZZ","slotsHumansTotal":4,"slotsHumansTaken":2,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":0,"minorVersion":30,"headerHash":null,"documentHash":null,"iconHash":"69fbf8669e175ccbce9e82b5435e324fa86cf4768662ef4a70c4e69025316e5f","document":{"bnetId":315855,"type":"map","name":"Annihilation Special Forces"}},"players":[{"joinedAt":"2020-02-26T03:10:56.000Z","leftAt":null,"name":"THEBOZZ"},{"joinedAt":"2020-02-26T03:11:48.000Z","leftAt":null,"name":"WyvernZed"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381196,"createdAt":"2020-02-26T03:11:04.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"4v5","mapVariantCategory":"Strategy","lobbyTitle":null,"hostName":"blade","slotsHumansTotal":9,"slotsHumansTaken":1,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":3,"minorVersion":27,"headerHash":null,"documentHash":null,"iconHash":"4d1894a0c55eee5ea282f9c9c2cd4f40a3f2f4c9f39293672e4e54950785991e","document":{"bnetId":281535,"type":"map","name":"Risk: World War 1"}},"players":[{"joinedAt":"2020-02-26T03:11:04.000Z","leftAt":null,"name":"blade"},{"joinedAt":"2020-02-26T03:11:34.000Z","leftAt":"2020-02-26T03:11:57.000Z","name":"Force"}]},{"bnetBucketId":1574802246,"bnetRecordId":11072993,"createdAt":"2020-02-26T03:11:14.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"최저가 컨트롤","mapVariantCategory":"Other","lobbyTitle":null,"hostName":"스타좀잘함","slotsHumansTotal":6,"slotsHumansTaken":5,"region":{"code":"KR","name":""},"mapDocumentVersion":{"majorVersion":2,"minorVersion":60,"headerHash":null,"documentHash":null,"iconHash":"41732ad0008b6fd587a7faa9503e32b4b9317024fd8949b43378fe94716a0505","document":{"bnetId":90289,"type":"map","name":"최저가 컨트롤"}},"players":[{"joinedAt":"2020-02-26T03:11:14.000Z","leftAt":null,"name":"스타좀잘함"},{"joinedAt":"2020-02-26T03:11:42.000Z","leftAt":null,"name":"투지"},{"joinedAt":"2020-02-26T03:11:42.000Z","leftAt":null,"name":"귀요미"},{"joinedAt":"2020-02-26T03:12:54.000Z","leftAt":null,"name":"치즈케잌"},{"joinedAt":"2020-02-26T03:13:27.000Z","leftAt":null,"name":"석원앱"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381235,"createdAt":"2020-02-26T03:11:25.000Z","closedAt":null,"status":"open","mapVariantIndex":4,"mapVariantMode":"S1 Prestige","mapVariantCategory":"Survival","lobbyTitle":"90+ prestige","hostName":"Dantalion","slotsHumansTotal":4,"slotsHumansTaken":3,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":12,"minorVersion":6,"headerHash":null,"documentHash":null,"iconHash":"b2b1fe163a0cab52fc80ad26cd984000091e25a6a587891ea036e3e922252d0b","document":{"bnetId":263158,"type":"map","name":"CP2 Official"}},"players":[{"joinedAt":"2020-02-26T03:11:25.000Z","leftAt":null,"name":"Dantalion"},{"joinedAt":"2020-02-26T03:11:28.000Z","leftAt":null,"name":"GradVic"},{"joinedAt":"2020-02-26T03:12:44.000Z","leftAt":null,"name":"Skyfunn"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381241,"createdAt":"2020-02-26T03:11:25.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Custom","mapVariantCategory":"Tower Defense","lobbyTitle":"","hostName":"FrancoKiller","slotsHumansTotal":8,"slotsHumansTaken":1,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":30,"headerHash":null,"documentHash":null,"iconHash":"3505eff17b840ca89e0b65c38152fa705293a6b54cb387eec3daae7a1593215f","document":{"bnetId":291597,"type":"map","name":"Line Tower Wars: Re-Engineered"}},"players":[{"joinedAt":"2020-02-26T03:11:25.000Z","leftAt":null,"name":"FrancoKiller"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381269,"createdAt":"2020-02-26T03:11:25.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Survival","mapVariantCategory":"Survival","lobbyTitle":null,"hostName":"RDUBIOUS","slotsHumansTotal":6,"slotsHumansTaken":4,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":0,"minorVersion":269,"headerHash":null,"documentHash":null,"iconHash":"62bc935afcb30c413e79eb1abbc7747f83b7b05c9e5139c5f1cc14f35022cef3","document":{"bnetId":293070,"type":"map","name":"Zombie World: Unity test"}},"players":[{"joinedAt":"2020-02-26T03:11:25.000Z","leftAt":null,"name":"RDUBIOUS"},{"joinedAt":"2020-02-26T03:12:19.000Z","leftAt":null,"name":"Nyala"},{"joinedAt":"2020-02-26T03:13:18.000Z","leftAt":null,"name":"PopSkicle"},{"joinedAt":"2020-02-26T03:13:18.000Z","leftAt":null,"name":"Psionic"}]},{"bnetBucketId":1574802246,"bnetRecordId":11073025,"createdAt":"2020-02-26T03:11:36.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"3v3","mapVariantCategory":"Tug Of War","lobbyTitle":null,"hostName":"치킨한쌈","slotsHumansTotal":6,"slotsHumansTaken":2,"region":{"code":"KR","name":""},"mapDocumentVersion":{"majorVersion":6,"minorVersion":203,"headerHash":null,"documentHash":null,"iconHash":"f765555f91464e07392366dd43ae9758e791b85686312ac753c13599ed81908e","document":{"bnetId":64155,"type":"map","name":"데저트 스트라이크2"}},"players":[{"joinedAt":"2020-02-26T03:11:36.000Z","leftAt":"2020-02-26T03:13:13.000Z","name":"Circle"},{"joinedAt":"2020-02-26T03:11:37.000Z","leftAt":null,"name":"치킨한쌈"},{"joinedAt":"2020-02-26T03:12:35.000Z","leftAt":null,"name":"만슈타인"}]},{"bnetBucketId":1574802246,"bnetRecordId":11073029,"createdAt":"2020-02-26T03:11:45.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Standard","mapVariantCategory":"Other","lobbyTitle":"운빨망겜","hostName":"blackhabits","slotsHumansTotal":8,"slotsHumansTaken":4,"region":{"code":"KR","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":274,"headerHash":null,"documentHash":null,"iconHash":"79c3b3a3d469f386aab6250bb6afb69c5a97340ebfc3a1738b08a4dd3407cea3","document":{"bnetId":133827,"type":"map","name":"스타 체스"}},"players":[{"joinedAt":"2020-02-26T03:11:45.000Z","leftAt":null,"name":"blackhabits"},{"joinedAt":"2020-02-26T03:11:57.000Z","leftAt":null,"name":"goodluck"},{"joinedAt":"2020-02-26T03:11:57.000Z","leftAt":null,"name":"twotime"},{"joinedAt":"2020-02-26T03:12:22.000Z","leftAt":null,"name":"서린비"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381306,"createdAt":"2020-02-26T03:11:45.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Version 8 - 3v3","mapVariantCategory":"Tug Of War","lobbyTitle":"","hostName":"mikeeee","slotsHumansTotal":6,"slotsHumansTaken":1,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":8,"minorVersion":0,"headerHash":null,"documentHash":null,"iconHash":"a968e9d4188bd5b0ee9e925a4cd3c1591277cb09bf6b0c85571176d363ecdab6","document":{"bnetId":121886,"type":"map","name":"Income Wars - official"}},"players":[{"joinedAt":"2020-02-26T03:11:45.000Z","leftAt":null,"name":"mikeeee"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381312,"createdAt":"2020-02-26T03:11:45.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Bunker Wars","mapVariantCategory":"Arena","lobbyTitle":null,"hostName":"apocalypse","slotsHumansTotal":12,"slotsHumansTaken":2,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":3,"minorVersion":103,"headerHash":null,"documentHash":null,"iconHash":"52387d2b35ab4b701797cf0382cf322cfb4b6fa7e6d993ad662826f9ec9026ea","document":{"bnetId":265415,"type":"map","name":"Bunker Wars X 3.0"}},"players":[{"joinedAt":"2020-02-26T03:11:45.000Z","leftAt":null,"name":"apocalypse"},{"joinedAt":"2020-02-26T03:12:39.000Z","leftAt":"2020-02-26T03:13:14.000Z","name":"Daedalus"},{"joinedAt":"2020-02-26T03:13:39.000Z","leftAt":null,"name":"strapcraper"}]},{"bnetBucketId":1574816994,"bnetRecordId":16832278,"createdAt":"2020-02-26T03:11:51.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"3V3","mapVariantCategory":"Tug Of War","lobbyTitle":null,"hostName":"MaxISBack","slotsHumansTotal":6,"slotsHumansTaken":4,"region":{"code":"EU","name":""},"mapDocumentVersion":{"majorVersion":2,"minorVersion":59,"headerHash":null,"documentHash":null,"iconHash":"db1f21cc0ba788acf7bfd69f93f80fc2bc583369ae5a69cce3c85ae928e70def","document":{"bnetId":140436,"type":"map","name":"Direct Strike"}},"players":[{"joinedAt":"2020-02-26T03:11:51.000Z","leftAt":null,"name":"MaxISBack"},{"joinedAt":"2020-02-26T03:12:31.000Z","leftAt":null,"name":"Adamantian"},{"joinedAt":"2020-02-26T03:12:59.000Z","leftAt":"2020-02-26T03:13:20.000Z","name":"Adamzgi"},{"joinedAt":"2020-02-26T03:13:22.000Z","leftAt":null,"name":"TeSTeT"},{"joinedAt":"2020-02-26T03:13:44.000Z","leftAt":null,"name":"YarovoyYusko"}]},{"bnetBucketId":1574802246,"bnetRecordId":11073023,"createdAt":"2020-02-26T03:11:53.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Ori : Normal","mapVariantCategory":"Other","lobbyTitle":"광전사 가랜","hostName":"막강한두더지","slotsHumansTotal":6,"slotsHumansTaken":3,"region":{"code":"KR","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":185,"headerHash":null,"documentHash":null,"iconHash":"c0d3021b9ce9633ae0e0af397c19d696b0fbb9d88c1245c7ea70759193d2aaf2","document":{"bnetId":91573,"type":"map","name":"광전사막기"}},"players":[{"joinedAt":"2020-02-26T03:11:53.000Z","leftAt":null,"name":"막강한두더지"},{"joinedAt":"2020-02-26T03:12:06.000Z","leftAt":null,"name":"kyon"},{"joinedAt":"2020-02-26T03:12:18.000Z","leftAt":"2020-02-26T03:12:40.000Z","name":"사람인"},{"joinedAt":"2020-02-26T03:12:29.000Z","leftAt":null,"name":"보오올지"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381335,"createdAt":"2020-02-26T03:11:53.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"3x Select","mapVariantCategory":"Tower Defense","lobbyTitle":null,"hostName":"Chapolin","slotsHumansTotal":8,"slotsHumansTaken":7,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":8,"minorVersion":9,"headerHash":null,"documentHash":null,"iconHash":"b5ac77f95f6fcb98aac8dd3ff188bd6344f589f88613ce1845b7ae4605c471ad","document":{"bnetId":251428,"type":"map","name":"Squadron TD"}},"players":[{"joinedAt":"2020-02-26T03:11:53.000Z","leftAt":null,"name":"Chapolin"},{"joinedAt":"2020-02-26T03:11:55.000Z","leftAt":null,"name":"Deskor"},{"joinedAt":"2020-02-26T03:11:55.000Z","leftAt":null,"name":"Phrantixs"},{"joinedAt":"2020-02-26T03:11:55.000Z","leftAt":null,"name":"SlowNSteady"},{"joinedAt":"2020-02-26T03:12:23.000Z","leftAt":null,"name":"Titian"},{"joinedAt":"2020-02-26T03:12:23.000Z","leftAt":null,"name":"Brisingr"},{"joinedAt":"2020-02-26T03:12:50.000Z","leftAt":null,"name":"Dalturo"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381367,"createdAt":"2020-02-26T03:12:06.000Z","closedAt":null,"status":"open","mapVariantIndex":2,"mapVariantMode":"3V3","mapVariantCategory":"Melee","lobbyTitle":null,"hostName":"WoodytheOG","slotsHumansTotal":6,"slotsHumansTaken":2,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":0,"headerHash":null,"documentHash":null,"iconHash":"da08dbfd7ad3ef547282393414733e85f8b918b7b449dfdc7cd389dcebe70efc","document":{"bnetId":205609,"type":"map","name":"[Official] Fastest Possible Map"}},"players":[{"joinedAt":"2020-02-26T03:12:06.000Z","leftAt":null,"name":"WoodytheOG"},{"joinedAt":"2020-02-26T03:13:11.000Z","leftAt":null,"name":"SERGIONIDAS"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381419,"createdAt":"2020-02-26T03:12:14.000Z","closedAt":null,"status":"open","mapVariantIndex":1,"mapVariantMode":"3V3 Commanders","mapVariantCategory":"Tug Of War","lobbyTitle":null,"hostName":"Mediocrates","slotsHumansTotal":6,"slotsHumansTaken":6,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":2,"minorVersion":56,"headerHash":null,"documentHash":null,"iconHash":"db1f21cc0ba788acf7bfd69f93f80fc2bc583369ae5a69cce3c85ae928e70def","document":{"bnetId":208271,"type":"map","name":"Direct Strike"}},"players":[{"joinedAt":"2020-02-26T03:12:14.000Z","leftAt":null,"name":"Mediocrates"},{"joinedAt":"2020-02-26T03:13:15.000Z","leftAt":null,"name":"Dax"},{"joinedAt":"2020-02-26T03:13:15.000Z","leftAt":null,"name":"RamenNoodleS"},{"joinedAt":"2020-02-26T03:13:33.000Z","leftAt":null,"name":"fusion"},{"joinedAt":"2020-02-26T03:13:33.000Z","leftAt":null,"name":"HunterKiller"},{"joinedAt":"2020-02-26T03:13:33.000Z","leftAt":null,"name":"Professional"}]},{"bnetBucketId":1574802246,"bnetRecordId":11073057,"createdAt":"2020-02-26T03:12:15.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Standard","mapVariantCategory":"Other","lobbyTitle":"","hostName":"뵈뵈","slotsHumansTotal":8,"slotsHumansTaken":1,"region":{"code":"KR","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":274,"headerHash":null,"documentHash":null,"iconHash":"79c3b3a3d469f386aab6250bb6afb69c5a97340ebfc3a1738b08a4dd3407cea3","document":{"bnetId":133827,"type":"map","name":"스타 체스"}},"players":[{"joinedAt":"2020-02-26T03:12:15.000Z","leftAt":null,"name":"뵈뵈"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381469,"createdAt":"2020-02-26T03:12:25.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Standard","mapVariantCategory":"Strategy","lobbyTitle":null,"hostName":"GigaTron","slotsHumansTotal":8,"slotsHumansTaken":2,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":2,"minorVersion":212,"headerHash":null,"documentHash":null,"iconHash":"a6c67226fc4a9423378d7fb6c48aed58f0eab0a149be9cc37ebd1a5755f1d451","document":{"bnetId":305679,"type":"map","name":"Zone Control CE"}},"players":[{"joinedAt":"2020-02-26T03:12:25.000Z","leftAt":null,"name":"GigaTron"},{"joinedAt":"2020-02-26T03:12:51.000Z","leftAt":"2020-02-26T03:13:45.000Z","name":"Kingswitness"},{"joinedAt":"2020-02-26T03:13:45.000Z","leftAt":null,"name":"Neves"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381434,"createdAt":"2020-02-26T03:12:26.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"PeepMode","mapVariantCategory":"Other","lobbyTitle":"","hostName":"KinG","slotsHumansTotal":10,"slotsHumansTaken":1,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":0,"minorVersion":2,"headerHash":null,"documentHash":null,"iconHash":"93f120d21bc7e2bc2f28405289dfe27ae1da10d412f465442255e918474e4109","document":{"bnetId":312656,"type":"map","name":"PeepMode Triton LE"}},"players":[{"joinedAt":"2020-02-26T03:12:26.000Z","leftAt":null,"name":"KinG"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381421,"createdAt":"2020-02-26T03:12:26.000Z","closedAt":null,"status":"open","mapVariantIndex":1,"mapVariantMode":"3V3 Commanders","mapVariantCategory":"Tug Of War","lobbyTitle":"3v3 COMMANDERS","hostName":"REAPER","slotsHumansTotal":6,"slotsHumansTaken":2,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":2,"minorVersion":56,"headerHash":null,"documentHash":null,"iconHash":"db1f21cc0ba788acf7bfd69f93f80fc2bc583369ae5a69cce3c85ae928e70def","document":{"bnetId":208271,"type":"map","name":"Direct Strike"}},"players":[{"joinedAt":"2020-02-26T03:12:26.000Z","leftAt":"2020-02-26T03:13:23.000Z","name":"HunterKiller"},{"joinedAt":"2020-02-26T03:13:23.000Z","leftAt":null,"name":"REAPER"},{"joinedAt":"2020-02-26T03:13:23.000Z","leftAt":null,"name":"CorvusCorax"},{"joinedAt":"2020-02-26T03:13:46.000Z","leftAt":null,"name":"Venom"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381412,"createdAt":"2020-02-26T03:12:26.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Standard","mapVariantCategory":"Hero Battle","lobbyTitle":"FFA from ....","hostName":"Rock","slotsHumansTotal":12,"slotsHumansTaken":5,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":69,"headerHash":null,"documentHash":null,"iconHash":"d75af9e51297914ab61da38610b5f72fe6840b635a5a29fa2e2c6e083ce4279b","document":{"bnetId":293068,"type":"map","name":"Star Battle Omega"}},"players":[{"joinedAt":"2020-02-26T03:12:26.000Z","leftAt":null,"name":"Rock"},{"joinedAt":"2020-02-26T03:12:53.000Z","leftAt":null,"name":"Baz"},{"joinedAt":"2020-02-26T03:12:53.000Z","leftAt":null,"name":"RDawg"},{"joinedAt":"2020-02-26T03:12:53.000Z","leftAt":null,"name":"ZapTaz"},{"joinedAt":"2020-02-26T03:13:24.000Z","leftAt":null,"name":"Shelf"},{"joinedAt":"2020-02-26T03:13:47.000Z","leftAt":null,"name":"CheeseBurger"},{"joinedAt":"2020-02-26T03:13:47.000Z","leftAt":null,"name":"Partizan"},{"joinedAt":"2020-02-26T03:13:47.000Z","leftAt":null,"name":"Strongman"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381471,"createdAt":"2020-02-26T03:12:26.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"4V4","mapVariantCategory":"Tug Of War","lobbyTitle":null,"hostName":"alchemis","slotsHumansTotal":8,"slotsHumansTaken":3,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":0,"minorVersion":6,"headerHash":null,"documentHash":null,"iconHash":"0844050761c26bf567c1e54cd9b5acb38ec50db841ea191d0ae06bebbdf7b4b0","document":{"bnetId":228411,"type":"map","name":"Nexus Wars One Lane"}},"players":[{"joinedAt":"2020-02-26T03:12:26.000Z","leftAt":null,"name":"alchemis"},{"joinedAt":"2020-02-26T03:12:54.000Z","leftAt":null,"name":"Zibsterpl"},{"joinedAt":"2020-02-26T03:13:48.000Z","leftAt":null,"name":"HorneyToad"},{"joinedAt":"2020-02-26T03:13:48.000Z","leftAt":null,"name":"Irish"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381507,"createdAt":"2020-02-26T03:12:43.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Freeform Story","mapVariantCategory":"Other","lobbyTitle":"","hostName":"killaguy","slotsHumansTotal":14,"slotsHumansTaken":1,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":5,"headerHash":null,"documentHash":null,"iconHash":"1d55f2f2521c10936648595e719d840f8802a34af4c689727553e5d84cf89c9e","document":{"bnetId":288937,"type":"map","name":"Apex Roleplay - The Barrens"}},"players":[{"joinedAt":"2020-02-26T03:12:43.000Z","leftAt":null,"name":"killaguy"}]},{"bnetBucketId":1574802246,"bnetRecordId":11073046,"createdAt":"2020-02-26T03:12:44.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Normal mode","mapVariantCategory":"Survival","lobbyTitle":"탈주사절","hostName":"군단을위하여","slotsHumansTotal":7,"slotsHumansTaken":2,"region":{"code":"KR","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":615,"headerHash":null,"documentHash":null,"iconHash":"14c23b0c44563767ad4631fdf3923758ea6ca21bc7311d8e8360b46c59878b3e","document":{"bnetId":118243,"type":"map","name":"Random Base Defender 4+"}},"players":[{"joinedAt":"2020-02-26T03:12:44.000Z","leftAt":null,"name":"군단을위하여"},{"joinedAt":"2020-02-26T03:13:30.000Z","leftAt":null,"name":"미친고수"}]},{"bnetBucketId":1574802246,"bnetRecordId":11073089,"createdAt":"2020-02-26T03:12:44.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Cooperative","mapVariantCategory":"Tower Defense","lobbyTitle":null,"hostName":"짱깨","slotsHumansTotal":8,"slotsHumansTaken":5,"region":{"code":"KR","name":""},"mapDocumentVersion":{"majorVersion":5,"minorVersion":129,"headerHash":null,"documentHash":null,"iconHash":"de31af87966cd8dd33545dd0784d6d6354951ae1266c266c66d00f7b52d63633","document":{"bnetId":82701,"type":"map","name":"세미-온 타워디펜스 2"}},"players":[{"joinedAt":"2020-02-26T03:12:44.000Z","leftAt":null,"name":"짱깨"},{"joinedAt":"2020-02-26T03:13:11.000Z","leftAt":null,"name":"Trendy"},{"joinedAt":"2020-02-26T03:13:11.000Z","leftAt":null,"name":"악령"},{"joinedAt":"2020-02-26T03:13:30.000Z","leftAt":"2020-02-26T03:13:43.000Z","name":"붉은가림판"},{"joinedAt":"2020-02-26T03:13:43.000Z","leftAt":null,"name":"pgb"},{"joinedAt":"2020-02-26T03:13:43.000Z","leftAt":null,"name":"나는야프징징"}]},{"bnetBucketId":1574802246,"bnetRecordId":11073099,"createdAt":"2020-02-26T03:12:56.000Z","closedAt":null,"status":"open","mapVariantIndex":1,"mapVariantMode":"Hard mode","mapVariantCategory":"Survival","lobbyTitle":null,"hostName":"도토리묵","slotsHumansTotal":7,"slotsHumansTaken":4,"region":{"code":"KR","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":615,"headerHash":null,"documentHash":null,"iconHash":"14c23b0c44563767ad4631fdf3923758ea6ca21bc7311d8e8360b46c59878b3e","document":{"bnetId":118243,"type":"map","name":"Random Base Defender 4+"}},"players":[{"joinedAt":"2020-02-26T03:12:56.000Z","leftAt":null,"name":"도토리묵"},{"joinedAt":"2020-02-26T03:13:09.000Z","leftAt":null,"name":"까마귀"},{"joinedAt":"2020-02-26T03:13:28.000Z","leftAt":null,"name":"Lolipop"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381534,"createdAt":"2020-02-26T03:12:57.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"3V3","mapVariantCategory":"Tug Of War","lobbyTitle":null,"hostName":"Boomstick","slotsHumansTotal":6,"slotsHumansTaken":4,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":2,"minorVersion":56,"headerHash":null,"documentHash":null,"iconHash":"db1f21cc0ba788acf7bfd69f93f80fc2bc583369ae5a69cce3c85ae928e70def","document":{"bnetId":208271,"type":"map","name":"Direct Strike"}},"players":[{"joinedAt":"2020-02-26T03:12:57.000Z","leftAt":null,"name":"Boomstick"},{"joinedAt":"2020-02-26T03:12:58.000Z","leftAt":null,"name":"Jimmus"},{"joinedAt":"2020-02-26T03:12:58.000Z","leftAt":null,"name":"RioRodreguez"},{"joinedAt":"2020-02-26T03:12:58.000Z","leftAt":"2020-02-26T03:13:28.000Z","name":"RocketSurgen"},{"joinedAt":"2020-02-26T03:13:28.000Z","leftAt":null,"name":"Aldebarán"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381532,"createdAt":"2020-02-26T03:12:57.000Z","closedAt":null,"status":"open","mapVariantIndex":2,"mapVariantMode":"3x Dynamic","mapVariantCategory":"Tower Defense","lobbyTitle":null,"hostName":"xxKGBxx","slotsHumansTotal":8,"slotsHumansTaken":7,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":8,"minorVersion":9,"headerHash":null,"documentHash":null,"iconHash":"b5ac77f95f6fcb98aac8dd3ff188bd6344f589f88613ce1845b7ae4605c471ad","document":{"bnetId":251428,"type":"map","name":"Squadron TD"}},"players":[{"joinedAt":"2020-02-26T03:12:57.000Z","leftAt":null,"name":"xxKGBxx"},{"joinedAt":"2020-02-26T03:12:58.000Z","leftAt":null,"name":"DanMacko"},{"joinedAt":"2020-02-26T03:13:28.000Z","leftAt":null,"name":"Castino"},{"joinedAt":"2020-02-26T03:13:28.000Z","leftAt":null,"name":"NinjaPoW"},{"joinedAt":"2020-02-26T03:13:28.000Z","leftAt":null,"name":"Wardo"},{"joinedAt":"2020-02-26T03:13:50.000Z","leftAt":null,"name":"Noob"},{"joinedAt":"2020-02-26T03:13:50.000Z","leftAt":null,"name":"Poseidon"},{"joinedAt":"2020-02-26T03:13:50.000Z","leftAt":null,"name":"RichHobo"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381533,"createdAt":"2020-02-26T03:12:57.000Z","closedAt":null,"status":"open","mapVariantIndex":1,"mapVariantMode":"3V3 Commanders","mapVariantCategory":"Tug Of War","lobbyTitle":"","hostName":"YFALucky","slotsHumansTotal":6,"slotsHumansTaken":2,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":2,"minorVersion":56,"headerHash":null,"documentHash":null,"iconHash":"db1f21cc0ba788acf7bfd69f93f80fc2bc583369ae5a69cce3c85ae928e70def","document":{"bnetId":208271,"type":"map","name":"Direct Strike"}},"players":[{"joinedAt":"2020-02-26T03:12:57.000Z","leftAt":null,"name":"YFALucky"},{"joinedAt":"2020-02-26T03:12:58.000Z","leftAt":null,"name":"YFAKUSHKILLA"},{"joinedAt":"2020-02-26T03:13:51.000Z","leftAt":null,"name":"Penguin"},{"joinedAt":"2020-02-26T03:13:51.000Z","leftAt":null,"name":"ramrod"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381428,"createdAt":"2020-02-26T03:12:58.000Z","closedAt":null,"status":"open","mapVariantIndex":3,"mapVariantMode":"3V3","mapVariantCategory":"Melee","lobbyTitle":"ice cliff 3v3","hostName":"Ridley","slotsHumansTotal":6,"slotsHumansTaken":1,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":14,"headerHash":null,"documentHash":null,"iconHash":"6fc171290f50b354d2cf8ca52c2f4e68c1c87675af1d5cbfc4fb301f8bed4b5b","document":{"bnetId":255105,"type":"map","name":"Ice Cliffs"}},"players":[{"joinedAt":"2020-02-26T03:12:58.000Z","leftAt":null,"name":"Ridley"}]},{"bnetBucketId":1574802246,"bnetRecordId":11073105,"createdAt":"2020-02-26T03:13:05.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"아무 방","mapVariantCategory":"Other","lobbyTitle":"상극방","hostName":"드라군","slotsHumansTotal":9,"slotsHumansTaken":3,"region":{"code":"KR","name":""},"mapDocumentVersion":{"majorVersion":2,"minorVersion":24,"headerHash":null,"documentHash":null,"iconHash":"7fadd900fd813270c6a912f63de637980d6ff4a02a9723ffb813b8fba1d90641","document":{"bnetId":131100,"type":"map","name":"RP Quad"}},"players":[{"joinedAt":"2020-02-26T03:13:05.000Z","leftAt":null,"name":"드라군"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381588,"createdAt":"2020-02-26T03:13:07.000Z","closedAt":null,"status":"open","mapVariantIndex":9,"mapVariantMode":"Gear","mapVariantCategory":"Tug Of War","lobbyTitle":"","hostName":"Bonza","slotsHumansTotal":6,"slotsHumansTaken":1,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":2,"minorVersion":56,"headerHash":null,"documentHash":null,"iconHash":"db1f21cc0ba788acf7bfd69f93f80fc2bc583369ae5a69cce3c85ae928e70def","document":{"bnetId":208271,"type":"map","name":"Direct Strike"}},"players":[{"joinedAt":"2020-02-26T03:13:07.000Z","leftAt":null,"name":"Bonza"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381581,"createdAt":"2020-02-26T03:13:07.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"3V3","mapVariantCategory":"Tug Of War","lobbyTitle":null,"hostName":"shakashka","slotsHumansTotal":6,"slotsHumansTaken":3,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":2,"minorVersion":56,"headerHash":null,"documentHash":null,"iconHash":"db1f21cc0ba788acf7bfd69f93f80fc2bc583369ae5a69cce3c85ae928e70def","document":{"bnetId":208271,"type":"map","name":"Direct Strike"}},"players":[{"joinedAt":"2020-02-26T03:13:07.000Z","leftAt":null,"name":"shakashka"},{"joinedAt":"2020-02-26T03:13:10.000Z","leftAt":null,"name":"DaronTBaron"},{"joinedAt":"2020-02-26T03:13:10.000Z","leftAt":null,"name":"ÞøsTScript"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381472,"createdAt":"2020-02-26T03:13:07.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"3V3","mapVariantCategory":"Tug Of War","lobbyTitle":null,"hostName":"tchnbhtz","slotsHumansTotal":6,"slotsHumansTaken":4,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":2,"minorVersion":56,"headerHash":null,"documentHash":null,"iconHash":"db1f21cc0ba788acf7bfd69f93f80fc2bc583369ae5a69cce3c85ae928e70def","document":{"bnetId":208271,"type":"map","name":"Direct Strike"}},"players":[{"joinedAt":"2020-02-26T03:13:07.000Z","leftAt":null,"name":"tchnbhtz"},{"joinedAt":"2020-02-26T03:13:10.000Z","leftAt":null,"name":"Killerfox"},{"joinedAt":"2020-02-26T03:13:10.000Z","leftAt":null,"name":"RocketSurgen"},{"joinedAt":"2020-02-26T03:13:10.000Z","leftAt":null,"name":"xiaoyu"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381584,"createdAt":"2020-02-26T03:13:07.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Mineralz Evolution","mapVariantCategory":"Survival","lobbyTitle":"","hostName":"Beave","slotsHumansTotal":8,"slotsHumansTaken":1,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":0,"minorVersion":124,"headerHash":null,"documentHash":null,"iconHash":"c58640139d53ca57b91b32e6303f9f9054444247df0891f4e75b83386b748fd5","document":{"bnetId":147118,"type":"map","name":"-Mineralz Evolution-"}},"players":[{"joinedAt":"2020-02-26T03:13:07.000Z","leftAt":null,"name":"Beave"}]},{"bnetBucketId":1574802246,"bnetRecordId":11073113,"createdAt":"2020-02-26T03:13:14.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Team LC","mapVariantCategory":"Other","lobbyTitle":"","hostName":"unchanged","slotsHumansTotal":6,"slotsHumansTaken":1,"region":{"code":"KR","name":""},"mapDocumentVersion":{"majorVersion":3,"minorVersion":256,"headerHash":null,"documentHash":null,"iconHash":"fcc8649b0a992f439b65def3570b451098c57e62cedabe9f51dc304899a2adab","document":{"bnetId":38391,"type":"map","name":"신전부수기 - 프로게이대전"}},"players":[{"joinedAt":"2020-02-26T03:13:14.000Z","leftAt":null,"name":"unchanged"}]},{"bnetBucketId":1574802246,"bnetRecordId":11073119,"createdAt":"2020-02-26T03:13:14.000Z","closedAt":null,"status":"open","mapVariantIndex":1,"mapVariantMode":"Hard mode","mapVariantCategory":"Survival","lobbyTitle":null,"hostName":"스카페이트","slotsHumansTotal":7,"slotsHumansTaken":3,"region":{"code":"KR","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":615,"headerHash":null,"documentHash":null,"iconHash":"14c23b0c44563767ad4631fdf3923758ea6ca21bc7311d8e8360b46c59878b3e","document":{"bnetId":118243,"type":"map","name":"Random Base Defender 4+"}},"players":[{"joinedAt":"2020-02-26T03:13:14.000Z","leftAt":null,"name":"스카페이트"},{"joinedAt":"2020-02-26T03:13:20.000Z","leftAt":null,"name":"우꾸에이"},{"joinedAt":"2020-02-26T03:13:33.000Z","leftAt":null,"name":"공허"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381615,"createdAt":"2020-02-26T03:13:15.000Z","closedAt":null,"status":"open","mapVariantIndex":3,"mapVariantMode":"2V2 Commanders","mapVariantCategory":"Tug Of War","lobbyTitle":null,"hostName":"SpeCiaList","slotsHumansTotal":4,"slotsHumansTaken":2,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":2,"minorVersion":56,"headerHash":null,"documentHash":null,"iconHash":"db1f21cc0ba788acf7bfd69f93f80fc2bc583369ae5a69cce3c85ae928e70def","document":{"bnetId":208271,"type":"map","name":"Direct Strike"}},"players":[{"joinedAt":"2020-02-26T03:13:15.000Z","leftAt":null,"name":"SpeCiaList"},{"joinedAt":"2020-02-26T03:13:40.000Z","leftAt":null,"name":"RaiN"},{"joinedAt":"2020-02-26T03:13:40.000Z","leftAt":null,"name":"Oni"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381623,"createdAt":"2020-02-26T03:13:15.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"3V3","mapVariantCategory":"Tug Of War","lobbyTitle":null,"hostName":"totoro","slotsHumansTotal":6,"slotsHumansTaken":3,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":125,"headerHash":null,"documentHash":null,"iconHash":"14e2aab6da28046f38a88b6a3cf373daef594b5062aa493751327b71c9c52277","document":{"bnetId":272469,"type":"map","name":"Desert Strike Legacy (Official)"}},"players":[{"joinedAt":"2020-02-26T03:13:15.000Z","leftAt":null,"name":"totoro"},{"joinedAt":"2020-02-26T03:13:41.000Z","leftAt":null,"name":"bMON"},{"joinedAt":"2020-02-26T03:13:41.000Z","leftAt":null,"name":"samhyun"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381479,"createdAt":"2020-02-26T03:13:16.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"4v4 Monobattle","mapVariantCategory":"Other","lobbyTitle":"","hostName":"IHateZerg","slotsHumansTotal":8,"slotsHumansTaken":1,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":77,"headerHash":null,"documentHash":null,"iconHash":"f505e36560ade61e40012d38e628c29ded52dbf93cac67620c3bc19ccf193029","document":{"bnetId":276566,"type":"map","name":"Monobattle LotV - Map Rotation"}},"players":[{"joinedAt":"2020-02-26T03:13:16.000Z","leftAt":null,"name":"IHateZerg"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381620,"createdAt":"2020-02-26T03:13:16.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"Normal","mapVariantCategory":"Survival","lobbyTitle":null,"hostName":"Illuminati","slotsHumansTotal":8,"slotsHumansTaken":2,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":3,"minorVersion":30,"headerHash":null,"documentHash":null,"iconHash":"81fddefd0e199c3f57cbdd3fd4a408b11afcc2c92809863384b4d84a883cc79b","document":{"bnetId":286631,"type":"map","name":"Zerg Hex"}},"players":[{"joinedAt":"2020-02-26T03:13:16.000Z","leftAt":null,"name":"Illuminati"},{"joinedAt":"2020-02-26T03:13:42.000Z","leftAt":null,"name":"Hoopstar"}]},{"bnetBucketId":1574816994,"bnetRecordId":16832317,"createdAt":"2020-02-26T03:13:20.000Z","closedAt":null,"status":"open","mapVariantIndex":1,"mapVariantMode":"3V3 Commanders","mapVariantCategory":"Tug Of War","lobbyTitle":null,"hostName":"MonTBlanc","slotsHumansTotal":6,"slotsHumansTaken":2,"region":{"code":"EU","name":""},"mapDocumentVersion":{"majorVersion":2,"minorVersion":59,"headerHash":null,"documentHash":null,"iconHash":"db1f21cc0ba788acf7bfd69f93f80fc2bc583369ae5a69cce3c85ae928e70def","document":{"bnetId":140436,"type":"map","name":"Direct Strike"}},"players":[{"joinedAt":"2020-02-26T03:13:20.000Z","leftAt":null,"name":"MonTBlanc"},{"joinedAt":"2020-02-26T03:13:29.000Z","leftAt":null,"name":"Selemon"}]},{"bnetBucketId":1574802246,"bnetRecordId":11073128,"createdAt":"2020-02-26T03:13:24.000Z","closedAt":null,"status":"open","mapVariantIndex":5,"mapVariantMode":"live 5 Hp500%(Hel)","mapVariantCategory":"Tower Defense","lobbyTitle":null,"hostName":"Pessive","slotsHumansTotal":8,"slotsHumansTaken":5,"region":{"code":"KR","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":38,"headerHash":null,"documentHash":null,"iconHash":"da14a6d5ca78eaac143bb8aa381c244c989d6144fb4b100e1b9f5f0def62e441","document":{"bnetId":120973,"type":"map","name":"Random Tower Defense Race mode"}},"players":[{"joinedAt":"2020-02-26T03:13:24.000Z","leftAt":null,"name":"Pessive"},{"joinedAt":"2020-02-26T03:13:25.000Z","leftAt":null,"name":"그레이트모스"},{"joinedAt":"2020-02-26T03:13:37.000Z","leftAt":null,"name":"딤섬"},{"joinedAt":"2020-02-26T03:13:37.000Z","leftAt":null,"name":"티그리스"},{"joinedAt":"2020-02-26T03:13:37.000Z","leftAt":null,"name":"팀탐"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381627,"createdAt":"2020-02-26T03:13:25.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"3V3","mapVariantCategory":"Tug Of War","lobbyTitle":"","hostName":"TheRedDevil","slotsHumansTotal":6,"slotsHumansTaken":1,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":2,"minorVersion":56,"headerHash":null,"documentHash":null,"iconHash":"db1f21cc0ba788acf7bfd69f93f80fc2bc583369ae5a69cce3c85ae928e70def","document":{"bnetId":208271,"type":"map","name":"Direct Strike"}},"players":[{"joinedAt":"2020-02-26T03:13:25.000Z","leftAt":null,"name":"TheRedDevil"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381600,"createdAt":"2020-02-26T03:13:25.000Z","closedAt":null,"status":"open","mapVariantIndex":3,"mapVariantMode":"1v1","mapVariantCategory":"Tug Of War","lobbyTitle":"Nexus One Lane 1v1 BRING IT","hostName":"Medic","slotsHumansTotal":2,"slotsHumansTaken":1,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":0,"minorVersion":6,"headerHash":null,"documentHash":null,"iconHash":"0844050761c26bf567c1e54cd9b5acb38ec50db841ea191d0ae06bebbdf7b4b0","document":{"bnetId":228411,"type":"map","name":"Nexus Wars One Lane"}},"players":[{"joinedAt":"2020-02-26T03:13:25.000Z","leftAt":null,"name":"Medic"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381692,"createdAt":"2020-02-26T03:13:33.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"LotR","mapVariantCategory":"Other","lobbyTitle":null,"hostName":"FNThrifty","slotsHumansTotal":7,"slotsHumansTaken":5,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":2,"minorVersion":12,"headerHash":null,"documentHash":null,"iconHash":"299e079db77c4c8655c1f882f201aaee4fcf95fde39a34980d41d1e9bf077f8f","document":{"bnetId":305219,"type":"map","name":"Middle Earth - Rise of the Witch King"}},"players":[{"joinedAt":"2020-02-26T03:13:33.000Z","leftAt":null,"name":"FNThrifty"},{"joinedAt":"2020-02-26T03:13:35.000Z","leftAt":null,"name":"Horus"},{"joinedAt":"2020-02-26T03:13:35.000Z","leftAt":null,"name":"LazyTurtle"},{"joinedAt":"2020-02-26T03:13:35.000Z","leftAt":null,"name":"Noah"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381690,"createdAt":"2020-02-26T03:13:33.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"4V4","mapVariantCategory":"Hero Battle","lobbyTitle":"","hostName":"Daedalus","slotsHumansTotal":8,"slotsHumansTaken":1,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":2,"minorVersion":34,"headerHash":null,"documentHash":null,"iconHash":"920f4439542fd35df56203b44833f7a1424fdb3ebb36d2525fa7a492e212442a","document":{"bnetId":253710,"type":"map","name":"Hero Line Wars Starlight"}},"players":[{"joinedAt":"2020-02-26T03:13:33.000Z","leftAt":null,"name":"Daedalus"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381606,"createdAt":"2020-02-26T03:13:33.000Z","closedAt":null,"status":"open","mapVariantIndex":8,"mapVariantMode":"Heroic Commanders","mapVariantCategory":"Tug Of War","lobbyTitle":"only noobs play mengsk","hostName":"Icarus","slotsHumansTotal":6,"slotsHumansTaken":3,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":2,"minorVersion":56,"headerHash":null,"documentHash":null,"iconHash":"db1f21cc0ba788acf7bfd69f93f80fc2bc583369ae5a69cce3c85ae928e70def","document":{"bnetId":208271,"type":"map","name":"Direct Strike"}},"players":[{"joinedAt":"2020-02-26T03:13:33.000Z","leftAt":null,"name":"Icarus"},{"joinedAt":"2020-02-26T03:13:34.000Z","leftAt":null,"name":"Stetmann"},{"joinedAt":"2020-02-26T03:13:34.000Z","leftAt":null,"name":"threth"}]},{"bnetBucketId":1574794309,"bnetRecordId":16381689,"createdAt":"2020-02-26T03:13:33.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"2V2","mapVariantCategory":"Tug Of War","lobbyTitle":"T   U   G       O  F       W   A   R","hostName":"Synergistic","slotsHumansTotal":4,"slotsHumansTaken":2,"region":{"code":"US","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":41,"headerHash":null,"documentHash":null,"iconHash":"61cf9c73a72cc77eddcec03444e0ad511b7b62c9a1feffb0e563e714e1688f4a","document":{"bnetId":314940,"type":"map","name":"Marine Tug o War 줄다리기"}},"players":[{"joinedAt":"2020-02-26T03:13:33.000Z","leftAt":null,"name":"Synergistic"},{"joinedAt":"2020-02-26T03:13:35.000Z","leftAt":null,"name":"RandomUC"}]},{"bnetBucketId":1574802246,"bnetRecordId":11073140,"createdAt":"2020-02-26T03:13:45.000Z","closedAt":null,"status":"open","mapVariantIndex":5,"mapVariantMode":"live 5 Hp500%(Hel)","mapVariantCategory":"Tower Defense","lobbyTitle":"랜타디 가자 새끼들아","hostName":"뇌물입니다","slotsHumansTotal":8,"slotsHumansTaken":1,"region":{"code":"KR","name":""},"mapDocumentVersion":{"majorVersion":1,"minorVersion":38,"headerHash":null,"documentHash":null,"iconHash":"da14a6d5ca78eaac143bb8aa381c244c989d6144fb4b100e1b9f5f0def62e441","document":{"bnetId":120973,"type":"map","name":"Random Tower Defense Race mode"}},"players":[{"joinedAt":"2020-02-26T03:13:45.000Z","leftAt":null,"name":"뇌물입니다"}]},{"bnetBucketId":1574802246,"bnetRecordId":11073146,"createdAt":"2020-02-26T03:13:45.000Z","closedAt":null,"status":"open","mapVariantIndex":0,"mapVariantMode":"RPG","mapVariantCategory":"RPG","lobbyTitle":"","hostName":"카니","slotsHumansTotal":4,"slotsHumansTaken":1,"region":{"code":"KR","name":""},"mapDocumentVersion":{"majorVersion":3,"minorVersion":315,"headerHash":null,"documentHash":null,"iconHash":"9ae417febe3641bebf83ba08e64cfc08108151763470e11ab61c7dd7abec7acb","document":{"bnetId":117850,"type":"map","name":"무기 강화 알피지"}},"players":[{"joinedAt":"2020-02-26T03:13:45.000Z","leftAt":null,"name":"카니"}]}]"""
    import json
    data = json.loads(data)
    return HttpResponse(json.dumps(data), content_type="application/json")

class Insights(APIView):
    def get(self, request):
        user_qs = (
            models.DiscordUser
            .objects
            .annotate(avg_elo=Avg(
                'profiles__leaderboard__elo'
            ))
            .annotate(avg_victim=Avg(
                'profiles__losses__victim_number'
            ))
            .all()
        )
        u = user_qs.get(email='dfitz.murrieta@gmail.com')
        response = {
            'avg_elo': u.avg_elo,
            'avg_victim': u.avg_victim,
        }
        return Response(response)