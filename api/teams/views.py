from rest_framework import viewsets
from . import serializers, filters
from .. import models
from decimal import Decimal
from django.contrib.postgres.aggregates import StringAgg
from django.db.models import Avg, Count, When, Case, Q, F, DecimalField

class TeamView(viewsets.ModelViewSet):
    serializer_class = serializers.TeamSerializerWithAnnotations
    filterset_class = filters.TeamFilter
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
            .annotate(profile_ids=StringAgg(
            'profiles__id',
            delimiter=', ',
            distinct=True,
        ))
        .annotate(elo_initial=Avg(
            'profiles__leaderboards__elo'
        ))
        .annotate(team_elo=
            Case(
                When(elo_initial=None, then=0),
                default=F("elo_initial")

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