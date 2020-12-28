from rest_framework import viewsets, permissions
from . import serializers, filters
from .. import models
from decimal import Decimal
from django.db.models import Count, Q, F, DecimalField, Case, When, Value, Avg, OuterRef, Subquery, Sum
from django.db.models.expressions import Window
from django.db.models.functions import Rank

class StandingView(viewsets.ModelViewSet):
    serializer_class = serializers.StandingsSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filterset_class = filters.StandingsFilter
    rank_window = Window(expression=Rank(),
                        order_by=F('adjusted_win_rate').desc())

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
    def get_queryset(self):
        print(self.request.GET.get('limit'))
        rank_window = Window(expression=Rank(),
                             order_by=F('adjusted_win_rate').desc())
        filter = Q(rosters__match__ranked=True)

        season = self.request.GET.get('season', '')
        league = self.request.GET.get('league', '')
        if league != '':
            filter &= Q(rosters__match__league__id=league)
        if season != '':
            filter &= Q(rosters__match__season__id=season)

        profiles = (
            models.SC2Profile
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
        return profiles