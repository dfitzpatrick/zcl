from decimal import Decimal

from django import http
from django.db.models import Count, Q, F, DecimalField, Case, When, Value, Avg, OuterRef, Subquery, Sum
from django.db.models.expressions import Window
from django.db.models.functions import Rank
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework.views import APIView
from api.models import Segment, Match, MatchMessage, SegmentProfileItem
from api.serializers import MatchSerializer
from django.contrib.postgres.aggregates import StringAgg


from ..models import SC2Profile


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
        model = SC2Profile
        fields = ('id', 'name', 'total_matches', 'total_wins', 'total_losses', 'total_draws', 'rate', 'win_rate', 'adjusted_win_rate', 'rank')

class Standings(APIView):

    def build_adj_rates(self):
        container = []
        for i in range(16):
            if i <= 5:
                container.append(When(total_matches=i, then=i*0.1))
            elif i == 6:
                container.append(When(total_matches=i, then=0.6))
            elif 6 < i <= 10:
                container.append(When(total_matches=i, then=((i-6.0) * 0.05) + 0.6))
            elif i == 11:
                container.append(When(total_matches=i, then=0.85))
            elif 11 < i <= 15:
                container.append(When(total_matches=i, then=((i-11.0)*0.03) +0.85))
        return container


    def get(self, request: Request):
        season = request.GET.get('season')
        league = request.GET.get('league')

        rank_window = Window(expression=Rank(),
                             order_by=F('adjusted_win_rate').desc())


        filter = Q(rosters__match__ranked=True)
        if league is not None:
            filter &= Q(rosters__match__league=league)
        if season is not None:
            filter &= Q(rosters__match__season=season)

        profiles = (
            SC2Profile
            .objects
            .annotate(
                total_matches=Count(
                    'rosters__match',
                    filter=filter,
                    distinct=True
                ),
                total_wins=Count(
                    'rosters__match__match_winners',
                    filter=filter & Q(rosters__match__match_winners__profile__id=F('id')),
                    distinct=True
                ),
                total_losses=Count(
                    'rosters__match__match_losers',
                    filter=filter & Q(rosters__match__match_losers__profile__id=F('id')),
                    distinct=True
                ),
                total_draws=F('total_matches') - F('total_wins') - F('total_losses'),
                win_rate=Case(
                    When(total_matches=0, then=0),
                    default=(Decimal('1.0') * F("total_wins") / (
                                F("total_wins") + F("total_losses") + (0.5 * F("total_draws")))) * 100,
                    output_field=DecimalField(),
                ),
                rate=Case(*self.build_adj_rates(),
                          default=1,
                          output_field=DecimalField(decimal_places=3, max_digits=5)
                          ),

                adjusted_win_rate=F('rate') * F('win_rate'),
                rank=rank_window

            )
            .filter(total_matches__gte=1)
            .order_by('rank')
        )

        return Response(StandingsSerializer(profiles, many=True).data, status=200)

class AbbreviatedMatchSerializer(serializers.Serializer):
    id = serializers.CharField()
    match_date = serializers.CharField()
    players = serializers.CharField()
    winners = serializers.CharField()


    # class Meta:
    #   model = Match
    #    fields = ('id', 'players', 'winners',)

class ProfileStatsSerializer(serializers.Serializer):
    avg_victim = serializers.DecimalField(max_digits=2, decimal_places=1)
    avg_all_chats = serializers.IntegerField()

    class Meta:
        fields = ('id', 'name', 'avg_victim', 'avg_all_chats')

class ProfileStats(APIView):

    def get(self, request: Request, profile_id: str):
        profile = None
        result = {}

        try:
            profile = SC2Profile.objects.get(id=profile_id)
        except SC2Profile.DoesNotExist:
            return Response("Profile does not exist", status=status.HTTP_400_BAD_REQUEST)

        ms = Match.objects.annotate(players=Count('rosters', distinct=True)).filter(status='final', players=8)
        ge_window = Window(expression=Rank(), partition_by=[F('match__match_date')],
                           order_by=(F('match__match_date'), F('game_time')))
        bunkers_cancelled = profile.game_events.filter(match__in=ms, key__id__istartswith='bunker').annotate(
            rank=ge_window).annotate(
            cancels=Case(When(Q(rank=2) & Q(key='bunker_cancelled'), then=1), default=0, output_field=DecimalField())).aggregate(Sum('cancels'))['cancels__sum']

        aggregates = ms.aggregate(
            avg_victim=Avg(
                'match_losers__victim_number',
                filter=Q(match_losers__profile=profile), distinct=True
            ),
            wins=Count('match_winners', filter=Q(match_winners__profile=profile), distinct=True)


        )
        total_matches = profile.rosters.filter(match__in=ms).count()
        all_chat_qs = MatchMessage.objects.filter(profile=profile, match__in=ms, message_type='all_chat')
        message_aggregates = all_chat_qs.aggregate(
            count=Count('message'),
            num_ggs=Count('message', filter=Q(message__icontains='gg'))
        )
        profile_segments_qs = SegmentProfileItem.objects.filter(profile=profile, match__in=ms)
        segment_aggregates = profile_segments_qs.aggregate(
            num_first_team_eliminated=Count('match', filter=Q(eliminated=True, segment__measure='three_teams'), distinct=True),
            num_times_final=Count('match', filter=Q(eliminated=False, segment__measure='two_teams'), distinct=True)
        )
        result['total_matches'] = total_matches
        result['wins'] = aggregates['wins']
        result['losses'] =  total_matches - aggregates['wins']
        result['avg_gg_all_chat'] = message_aggregates['num_ggs'] / total_matches if total_matches > 0 else 0
        result['avg_victim'] = aggregates['avg_victim']
        result['avg_all_chats'] = message_aggregates['count'] / total_matches if total_matches > 0 else 0
        result['avg_first_bunker_cancelled'] = (bunkers_cancelled / total_matches) if total_matches > 0 else 0
        result['avg_first_team_eliminated'] = segment_aggregates['num_first_team_eliminated'] / total_matches if total_matches > 0 else 0
        result['avg_times_in_final'] = segment_aggregates['num_times_final'] / total_matches if total_matches > 0 else 0
        result['win_rate_from_final'] = result['wins'] / segment_aggregates['num_times_final'] if segment_aggregates['num_times_final'] > 0 else 0
        return Response(result, status=200)


