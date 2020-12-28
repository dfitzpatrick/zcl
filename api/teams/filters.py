from django_filters import rest_framework as filters
from .. import models
from .. import filters as custom_filters

class TeamFilter(filters.FilterSet):

    players = custom_filters.CSVMembershipOf(field_name='profile_ids')
    sort = filters.OrderingFilter(fields=(
        ('games', 'games'),
        ('wins', 'wins'),
        ('losses', 'losses'),
        ('team_elo', 'team_elo'),
        ('win_rate', 'win_rate')
    ))
    class Meta:
        model = models.Team
        fields = ('id', 'players',)