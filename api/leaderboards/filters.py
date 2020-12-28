from django_filters import rest_framework as filters
from django.db.models import Q
from django.db.models import When, Case, IntegerField

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

class LeaderboardNameFilter(filters.Filter):

    def filter(self, qs, value):
        if value is None or value == "":
            return qs

        query = Q(**{f"{self.field_name}__{self.lookup_expr}": value})

        rank_values = qs.all().values('pk', 'rank')
        mappings = dict((p['pk'], p['rank']) for p in rank_values)
        whens = [When(pk=pk, then=rank) for pk, rank in mappings.items()]

        return (
            qs
            .annotate(rank=Case(
                *whens, default=0, output_field=IntegerField())
            ).filter(query)
        )

class LeaderboardFilter(filters.FilterSet):
    profile_id = LeaderboardListFilter(field_name='profile__id')
    name = LeaderboardNameFilter(field_name='name', lookup_expr='icontains')
    mode = filters.CharFilter(field_name='mode')
    league = filters.NumberFilter(field_name='league__id')

    sort = filters.OrderingFilter(fields=(
        ('rank', 'rank'),
        ('name', 'name'),
        ('elo', 'elo'),
        ('games', 'games'),
        ('wins', 'wins'),
        ('losses', 'losses'),
        ('updated', 'updated'),
    ))