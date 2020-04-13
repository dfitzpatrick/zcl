from django.contrib.postgres.aggregates import StringAgg
from django.db.models import Q
from django.db.models.query import QuerySet

from api.models import Match


def qs_with_players() -> QuerySet:
    qs = (
        Match
        .objects
        .prefetch_related('rosters', 'rosters__sc2_profile', 'rosters__sc2_profile__discord_users','rosters__match', 'events')
        .annotate(players=StringAgg(
            'rosters__sc2_profile__name',
            delimiter=', ',
            distinct=True,
            )
        )

        .annotate(profile_ids=StringAgg(
            'rosters__sc2_profile__id',
            delimiter=', ',
            distinct=True,
            )
        )
        .annotate(winners=StringAgg(
            'events__handle__name',
            delimiter=', ',
            filter=Q(events__key='WIN'),
            distinct=True
        ))

        .order_by('-match_date', 'rosters__team_number')


    )
    return qs

def qs_with_details():
    qs = (
        Match
        .objects
        .prefetch_related('rosters', 'events')
        .annotate(players='rosters__sc2_profile')
        .annotate(events='events')

    )
    return qs