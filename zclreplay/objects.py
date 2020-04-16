import datetime
import re
import typing
from decimal import Decimal
import collections
import logging
from copy import deepcopy
from .units import UNIT_VALUES

log = logging.getLogger(__name__)




class Event(dict):

    def __init__(self, *args, **kwargs):
        super(Event, self).__init__(*args, **kwargs)
        self._event = self.get('_event')

        # The default return value is bytes for quite a few of the units.
        # Encode them to strings for easier parsing.
        for key, value in self.items():
            if isinstance(value, bytes):
                value:bytes
                self[key] = value.decode(encoding='utf-8')

    @property
    def unit(self) -> typing.Optional[str]:
        """Returns the unit name if any"""
        return self.get('m_unitTypeName')

    @property
    def unit_born(self) -> bool:
        return self._event == 'NNet.Replay.Tracker.SUnitBornEvent'

    @property
    def unit_init(self) -> bool:
        return self._event == 'NNet.Replay.Tracker.SUnitInitEvent'

    @property
    def unit_done(self) -> bool:
        return self._event == 'NNet.Replay.Tracker.SUnitDoneEvent'

    @property
    def unit_died(self) -> bool:
        return self._event == 'NNet.Replay.Tracker.SUnitDiedEvent'

    @property
    def stats_update(self) -> bool:
        return self._event == "NNet.Replay.Tracker.SPlayerStatsEvent"

    @property
    def time_event(self) -> bool:
        return self._event == "NNet.Game.SSetSyncLoadingTimeEvent"

    @property
    def player_setup(self) -> bool:
        return self._event == "NNet.Replay.Tracker.SPlayerSetupEvent"

    @property
    def upgrade_event(self) -> bool:
        return self._event == 'NNet.Replay.Tracker.SUpgradeEvent'

    @property
    def unit_owner_transferred(self) -> bool:
        return self._event == 'NNet.Replay.Tracker.SUnitOwnerChangeEvent'

    @property
    def unit_type_changed(self) -> bool:
        return self._event == 'NNet.Replay.Tracker.SUnitTypeChangeEvent'

    @property
    def message_received(self) -> bool:
        return self._event == 'NNet.Game.SChatMessage'

    @property
    def position(self) -> typing.Optional[int]:
        x, y = self.get('m_x'), self.get('m_y')
        if x is None or y is None:
            return
        x = round((x - 20.5) / 10.0)
        y = round((90.0 - y) / 10)
        return x + (round(y * 8.0))

    @property
    def game_time(self):
        game_time = Decimal(self.get('_gameloop', 0))
        game_time = game_time / Decimal("16")   # Trigger update time
        game_time = game_time / Decimal("1.4")  # Map speed Faster
        return str(round(game_time, 4))           # in seconds

    @property
    def formatted_game_time(self):
        return str(datetime.timedelta(seconds=float(self.game_time)))

    @property
    def trackable_unit(self):
        tracked_units = [
            'Bunker',
            'SCV',
            'Nuke',
            'Tank',
        ]
        return any([self.is_unit(u) for u in tracked_units])

    def is_unit(self, unit_name: str, key='m_unitTypeName') -> bool:
        unit = self.get(key)
        encoded = unit_name.encode('utf-8')
        return unit == encoded or unit == unit_name





