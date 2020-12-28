import logging

from django.db.models import Q
from django.db.models import When, Case, IntegerField
from django_filters import rest_framework as filters
from dateutil import parser

from api import models as api_models

log = logging.getLogger(__name__)


class CSVMembershipOf(filters.Filter):

    def __init__(self, *, field_name, dunder_method="icontains", **kwargs):
        super(CSVMembershipOf, self).__init__(field_name=field_name, **kwargs)
        self.dunder_method = dunder_method

    def filter(self, qs, value):
        if not hasattr(value, 'split'):
            return qs
        value_set = value.split(',')
        query = Q()
        for v in value_set:
            query &= Q(**{f"{self.field_name}__{self.dunder_method}": v})

        return qs.filter(query)





















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

class CharFieldContainsFilter(filters.Filter):
    def __init__(self, **kwargs):
        super(CharFieldContainsFilter, self).__init__(**kwargs)

    def filter(self, qs, value):
        if value is None:
            return qs
        query = Q(**{f"{self.field_name}__icontains": value})
        print(query)
        return qs.filter(query)

class BeforeDateFilter(filters.Filter):
    def __init__(self, **kwargs):
        super(BeforeDateFilter, self).__init__(**kwargs)
        
    def filter(self, qs, value):
        if value is None:
            return qs
        query = Q(**{f"{self.field_name}__lte": value})
        return qs.filter(query)
    
class GenericFilter(filters.Filter):
    def __init__(self, *, dunder, **kwargs):
        super(GenericFilter, self).__init__(**kwargs)
        self.dunder = dunder

    def filter(self, qs, value):
        if value is None or self.dunder is None:
            return qs
        q = Q(**{f"{self.field_name}__{self.dunder}": value})
        return qs.filter(q)

class AfterDateFilter(GenericFilter):
    def __init__(self, **kwargs):
        super(AfterDateFilter, self).__init__(dunder="gte", **kwargs)

    def filter(self, qs, value):
        try:
            value = parser.parse(value)
            return super(AfterDateFilter, self).filter(qs, value)
        except Exception as e:
            print(f"crap: {e}")
            return qs

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
    players = MatchHasAnyPlayers()
    start_date = filters.DateFilter()
    max = filters.Filter(field_name='id', method=limit_filter)
    match_after = AfterDateFilter(field_name="match_date")

    class Meta:
        model = api_models.Match
        fields = '__all__'
        exclude = ['details']

class StandingsFilter(filters.FilterSet):
    league = filters.NumberFilter('league')
    season = filters.NumberFilter('season')

class LeaderboardFilter(filters.FilterSet):
    profile_id = LeaderboardListFilter(field_name='profile__id')
    mode = filters.CharFilter(field_name='mode')


    class Meta:
        model = api_models.Leaderboard
        fields = '__all__'

class GameEventFilter(filters.FilterSet):
    match = filters.NumberFilter(field_name='match')

    class Meta:
        model = api_models.GameEvent
        fields = '__all__'

class ProfileFilter(filters.FilterSet):
    name = CharFieldContainsFilter(field_name='name')

    class Meta:
        model = api_models.SC2Profile
        fields = '__all__'