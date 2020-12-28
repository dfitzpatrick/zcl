from django.conf.urls import include, url
from rest_framework import routers

from accounts import views as account_views
from .banks.views import BankAPIView
from . import views
from .standings.views import Standings, ProfileStats
from .teams.views import TeamView
from .events.views import EventView
from .matches.views import MatchView
from .leaderboards.views import LeaderboardView
from .standings.standing_view import StandingView
from .profiles.views import ProfileView
from .users.views import UserView
router = routers.DefaultRouter()
router.register('users', UserView, basename='users')
router.register('profiles', ProfileView, basename='profiles')
router.register('guilds', views.GuildView)
router.register('leagues', views.LeagueView)
router.register('leaderboards', LeaderboardView)
router.register('matches', MatchView, basename='matches')
router.register('standings', StandingView, basename='standings')

router.register('match_events', views.MatchEventView)
router.register('replays', views.ReplayView)
router.register('automatch', views.AutoMatch, basename='automatch')
router.register('connections', account_views.Connections, basename='connections')
router.register('gameevents', views.GameEventView, basename='gameevents')
router.register('teams', TeamView, basename='teams')



urlpatterns = [

    # ...
]

urlpatterns = [
    url('', include(router.urls)),
    url('current_user/', views.CurrentUser.as_view()),
    url('replayupload', views.ReplayUpload.as_view()),
    url('authorize/', views.exchange_discord_token),
    url('^chartpoints/(?P<match_id>\d+)/$', views.ChartPointView.as_view()),
    url('^charts/(?P<match_id>\d+)/$', views.ChartsView.as_view()),
    url('test/', views.Insights.as_view()),
    url('^banks/$', BankAPIView.as_view()),
    #url('standings', Standings.as_view(), name='standings'),
    url('playerstats/(?P<profile_id>.+)/$', ProfileStats.as_view(), name='playerstats'),
    url('event/', EventView.as_view(), name='event'),




]