class Player:

    def __init__(self, player_id: int):
        self.player_id = player_id
        self.user_id = None
        self.name = None
        self.team = None
        self.profile_id = None
        self.slot_id = None
        self.position = None
        self.lane = None
        self.color = None
        self.unit_stats = Stats(self)
        self._upgrades = []
        self.left_game = False
        self.eliminated = False
        self.victim_number = -1
        self.nuke_event = None
        self.all_chats = []
        self.allied_chats = []
        self.winner = False
        self.killer = None
        self.eliminated_at = 0.0
        self.upgrade_totals = {}



    @property
    def is_eliminated(self) -> bool:
        return self.left_game or self.eliminated

    @property
    def has_no_bunkers(self) -> bool:
        bunkers = self.unit_stats.bunkers
        return bunkers['created'] - bunkers.get('cancelled', 0) - bunkers['lost'] == 0



    def add_upgrade(self, event: Event):
        upgrade_name = event['m_upgradeTypeName']
        if upgrade_name.startswith('Reward'):
            return
        count = event['m_count']
        payload = {
            'name': self.name,
            'game_time': event.game_time,
            'total_score': self.unit_stats.total_score,
            upgrade_name: count,
        }
        if len(self._upgrades) == 0:
            self._upgrades.append(payload)
        else:
            payload = deepcopy(self._upgrades[-1])
            if upgrade_name in payload.keys():
                payload[upgrade_name] += count
            else:
                payload[upgrade_name] = count

            payload['game_time'] = event.game_time
            payload['total_score'] = self.unit_stats.total_score
            self._upgrades.append(payload)

    @property
    def upgrades(self):
        """
        Formats it better by sequence
        Returns
        -------

        """
        if len(self._upgrades) == 0:
            return []
        # Find largest one:
        key, length = 0, 0
        for i, o in enumerate(self._upgrades):
            if len(o.keys()) > length:
                key, length = i, len(o.keys())

        largest = self._upgrades[key]

        result = []
        for o in self._upgrades:
            for k in largest.keys():
                if k not in o:
                    o[k] = 0
            result.append(o)
        return result

    def increment_stat(self, stat_object: dict, unit: str, category: str) -> int:
        n = stat_object.get(unit, {}).get(category, 0)
        stat_object[unit][category] = n + 1
        return stat_object[unit][category]

    #@property
    #def winner(self):
    #    return any(p.result == 1 for p in self.team.players)

    @property
    def observer(self):
        return self.position == None or self.team.id == None

    @property
    def partners(self):
        """
        Just in case we ever do other configurations, don't assume one partner.
        :return:
        """
        return [p for p in self.team.players if p.player_id != self.player_id]

    @property
    def feed(self):
        """
        Returns feed data
        Returns
        -------

        """
        container = []
        totals = self.unit_stats.totals
        obj = {}
        for profile in totals.keys():
            award = 0

            units = totals.get(profile, {}).keys()
            for unit in units:
                award += totals[profile][unit].get('killed', 0) * UNIT_VALUES.get(unit, {}).get('award', 0)
            obj[profile.name] = award



        obj = {k:v for k,v in sorted(obj.items(), key=lambda item: item[1])}
        obj['name'] = self.name
        return obj


    @property
    def color_string(self) -> str:
        if self.color is None:
            return ""
        else:
            return ",".join(map(str, self.color))

    def __repr__(self):
        return "Player(name={0.name}, player_id={0.player_id}, team_id={0.team.id}, position={0.position})".format(self)

    def serialize(self):
        lane_id = self.lane.profile_id if self.lane is not None else None
        return {
            'id': self.profile_id,
            'name': self.name,
            'lane_id': lane_id,
            'position': self.position,
            'color': self.color

        }

    def to_dict(self):
        if self.is_observer:
            return {
                self.name: {
                    'handle': self.handle,
                    'player_id': self.player_id,
                    'slot_id': self.slot_id,
                }
            }
        result = {
            self.name: {
                'team_id': self.team_id,
                'handle': self.handle,
                'color': self.color,
                'slot_id': self.slot_id,
                'player_id': self.player_id,
                'position': self.position,
                'result': 'win' if self.result == 1 else 'loss',
                'unit_stats': self.unit_stats.to_dict(),
                'lane_stats': self.lane_units.to_dict(),
                'lane': None if self.lane is None else self.lane.name,
            }
        }

        return result

class Team:
    def __init__(self, team_id: int, players: typing.Optional[typing.List[Player]] = None):
        if players is None:
            players = []
        self.id = team_id
        self.players = players


    def serialize(self):
        return {
            'label': 'Top Left',
            'team_id': self.id,
            'winner': self.winner,
            'profiles': [x.serialize() for x in self.players]
        }

    @property
    def is_eliminated(self):
        return all(p.is_eliminated for p in self.players)

    @property
    def winner(self):
        return any(p.winner for p in self.players)

    @property
    def position(self) -> typing.Optional[int]:
        if len(self.players) == 0:
            return
        pos = self.players[0].position
        if pos in [0,1,8]:
            return 0
        if pos in [2,3,9]:
            return 1
        if pos in [4,5,10]:
            return 2
        if pos in [6,7,11]:
            return 3


    def __repr__(self):
        players = ' & '.join(p.name for p in self.players) or "No Players"
        return "Team(number={0.id}, players={1})".format(self, players)


