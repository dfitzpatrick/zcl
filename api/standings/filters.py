from django_filters import rest_framework as filters
from .. import models

class StandingsFilter(filters.FilterSet):

    sort = filters.OrderingFilter(
        fields=(
            ('id', 'id'),
            ('name', 'name'),
            ('total_matches', 'total_matches'),
            ('total_losses', 'total_losses'),
            ('total_wins', 'total_wins'),
            ('total_draws', 'total_draws'),
            ('rate', 'rate'),
            ('win_rate', 'win_rate'),
            ('adjusted_win_rate', 'adjusted_win_rate'),
            ('rank', 'rank'),
        )
    )
    class Meta:
        model = models.SC2Profile
        fields = ('id', 'name')