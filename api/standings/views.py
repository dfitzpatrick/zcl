from decimal import Decimal

from django import http
from django.db.models import Count, Q, F, DecimalField, Case, When, Value
from django.db.models.expressions import Window
from django.db.models.functions import Rank
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView


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
        fields = ('id', 'rank', 'name', 'total_wins', 'total_losses', 'total_matches', 'total_draws', 'rate', 'win_rate', 'adjusted_win_rate')

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





    def get(self, request: http.HttpRequest):

        rank_window = Window(expression=Rank(),
                             order_by=F('adjusted_win_rate').desc())

        season = request.GET.get('season')
        league = request.GET.get('league')
        custom_filter = {}
        wins_filter = Q(wins__match__ranked=True)
        losses_filter = Q(losses__match__ranked=True)
        total_matches_filter = Q(rosters__match__ranked=True)


        if season:
            wins_filter &= Q(wins__match__season=season)
            losses_filter &= Q(losses__match__season=season)
            total_matches_filter &= Q(rosters__match__season=season)
            custom_filter['rosters__match__season'] = season
        if league:
            wins_filter &= Q(wins__match__league=league)
            losses_filter &= Q(losses__match__league=league)
            custom_filter['rosters__match__league'] = league
            total_matches_filter &= Q(rosters__match__league=league)
        profiles = SC2Profile.objects.filter(**custom_filter)
        profiles = (
            profiles
            .prefetch_related(
                'wins', 'losses', 'rosters',
            )
            .annotate(
                total_wins=Count(
                    'wins',
                    filter=wins_filter,

                    distinct=True
                ),
                total_losses=Count(
                    'losses',
                    filter=losses_filter,
                    distinct=True
                ),
                total_matches=Count(
                    'rosters',
                    filter=total_matches_filter,

                    distinct=True
                ),
                total_draws=F('total_matches') - F('total_losses') - F('total_wins'),
                win_rate=Case(
                    When(total_matches=0, then=0),
                    default=(Decimal('1.0') * F("total_wins") / (F("total_wins") + F("total_losses") + (0.5 * F("total_draws")))) * 100,
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