class TrackedUnits:
    def __init__(self):
        self._tracked = {}

    def add(self, event: Event) -> None:
        key = "{m_unitTagIndex}-{m_unitTagRecycle}".format(**event)
        self._tracked[key] = event

    def fetch(self, event: Event, killer=False) -> typing.Optional[Event]:
        try:
            if killer:
                key = "{m_killerUnitTagIndex}-{m_killerUnitTagRecycle}".format(**event)
            else:
                key = "{m_unitTagIndex}-{m_unitTagRecycle}".format(**event)
            return self._tracked.get(key)
        except KeyError:
            return

    def delete(self, event: Event) -> None:
        key = "{m_unitTagIndex}-{m_unitTagRecycle}".format(**event)
        try:

            del self._tracked[key]
        except KeyError:
            log.warning("Called TrackUnits.delete() on non-existant key")

class MatchEvent:
    def __init__(self, event: Event, key: str, description: str, profile: Player,
                 opposing_profile: Player, player_state: typing.List[Player], points: int = 0, value: int = 0, raw: str = ""):
        self.event = event
        self.key = key
        self.description = description
        self.points = points
        self.value = value
        self.raw = raw
        self.profile = deepcopy(profile)
        self.opposing_profile = deepcopy(opposing_profile)
        self.game_time = event.game_time
        self.player_state = [deepcopy(p) for p in player_state]
        self.total_score = 0 if self.profile is None else self.profile.unit_stats.total_score
        self.minerals_on_hand = 0 if self.profile is None else self.profile.unit_stats.minerals_on_hand

    def serialize(self):
        profile = self.profile.profile_id if isinstance(self.profile, Player) else None
        opposing_profile = self.opposing_profile.profile_id if isinstance(self.opposing_profile, Player) else None
        return {
            'key': self.key,
            'description': self.description,
            'points': self.points,
            'value': self.value,
            'profile_id': profile,
            'oppoing_profile': opposing_profile,
            'game_time': self.game_time,
            'total_score': self.total_score,
            'minerals_on_hand': self.minerals_on_hand,

        }
    def __repr__(self):
        gameloop = self.event['_gameloop']
        player = self.profile.name
        return "MatchEvent(key={0.key}, gameloop={1} player={2}".format(
            self,
            gameloop,
            player
        )

class Snapshot:

    def __init__(self, event: MatchEvent, players: typing.List[Player]):
        self.event = event
        self.game_time = event.game_time
        self.players = deepcopy(players)
        container = []
        for p in players:
            result = {}
            result[p.profile_id] = p.serialize()
            result[p.profile_id]['stats'] = p.unit_stats.serialize()
            container.append(result)
        self.serialized_players = container

    def find_player(self, player_id):
        for p in self.players:
            if p.player_id == player_id:
                return p

    def serialize(self):
        return {
            'event': self.event.serialize(),
            'game_time': self.game_time,
            'players': self.serialized_players
        }





