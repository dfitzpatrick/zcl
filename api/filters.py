import logging

from django.db.models import Q
from django.db.models import When, Case, IntegerField
from django_filters import rest_framework as filters

from api import models as api_models

log = logging.getLogger(__name__)

def limit_filter(qs, name, value):
    """
    Generic function for choosing the top n records
    Parameters
    ----------
    qs
    name
    value

    Returns
    -------

    """
    try:
        value = int(value)
        return qs[:value]
    except ValueError:
        return qs


class MatchHasPlayer(filters.Filter):

    def __init__(self, **kwargs):
        fn = 'rosters__sc2_profile__id'
        super(MatchHasPlayer, self).__init__(fn, **kwargs)

    def filter(self, qs, value):
        if value is None:
            return qs

        return qs.filter(Q(rosters__sc2_profile__id__icontains=value))


class MatchHasAnyPlayers(filters.Filter):
    def __init__(self, **kwargs):
        fn = 'rosters__sc2_profile__id'
        super(MatchHasAnyPlayers, self).__init__(fn, **kwargs)

    def filter(self, qs, value):
        if value is None:
            return qs
        players = value.split(',')
        query = Q()
        for p in players:
            query |= Q(rosters__sc2_profile__id__icontains=p)
        return qs.filter(query)

class ListFilter(filters.Filter):

    def __init__(self, **kwargs):
        super(ListFilter, self).__init__(**kwargs)

    def filter(self, qs, value):
        if value is None:
            return qs
        values = value.split(',')
        query = Q()
        for v in values:
            query |= Q(**{self.field_name: v})
        return qs.filter(query)


class LeaderboardListFilter(filters.Filter):

    def filter(self, qs, value):
        if value is None or value == "":
            return qs
        values = value.split(',')
        query = Q()
        for v in values:
            query |= Q(**{self.field_name: v})

        rank_values = qs.all().values('pk', 'rank')
        mappings = dict((p['pk'], p['rank']) for p in rank_values)
        whens = [When(pk=pk, then=rank) for pk, rank in mappings.items()]

        return (
            qs
            .annotate(rank=Case(
                *whens, default=0, output_field=IntegerField())
            ).filter(query)
        )

class MatchFilter(filters.FilterSet):
    player = MatchHasPlayer()
    anyplayers = MatchHasAnyPlayers()
    max = filters.Filter(field_name='id', method=limit_filter)

    class Meta:
        model = api_models.Match
        fields = '__all__'
        exclude = ['details']



class LeaderboardFilter(filters.FilterSet):
    id = LeaderboardListFilter(field_name='id')
    mode = filters.CharFilter(field_name='mode')

    class Meta:
        model = api_models.Leaderboard
        fields = '__all__'

class GameEventFilter(filters.FilterSet):
    match = filters.NumberFilter(field_name='match')

    class Meta:
        model = api_models.GameEvent
        fields = '__all__'