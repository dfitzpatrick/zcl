from django.db import models

from api.models import WithTimeStamp, Match, SC2Profile


class GameUnit(WithTimeStamp):

    base_name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100, null=True)
    value = models.IntegerField(default=0)
    cost = models.IntegerField(default=0)
    active = models.BooleanField(default=True)

    @property
    def name(self):
        return self.real_name if self.real_name else self.map_name

    def __str__(self):
        return self.name


class GameUnitStat(WithTimeStamp):

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='game_unit_stats')
    profile = models.ForeignKey(SC2Profile, on_delete=models.CASCADE, related_name="game_unit_stats")
    opposing_profile = models.ForeignKey(SC2Profile, on_delete=models.CASCADE,
                                         related_name="+", null=True)
    made = models.IntegerField(default=0)
    lost = models.IntegerField(default=0)
    killed = models.IntegerField(default=0)


class GameEventName(WithTimeStamp):
    id = models.CharField(max_length=50, unique=True, primary_key=True)
    title = models.CharField(max_length=200)


class GameEvent(WithTimeStamp):
    key = models.ForeignKey(GameEventName, on_delete=models.CASCADE)
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='game_events')
    profile = models.ForeignKey(SC2Profile, on_delete=models.SET_NULL, null=True, related_name='game_events')
    opposing_profile = models.ForeignKey(SC2Profile, on_delete=models.SET_NULL, null=True, related_name="+")
    game_time = models.FloatField(max_length=20)
    description = models.CharField(max_length=500)
    total_score = models.IntegerField()
    minerals_on_hand = models.IntegerField()
    value = models.IntegerField(default=0)

    def __str__(self):
        return str(self.id) + " " + self.description + " " + str(self.game_time)


    class Meta:
        unique_together = ('key', 'match', 'profile', 'game_time')


class ChartPoints(WithTimeStamp):
    # Not sure if I should offload this into S3 or serve locally.
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='+')
    profile = models.ForeignKey(SC2Profile, on_delete=models.CASCADE, related_name='+')
    game_event = models.ForeignKey(GameEvent, on_delete=models.CASCADE, related_name='chart_points')
    total_score = models.IntegerField()
    minerals_on_hand = models.IntegerField()



class Segment(WithTimeStamp):
    measure = models.CharField(max_length=100)
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="segments")
    game_time = models.FloatField()
    valid = models.BooleanField()



class SegmentProfileItem(WithTimeStamp):
    segment = models.ForeignKey(Segment, on_delete=models.CASCADE, related_name="profiles")
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="match")
    profile = models.ForeignKey(SC2Profile, on_delete=models.CASCADE, related_name="+")
    lane = models.ForeignKey(SC2Profile, on_delete=models.SET_NULL, related_name="+", null=True)
    left_game = models.BooleanField(default=False)
    eliminated = models.BooleanField(default=False)
    eliminated_by = models.ForeignKey(SC2Profile, on_delete=models.SET_NULL, null=True)

    total_score = models.IntegerField(default=0)
    minerals_on_hand = models.IntegerField(default=0) # m_scoreValueMineralsCurrent
    army_value = models.IntegerField(default=0) # m_scoreValueMineralsUsedCurrentArmy
    tech_value = models.IntegerField(default=0) # m_scoreValueMineralsUsedCurrentTechnology
    lost_tech_value = models.IntegerField(default=0) # m_scoreValueMineralsLostTechnology
    tech_damage_value = models.IntegerField(default=0) # m_scoreValueMineralsKilledTechnology





class SegmentUnitStat(WithTimeStamp):
    segment_profile = models.ForeignKey(SegmentProfileItem, on_delete=models.CASCADE, related_name="unit_stats")

    unit = models.ForeignKey('Unit', on_delete=models.CASCADE)
    segment = models.ForeignKey(Segment, on_delete=models.CASCADE, related_name="+")

    created = models.IntegerField(default=0)
    lost = models.IntegerField(default=0)
    killed = models.IntegerField(default=0)
    cancelled = models.IntegerField(default=0)





