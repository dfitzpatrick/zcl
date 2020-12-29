from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from . import serializers, filters
from api import models
from django.contrib.postgres.aggregates import StringAgg
from django.db.models import F, OuterRef, Subquery, Count, Q, Sum, When, Case, Prefetch, Avg
from django.db.models.fields import IntegerField, TextField
from ..import utils
from ..profiles.serializers import ProfileSerializer
import dateutil

class MatchView(viewsets.ModelViewSet):

    serializer_class = serializers.MatchSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    #filterset_class = filters.MatchFilter ok



    def get_queryset(self):
        """
        Try to optimize this queryset to be faster.
        Right now:

        No filters and with the annotations for certain unit stats, we are looking
        at about 450ms when paged to 20 records.

        I have attempted to add in a way to filter matches if ALL players exist.
        This is brought in via querystring 'players' and 'winners that is a CSV
        of the object id.

        The way I ended up structuring it to get the right SQL is to create two
        annotated entries that provide a COUNT of rosters that have this team member.
        I then do a final filter() that checks if the COUNT is the same as the
        querystring list length when it is split().

        This works but it brings the overall query time to about 4500ms.

        Returns
        -------

        """

        # Reduce the dataset to help with performance to only units that we
        # care about
        filter_units = ['Nuke', 'SiegeBreakerSieged', 'AutoTurret']

        # Filter AND on Players and Winners.
        # Is there a better way to do this?
        players = self.request.query_params.get('players', '')
        winners = self.request.query_params.get('winners', '')
        player_ids = []
        winner_ids = []
        q_players_winners = Q()
        q_filter_players = Q()

        if players is not '':
            player_ids = players.split(',')
            q_players_winners &= Q(players_filter_count=len(player_ids))

        if winners is not '':
            winner_ids = winners.split(',')
            q_players_winners &= Q(rosters__sc2_profile__id__in=winner_ids)

        if player_ids or winner_ids:
            q_filter_players = Q(rosters__sc2_profile__id__in=player_ids + winner_ids)

        league = self.request.query_params.get('league', '')
        season = self.request.query_params.get('season', '')
        ranked = self.request.query_params.get('ranked', '')
        before_date = self.request.query_params.get('before_date', '')
        after_date = self.request.query_params.get('after_date', '')
        sort = self.request.query_params.get('sort', '')
        sort = '-match_date' if sort == '' else sort
        primary_filters = Q(status='final', legacy=False)
        primary_filters &= ~Q(replay=None)
        if league != '':
            primary_filters &= Q(league__id=league)
        if season != '':
            primary_filters &= Q(league__season__id=season)
        if ranked != '':
            primary_filters &= Q(ranked=ranked == '1')
        if before_date != '':
            bd = dateutil.parser.parse(before_date)
            primary_filters = Q(match_date__lte=bd)
        if after_date != '':
            ad = dateutil.parser.parse(after_date)
            primary_filters = Q(match_date__gte=ad)
        queryset = (
            models.Match
                .objects
            .select_related(
                'aggregates'
            )
            .annotate(
                elo_average=Avg(
                    'rosters__sc2_profile__leaderboards__elo',
                    filter=Q(rosters__sc2_profile__leaderboards__mode='2v2v2v2'),
                    output_field=IntegerField(),
                ),
                players_filter_count=Count(
                    'rosters__sc2_profile__id',
                    filter=Q(rosters__sc2_profile__in=player_ids),
                    distinct=True
                ),
                winners_filter_count=Count(
                    'rosters__sc2_profile__id',
                    filter=Q(match_winners__profile__id__in=winner_ids),
                    distinct=True
                ),
                tanks=F('aggregates__tanks'),
                scv=F('aggregates__scv'),
                nukes=F('aggregates__nukes'),
                turrets=F('aggregates__turrets'),
                bunkers=F('aggregates__bunkers'),
                sensors=F('aggregates__sensors'),
                shields=F('aggregates__shields'),
                supply_depots=F('aggregates__supply_depots'),
                names=F('aggregates__names'),
                alt_winners=F('aggregates__winners'),
                mid=F('aggregates__mid'),
            )

        ).filter(primary_filters)
        # Seems to be an expensive operation. From 450ms to 4500
        if len(q_players_winners) > 0:
            queryset = queryset.filter(q_players_winners)
        return queryset.order_by(sort)


    @action(methods=['get'], detail=True)
    def teams(self, request, *args, **kwargs):
        sub_query = models.Roster.objects.filter(match__matchteam=OuterRef('pk'))
        match: models.Match = self.get_object()
        qs = (
            models.Match
            .objects
            .prefetch_related( 'rosters__sc2_profile__discord_users')
            .get(id=match.pk)
        )
        # lets just make this easy

        return Response(serializers.MatchTeamRosterSerializer(match.matchteam_set.all(), many=True).data, 200)

    @action(methods=['get'], detail=True)
    def rosters(self, request, *args, **kwargs):
        match: models.Match = self.get_object()
        rosters = (
            match
                .rosters
                .all()
        )
        return Response(serializers.RosterSerializer(rosters, many=True).data, status=200)

class MatchView2(viewsets.ModelViewSet):
    """
    The main match end point
    """
    serializer_class = serializers.MatchSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = (
        models.Match
        .objects
        .prefetch_related('rosters', 'rosters__sc2_profile',
            'rosters__sc2_profile__discord_users', 'rosters__match', 'events')
        .annotate(players=StringAgg(
            'rosters__sc2_profile__name',
            delimiter=', ',
            distinct=True,
        ))
        .annotate(profile_ids=StringAgg(
            'rosters__sc2_profile__id',
            delimiter=', ',
            distinct=True,
        ))
        .annotate(winners=StringAgg(
            'match_winners__profile__name',
            delimiter=', ',
        ))
        .order_by('-match_date', 'rosters__team_number')
    )


