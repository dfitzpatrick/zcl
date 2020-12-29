import typing

import django.utils.timezone
from django.contrib.postgres.fields import JSONField
from django.db import models

from accounts.models import DiscordUser, SocialAccount

EVENT_KEYS = (
    ('player_leave', "Player Leaving"),
    ('bunker_killed', "Bunker Destroyed"),
    ('bunker_started', "Bunker Building"),
    ('match_end', "Match Ending"),
    ('bunker_cancelled', "Bunker Cancelled"),
    ('match_start', "Match Starting"),
    ('WIN', 'Player Wins'),
    ('LOSS', 'Player Loses'),
    ('DRAW', 'Player Draws'),
    ('ADJ', 'Player Point Adjustment'),
)
MATCH_STATUS = (
    ('initial', 'Initial'),
    ('abandoned', 'Abandoned'),
    ('final', 'Final'),
)

MESSAGE_TYPES = (
    ('all_chat', 'All Chat'),
    ('allied_chat', 'Allied Chat'),
)
TEAM_POSITIONS = (
    (0, 'Top Left'),
    (1, 'Top Right'),
    (2, 'Bottom Right'),
    (3, 'Bottom Left'),
)
TEAM_OUTCOMES = (
    ('win', 'Win'),
    ('loss', 'Loss'),
    ('draw', 'Draw'),
)