class ProfileStatsSerializer2(serializers.Serializer):

    id = serializers.CharField()
    name = serializers.CharField()
    avatar_url = serializers.CharField()
    total_matches = serializers.IntegerField()
    total_matches_1650 = serializers.IntegerField()
    wins = serializers.IntegerField()
    wins_1650 = serializers.IntegerField()
    win_rate = serializers.FloatField()
    win_rate_1650 = serializers.FloatField()
    death_avg = serializers.FloatField()
    death_avg_1650 = serializers.FloatField()

    class Meta:
        fields = ('id', 'name')

class ProfileStats2(APIView):

    def get(self, request: Request, profile_id: str):
        profile = None
        try:
            profile = SC2Profile.objects.get(id=profile_id)
        except SC2Profile.DoesNotExist:
            return Response("Profile does not exist", status=status.HTTP_400_BAD_REQUEST)

        ms = (
            Match
            .objects
            .all()

            .annotate(
                players=Count('rosters', distinct=True),
                lobby_elo=Avg(
                    'rosters__sc2_profile__leaderboards__elo',
                    filter=Q(rosters__sc2_profile__leaderboards__mode='2v2v2v2',
                             rosters__match__league=None,

                    )
                )
            )
            .filter(league=None, legacy=False, players=8, season=None).exclude(lobby_elo=None)

        )
        die = (
            SC2Profile
            .objects
            .annotate(
                avg_death=Avg(
                    'losses__victim_number',
                    filter=Q(losses__victim_number__gte=1, losses__match__in=ms)
                )
            )
        )
        elo_1650 = ms.filter(lobby_elo__gte=1650)
        die_1650 = (
            SC2Profile
                .objects
                .annotate(
                avg_death=Avg(
                    'losses__victim_number',
                    filter=Q(losses__victim_number__gte=1, losses__match__in=elo_1650)
                )
            )
        )
        ms_qs =  (
            ms
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
            .filter(rosters__sc2_profile__id=profile.id)
            .order_by('-match_date')
        )

        ge_window = Window(expression=Rank(), partition_by=[F('match__match_date')], order_by=(F('match__match_date'), F('game_time')))
        game_events = profile.game_events.filter(match__in=ms, key__id__istartswith='bunker').annotate(rank=ge_window).annotate(cancels=Case(When(Q(rank=2) & Q(key='bunker_cancelled'), then=1), default=0, output_field=DecimalField()))
        cancels = int(game_events.aggregate(Sum('cancels'))['cancels__sum'])
        game_events_1650 = profile.game_events.filter(match__in=ms.filter(lobby_elo__gte=1650), key__id__istartswith='bunker').annotate(rank=ge_window).annotate(cancels=Case(When(Q(rank=2) & Q(key='bunker_cancelled'), then=1), default=0, output_field=DecimalField()))
        cancels_1650 = int(game_events_1650.aggregate(Sum('cancels'))['cancels__sum'])



        total_matches = profile.rosters.filter(match__in=ms).count()
        all_chats = 'N/A'
        if total_matches > 0:
            all_chats = MatchMessage.objects.filter(profile=profile, match__in=ms).count() or 0
            all_chats = all_chats / total_matches

        results = {
            'id': profile.id,
            'name': profile.name,
            'avatar_url': profile.avatar_url,
            'all_chats_per_game': all_chats,
            'total_matches': profile.rosters.filter(match__in=ms).count(),
            'first_bunker_cancels': cancels,
            'first_bunker_cancels_1650': cancels_1650,
            'wins': profile.wins.filter(match__in=ms).count(),
            'total_matches_1650': profile.rosters.filter(match__in=elo_1650).count(),
            'wins_1650': profile.wins.filter(match__in=elo_1650).count(),
            'death_avg': die.get(id=profile.id).avg_death,
            'death_avg_1650': die_1650.get(id=profile.id).avg_death

        }
        results['win_rate'] = (results['wins'] / max([results['total_matches'], 1])) * 100
        results['win_rate_1650'] = (results['wins_1650'] / max([results['total_matches_1650'], 1])) * 100
        results['match_set'] = AbbreviatedMatchSerializer(ms_qs, many=True).data

        return Response(results, status=200)
