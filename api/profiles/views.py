from decimal import Decimal

from django.db.models import Count, Q, F, DecimalField, Case, When, Sum
from django.db.models.expressions import Window
from django.db.models.functions import Rank
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import filters, serializers
from .. import models


class ProfileView(viewsets.ModelViewSet):
    filterset_class = filters.ProfileFilters
    serializer_class = serializers.ProfileSerializer
    queryset = models.SC2Profile.objects.prefetch_related('discord_users').all()

    def build_adj_rates(self):
        container = []
        for i in range(16):
            if i <= 5:
                container.append(When(total_matches=i, then=i * 0.1))
            elif i == 6:
                container.append(When(total_matches=i, then=0.6))
            elif 6 < i <= 10:
                container.append(When(total_matches=i, then=((i - 6.0) * 0.05) + 0.6))
            elif i == 11:
                container.append(When(total_matches=i, then=0.85))
            elif 11 < i <= 15:
                container.append(When(total_matches=i, then=((i - 11.0) * 0.03) + 0.85))
        return container

    @action(methods=['get'], detail=True)
    def lanes(self, request, pk, *args, **kwargs):
        season = request.GET.get('season')
        league = request.GET.get('league')

        rank_window = Window(expression=Rank(),
                             order_by=F('adjusted_win_rate').desc())

        filter = Q(lane_rosters__sc2_profile__id=pk)
        if league is not None:
            filter &= Q(rosters__match__league=league)
        if season is not None:
            filter &= Q(rosters__match__season=season)

        profiles = (
            models.SC2Profile
                .objects
                .prefetch_related('lane_segments', 'profile_segments')
                .annotate(
                total_matches=Count(
                    'lane_rosters__match',
                    filter=filter,
                    distinct=True
                ),
                test=Case(
                    When(profile_segments__total_score__lt=F('lane_segments__total_score'), then=Sum(1)),
                    default=0,
                    filter=Q(lane_segments__profile__id=pk),
                    output_field=DecimalField()
                ),
                total_wins=Count(
                    'lane_rosters__match__match_winners',
                    filter=filter & Q(lane_rosters__match__match_winners__profile__id=F('id')),
                    distinct=True
                ),
                total_losses=Count(
                    'lane_rosters__match__match_losers',
                    filter=filter & Q(lane_rosters__match__match_losers__profile__id=F('id')),
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
                .order_by('rank')[:5]
        )

        return Response(serializers.LaneStandingsSerializer(profiles, many=True).data, status=200)

    class Meta:
        model = models.SC2Profile
        fields = '__all__'