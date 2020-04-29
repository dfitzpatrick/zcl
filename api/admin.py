from django.contrib import admin
from django.contrib.postgres.aggregates import StringAgg

from . import models


class MatchAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'id', 'created', 'match_date']

    def get_queryset(self, request):

        return (
            super(MatchAdmin, self)
            .get_queryset(request)
            .select_related('league', 'season',)
            .prefetch_related('rosters')
            .annotate(match_players=StringAgg(
                'rosters__sc2_profile__name',
                delimiter=', ')
            )
        )

class TeamAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        return (
            super(TeamAdmin, self)
            .get_queryset(request)
            .prefetch_related('profiles')
            .annotate(team_players=StringAgg(
                'profiles__name',
                delimiter=', ')
            )
        )

class MatchTeamAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        return (
            super(MatchTeamAdmin, self)
            .get_queryset(request)
            .select_related('team')
            .prefetch_related('team__profiles')
            .annotate(team_players=StringAgg(
                'team__profiles__name',
                delimiter=', ')
            )
        )
admin.site.register(models.Game)
admin.site.register(models.SC2Profile)
admin.site.register(models.Guild)
admin.site.register(models.League)
admin.site.register(models.Match, MatchAdmin)
admin.site.register(models.MatchEvent)
admin.site.register(models.Season)
admin.site.register(models.Roster)
admin.site.register(models.Unit)
admin.site.register(models.UnitStat)
admin.site.register(models.Replay)
admin.site.register(models.TwitchStream)
admin.site.register(models.GameEventName)
admin.site.register(models.GameEvent)
admin.site.register(models.GameUnit)
admin.site.register(models.GameUnitStat)
admin.site.register(models.ChartPoints)
admin.site.register(models.Leaderboard)
admin.site.register(models.MatchTeam, MatchTeamAdmin)
admin.site.register(models.Team, TeamAdmin)
