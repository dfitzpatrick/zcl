from dateutil import parser
from django_filters import rest_framework as filters
from django.db.models import Q
from django.db.models import When, Case, IntegerField
from api import models

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

class BeforeDateFilter(AfterDateFilter):
    def __init__(self, **kwargs):
        print('before date')
        super(AfterDateFilter, self).__init__(dunder="lte", **kwargs)

class Players(filters.Filter):
    def __init__(self, **kwargs):
        fn = 'rosters__sc2_profile__id'
        super(Players, self).__init__(fn, **kwargs)

    def filter(self, qs, value):
        if value is None:
            return qs
        players = value.split(',')
        query = Q()
        for p in players:
            query &= Q(profile_ids__icontains=p)
        return qs.filter(query)

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

class MatchFilter(filters.FilterSet):

    sort = filters.OrderingFilter(fields=(
        ('match_date', 'match_date'),
        ('nukes', 'nukes'),
        ('game_length', 'game_length'),
        ('tanks', 'tanks'),
        ('turrets', 'turrets'),
    ))
    class Meta:
        model = models.Match
        fields = ('match_date',)