class Stats:
    """
    b'Spectre'
b'SensorTower'
b'NaturalMineralsRed'
b'XelNagaTower'
b'HiveMindEmulator'
b'Ghost'
b'MercReaper'
b'Nuke'
b'SmallInvisiblePylon'
b'WarPig'
b'Reaper'
b'Marine'
b'Bunker'
b'GhostAcademy'
b'SiegeBreakerSieged'
b'SCV'
b'PalletMinerals'
b'LargeInvisiblePylon'
b'MineralCrystal'
b'InvisiblePylon'
b'EngineeringBay'
b'AutoTurret'
b'SupplyDepot'
    """

    def __init__(self, profile: Player = None):
        self.totals: collections.defaultdict[Player, typing.Any] = collections.defaultdict(dict)
        self.profile = profile
        self.stat_event = {}
        self.new_totals: collections.defaultdict[Player, typing.Any] = collections.defaultdict(dict)



    def increment(self, player: typing.Optional[Player], unit: str, category: str) -> int:
        ref = player if player is not None else self.profile
        if self.totals.get(ref) is None:
            self.totals[ref] = collections.defaultdict(dict)

        n = self.totals.get(ref, {}).get(unit, {}).get(category, 0)
        self.totals[ref][unit][category] = n + 1
        return self.totals[ref][unit][category]

    def transfer(self, new_owner: Player, unit: str):
        self.totals[self.profile][unit]['created'] -= 1
        new_owner.unit_stats.increment(new_owner, unit, 'created')

        #new_owner.unit_stats.totals[new_owner][unit]['created'] += 1


    def get_score_from_stats_event(self, event):
        event = event.get('m_stats', {})
        minerals_from_army = event.get('m_scoreValueMineralsKilledArmy', 0)
        workers_killed = event.get('m_scoreValueMineralsKilledEconomy', 0)
        return minerals_from_army + workers_killed

    @property
    def total_score(self):
        """
        Gets the total score from the last recorded stat update
        Returns
        -------

        """
        return self.get_score_from_stats_event(self.stat_event)

    @property
    def army_value(self):
        return self.stat_event.get('m_stats', {}).get('m_scoreValueMineralsUsedCurrentArmy', 0)

    @property
    def tech_value(self):
        return self.stat_event.get('m_stats', {}).get('m_scoreValueMineralsUsedCurrentTechnology', 0)

    @property
    def lost_tech_value(self):
        return self.stat_event.get('m_stats', {}).get('m_scoreValueMineralsLostTechnology', 0)

    @property
    def tech_damage_value(self):
        return self.stat_event.get('m_stats', {}).get('m_scoreValueMineralsKilledTechnology', 0)

    @property
    def minerals_on_hand(self):
        return self.stat_event.get('m_stats', {}).get('m_scoreValueMineralsCurrent', 0)

    @property
    def units(self):
        return list(set(unit for player in self.totals.keys() for unit in self.totals[player].keys()))

    @property
    def bunkers(self):
        return self.filter_and_sum('Bunker')

    @property
    def depots(self):
        return self.filter_and_sum('SupplyDepot')

    @property
    def scvs(self):
        return self.filter_and_sum('SCV')

    @property
    def turrets(self):
        return self.filter_and_sum('AutoTurret')

    @property
    def nukes(self):
        return self.filter_and_sum('Nuke')

    @property
    def towers(self):
        units = ['SensorTower', 'HiveMindEmulator']
        return self.filter_and_sum(units)


    @property
    def biological_stats(self):
        return self.get_biological_stats()

    def get_biological_stats(self, player: typing.Optional[Player] = None):
        result = {'created': 0, 'killed': 0, 'lost': 0}
        units = [
            'Spectre',
            'Reaper',
            'Marine',
            'Ghost',
            'WarPig',
            'MercReaper',

        ]
        for u in units:
            stats = self.filter_and_sum(u)
            result['created'] += stats['created']
            result['killed'] += stats['killed']
            result['lost'] += stats['lost']
        return result

    @property
    def tanks(self):
        return self.filter_and_sum('SiegeBreakerSieged')

    def biological_stats_against_player(self, player: Player):
        against_stats = self.get_biological_stats(player)
        against_stats['created'] = self.biological_stats.get('created', 0)
        return against_stats


    def filter_and_sum(self, unit: str, against: typing.Optional[Player] = None) -> typing.Optional[typing.Dict[str, int]]:
        result = {'created': 0, 'killed': 0, 'lost': 0, 'cancelled': 0}
        predicate = True
        for key in self.totals.keys():
            if against is not None:
                predicate = key.profile_id == against.profile_id
            # This is the player and global state
            for u in self.totals[key]:

                if u == unit and predicate:
                    result['created'] += self.totals[key][u].get('created', 0)
                    result['killed'] += self.totals[key][u].get('killed', 0)
                    result['lost'] += self.totals[key][u].get('lost', 0)
                    result['cancelled'] += self.totals[key][u].get('cancelled', 0)

        return result

    def all(self):
        exclude = [
            'biological_stats', 'tanks', 'depots', 'towers', 'EngineeringBay',
            'XelNagaTower', 'LargeInvisiblePylon', 'SmallInvisiblePylon',
            'GhostAcademy' 'InvisiblePylon',
        ]
        return {k: v for k, v in self.totals.items() if k not in exclude}

    def to_dict(self):
        unit_stats = self.totals
        unit_stats['biological_stats'] = self.biological_stats
        unit_stats['tanks'] = self.tanks
        unit_stats['depots'] = self.depots
        unit_stats['towers'] = self.towers
        return unit_stats


    def serialize(self):
        return self.new_totals