class WithTimeStamp(models.Model):
    created = models.DateTimeField(auto_created=True, auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class SC2Profile(models.Model):
    """
    The database object that represents a Starcraft 2 Profile.
    """
    # The primary key is what is known as a handle
    # {region}-S2-{realm_id}-{profile_id}  :str:
    id = models.CharField(primary_key=True, unique=True, max_length=50)

    created = models.DateTimeField(auto_created=True, auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=300)
    profile_url = models.URLField()
    avatar_url = models.CharField(max_length=300, blank=True, null=True)
    clan_tag = models.CharField(max_length=50, blank=True, default='')
    clan_name = models.CharField(max_length=300, blank=True, default='')
    discord_users = models.ManyToManyField(DiscordUser, related_name='profiles')

    def _parse_id(self, n: int) -> typing.Optional[str]:
        # The primary key is what is known as a handle
        # {region}-S2-{realm_id}-{profile_id}  :str:
        #    0      1   2           3
        try:
            parts = self.id.split('-')
            return parts[n]
        except (IndexError, AttributeError):
            return

    @property
    def region(self):
        return self._parse_id(0)

    @property
    def realm(self):
        return self._parse_id(2)

    @property
    def profile_id(self):
        return self._parse_id(3)


    def __repr__(self):
        return "[id={0.id}, name={0.name}]".format(self)

    def __str__(self):
        return self.__repr__()

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'
        ordering = ('name',)

class Guild(models.Model):
    """
    A discord Guild
    """
    id = models.BigIntegerField(primary_key=True, unique=True)
    name = models.CharField(max_length=300)


def upload_replay_to(instance, fn):
    """
    Used to generate a name for a replay to the s3 bucket. This will be the match
    id.
    Parameters
    ----------
    instance: The replay instance
    fn: The filename that was uploaded. This is automatically populated when
        passing it into the Replay model upload_to attribute.

    Returns
    -------

    """
    fn = instance.file.name
    return f"replays/{fn}.SC2Replay"


class Replay(models.Model):
    """
    Represents a replay object that a user has uploaded.
    This could be done by a couple ways

        - cli program (an automatic program via websockets -- matchcli)
        - server replay upload
    """
    created = models.DateTimeField(auto_created=True, auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # Associate with a match object directly. Only one replay is used per match.
    match = models.OneToOneField('Match', on_delete=models.SET_NULL, null=True, blank=True, related_name='replay')

    # Allow this to be null so we won't lose matches if someone is deleted.
    user = models.ForeignKey(DiscordUser, on_delete=models.SET_NULL, null=True, blank=True)

    file = models.FileField(upload_to=upload_replay_to)
    description = models.TextField(blank=True)




class Game(models.Model):
    """
    Placeholder in case we ever want to expand out and add more games.
    """
    id = models.CharField(primary_key=True, unique=True, max_length=50)

    created = models.DateTimeField(auto_created=True, auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=300)

class Match(models.Model):
    """
    The main match model that ties a match to a game and a guild. The idea is
    if we ever want to host multiple discords for different type of Arcade
    Games in the future. Right now it is extra fields.
    """
    created = models.DateTimeField(auto_created=True, auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    id = models.CharField(max_length=50, primary_key=True, unique=True)
    # This is used to track from new clients uploading replays what the original date was
    match_date = models.DateTimeField(default=django.utils.timezone.now)
    game_length = models.FloatField(default=0)
    # Each guild can have their own match set
    guild = models.ForeignKey(Guild, on_delete=models.SET_NULL, null=True)
    arcade_map = models.ForeignKey(Game, on_delete=models.SET_NULL, null=True)

    # A match may belong to a league, or may not. If a league is deleted, we
    # keep the matches
    league = models.ForeignKey('League', on_delete=models.SET_NULL, null=True, blank=True, related_name='matches')

    # A match may belong to a season, or may not. If a season is deleted, we
    # keep the matches.
    season = models.ForeignKey('Season', on_delete=models.SET_NULL, null=True, blank=True, related_name='seasons')

    # Since all games are not manually entered, do not allow this to be null
    game_id = models.CharField(max_length=300)

    # For tracking clients

    stream_url = models.URLField(blank=True, null=True)

    status = models.CharField(max_length=50, default='initial', choices=MATCH_STATUS)

    # Elementary team support for named teams
    teams = models.ManyToManyField('Team', through='MatchTeam')
    # Probably a really bad idea

    # Draw support
    draw = models.BooleanField(default=False)

    # Extra field in case a match with a league and season need to be excluded
    ranked = models.BooleanField(default=False)

    # To filter out old ZC4 Matches or those without replays. Will probably migrate
    # to just exclude on replay later.
    legacy = models.BooleanField(default=False)

    # Track Observers, either for 'initial' matches or just to know for later.
    observers = models.ManyToManyField(SC2Profile, blank=True, related_name='observers')

    # Track connected clients. Mainly for scaffolding matches
    clients = models.ManyToManyField(DiscordUser, blank=True, null=True, related_name='clients')



    def __str__(self):
        """
        If made from an annotation grab the players. Otherwise just use the
        match id.
        Returns
        -------

        """
        if hasattr(self, 'match_players'):
            return self.match_players
        return str(self.id)

    @property
    def streamers(self):
        """
        Finds which players are actively streaming when this method is called
        Returns
        -------

        """""
        return [r.stream_info for r in self.rosters.all() if r.stream_info is not None]



class MatchAggregates(models.Model):
    """
    Cheating here.
    Keep aggreagates for quicker rendering of match lists
    """
    match = models.OneToOneField(Match, on_delete=models.CASCADE, related_name='aggregates')
    nukes = models.IntegerField(default=0)
    tanks = models.IntegerField(default=0)
    turrets = models.IntegerField(default=0)
    bunkers = models.IntegerField(default=0)
    scv = models.IntegerField(default=0)
    sensors = models.IntegerField(default=0)
    shields = models.IntegerField(default=0)
    supply_depots = models.IntegerField(default=0)
    names = models.CharField(max_length=300, blank=True, default="")
    winners = models.CharField(max_length=200, blank=True, default="")
    mid = models.BooleanField(default=False)

class ProfileAlias(WithTimeStamp):
    profile = models.ForeignKey(SC2Profile, on_delete=models.CASCADE, related_name='aliases')
    name = models.CharField(max_length=300)


class Roster(models.Model):
    """
    Holds player starting positions and profiles.
    """
    created = models.DateTimeField(auto_created=True, auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    match = models.ForeignKey('Match', on_delete=models.CASCADE, related_name='rosters')
    sc2_profile = models.ForeignKey('SC2Profile', on_delete=models.CASCADE, related_name='rosters')
    lane = models.ForeignKey(SC2Profile, on_delete=models.SET_NULL, related_name="lane_rosters", null=True)
    team_number = models.IntegerField()
    position_number = models.IntegerField()
    color = models.CharField(max_length=50, blank=True, default='')
    team = models.ForeignKey('MatchTeam', on_delete=models.SET_NULL, null=True, related_name='rosters')

    # Have these next two to capture static values at the time of the match recording
    elo = models.IntegerField(default=0)
    leaderboard_ranking = models.IntegerField(default=0)

    def __str__(self):
        return "[name={0.sc2_profile.name}, t={0.team_number}, p={0.position_number}".format(self)

    @property
    def stream_info(self) -> typing.Optional[typing.Dict[str, typing.Any]]:

        users = self.sc2_profile.discord_users.all()
        if users is None:
            return
        stream = TwitchStream.objects.filter(active=True, user__in=users).first()
        if stream is None:
            return
        return {
            'profile': self.sc2_profile,
            'stream': stream
        }

    class Meta:
        unique_together = ('match', 'sc2_profile', 'team_number', 'position_number')


class MatchEvent(models.Model):
    """
    Holds important events that have happened in the game. These can be tied to points.

    """
    created = models.DateTimeField(auto_created=True, auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    match = models.ForeignKey('Match', on_delete=models.CASCADE, related_name='events')
    handle = models.ForeignKey('SC2Profile', on_delete=models.CASCADE, related_name='match_events')
    opposing_handle = models.ForeignKey('SC2Profile', on_delete=models.SET_NULL, null=True, related_name="+")
    game_time = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    value = models.IntegerField(default=0)
    key = models.CharField(max_length=100)
    raw = models.TextField(blank=True)
    description = models.TextField()
    points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.key}: {self.handle.name}"

class League(models.Model):
    created = models.DateTimeField(auto_created=True, auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # Each guild can have their own league. A league cannot exist without a discord guild.
    # If a guild is deleted, all league objects are deleted with it.
    # We will preserve matches by setting the league to null on the Match table.
    guild = models.ForeignKey(Guild, on_delete=models.CASCADE, related_name='leagues')

    # Owners can come and go. Retain the league if the owner leaves or allow
    # for a transition period.
    owner = models.ForeignKey(DiscordUser, on_delete=models.SET_NULL, null=True)

    name = models.CharField(max_length=300)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"[id={self.id}, name={self.name}]"

    class Meta:
        unique_together = ('guild', 'name',)

class Season(models.Model):
    created = models.DateTimeField(auto_created=True, auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # Each season must belong to a league. If a league deletes, cascade.
    league = models.ForeignKey('League', on_delete=models.CASCADE, related_name='seasons')

    name = models.CharField(max_length=300)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name
        #return f"[id={self.id}, name={self.name}, league={self.league.name}]"

    class Meta:
        unique_together = ('league', 'name',)
        ordering = ('id',)

class Leaderboard(models.Model):
    created = models.DateTimeField(auto_created=True, auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    profile = models.ForeignKey(SC2Profile, on_delete=models.CASCADE, related_name='leaderboards')
    games = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    elo = models.DecimalField(default=0, decimal_places=3, max_digits=7)
    mode = models.CharField(max_length=50)

    def __str__(self):
        return "{0.profile.name}: {0.mode} / {0.elo} ELO".format(self)


class Unit(models.Model):
    created = models.DateTimeField(auto_created=True, auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    map_name = models.CharField(max_length=100, unique=True, db_index=True)
    real_name = models.CharField(max_length=100, null=True)
    value = models.IntegerField(default=0)
    cost = models.IntegerField(default=0)
    active = models.BooleanField(default=True)

    @property
    def name(self):
        return self.real_name if self.real_name else self.map_name

    def __str__(self):
        return self.name

class UnitStat(models.Model):
    created = models.DateTimeField(auto_created=True, auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="unit_stats")
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='units')
    sc2_profile = models.ForeignKey(SC2Profile, on_delete=models.CASCADE, related_name="unit_stats")
    opposing_profile = models.ForeignKey(SC2Profile, on_delete=models.CASCADE,
                                         related_name="+", null=True)
    made = models.IntegerField(default=0)
    lost = models.IntegerField(default=0)
    killed = models.IntegerField(default=0)

class MatchMessage(WithTimeStamp):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="messages")
    profile = models.ForeignKey(SC2Profile, on_delete=models.CASCADE, related_name="messages")
    game_time = models.FloatField()
    message_type = models.CharField(max_length=100, choices=MESSAGE_TYPES)
    message = models.TextField()

class MatchWinner(WithTimeStamp):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="match_winners")
    profile = models.ForeignKey(SC2Profile, on_delete=models.CASCADE, related_name="wins")
    carried = models.BooleanField(default=False)

class MatchLoser(WithTimeStamp):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="match_losers")
    profile = models.ForeignKey(SC2Profile, on_delete=models.CASCADE, related_name="losses")
    killer = models.ForeignKey(SC2Profile, on_delete=models.SET_NULL, related_name="+", null=True)
    left_game = models.BooleanField()
    game_time = models.FloatField()
    victim_number = models.IntegerField()

class Team(WithTimeStamp):
    name = models.CharField(max_length=300, default='')
    profiles = models.ManyToManyField(SC2Profile)

    def __str__(self):
        """
        If made from an annotation grab the players. Otherwise just use the
        team id.
        Returns
        -------

        """
        if hasattr(self, 'team_players'):
            return self.team_players
        return str(self.id)

class MatchTeam(WithTimeStamp):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    position = models.IntegerField(choices=TEAM_POSITIONS)
    elo_average = models.IntegerField(default=0)

    # I may just be able to do this with queries
    outcome = models.CharField(max_length=50, choices=TEAM_OUTCOMES)
    victim_number = models.IntegerField(default=0)
    def __str__(self):
        if hasattr(self, 'team_players'):
            return "{0}: {1}".format(self.match, self.team_players)
            #   return self.team_players
        return str(self.id)



"""
Twitch Integrations. Keep this here or another app?
"""
class TwitchStream(models.Model):

    # We use a webhook callback UUID to really see who the stream is about.
    # That way when a stream stops, we know the social account its tied to.
    uuid = models.UUIDField()

    # For twitch streams, we link to the SocialAccount which also has the
    # Discord user that its linked to
    social_account = models.ForeignKey(SocialAccount, on_delete=models.CASCADE, related_name='twitch_streams')
    user = models.ForeignKey(DiscordUser, on_delete=models.CASCADE, related_name='twitch_streams')
    username = models.CharField(max_length=300)
    active = models.BooleanField(default=False)
    extra_data = JSONField(default=dict)

    def url(self):
        """
        Builds the twitch stream url
        Returns
        -------
        str URL
        """
        return "https://twitch.tv/{0}".format(self.user_name)






from .stats.models import *