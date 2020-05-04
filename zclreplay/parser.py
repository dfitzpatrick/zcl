import json
import logging
import typing
import collections
import mpyq
from s2protocol import versions

from zclreplay.errors import NotZCReplay, IncompleteReplay, ReplayParseError
from zclreplay.objects import Event, TrackedUnits, Team, Player, MatchEvent, Snapshot
from datetime import datetime, timezone
import re
from copy import deepcopy
from . import utils


log = logging.getLogger('zclreplays')


TEAM_MAP = {  # position -> team_id
    -1: -1,
    0: 0,
    1: 0,
    2: 1,
    3: 1,
    4: 2,
    5: 2,
    6: 3,
    7: 3,
    8: 0,
    9: 1,
    10: 2,
    11: 3,
}


# Lanes are defined by positions
# key: Position
# value: Lane Position
LANE_POSITION_MAP = {
    0: 7,
    1: 2,
    2: 1,
    3: 4,
    4: 3,
    5: 6,
    6: 5,
    7: 0,

}

def closest_version(n, versions) -> (int, int):
    """
    s2protocol may be missing a particular protocol. Find the closest one two it down-versioned and upversioned.
    Parameters
    ----------
    n
    versions: s2protocol.versions

    Returns
    -------

    """
    seq = list(map(int, re.findall('\\d+', ''.join(versions.list_all()))))
    lst = sorted(seq + [n])
    min_index = lst.index(n) - 1
    max_index = min_index + 2
    return seq[min_index], lst[max_index]


class SerializeEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, Player):
            ignore = ['_replay',]
            return {k:v for k,v in o.__dict__.items() if k not in ignore }

        if isinstance(o, datetime):
            return {'__datetime__': o.replace(microsecond=0).isoformat()}


        return {'__{}__'.format(o.__class__.__name__): o.__dict__}

class Replay:


    @classmethod
    def info(cls, path):
        archive = mpyq.MPQArchive(path)
        hash = archive.__hash__()
        meta = json.loads(
            archive.read_file('replay.gamemetadata.json')
            .decode('utf-8')
        )
        return hash, meta

    def __init__(self, path):
        self.archive = mpyq.MPQArchive(path)
        self.fallback_versions = None
        _header_contents = self.archive.header['user_data_header']['content']
        protocol = versions.latest()
        _header = protocol.decode_replay_header(_header_contents)
        self.base_build = _header['m_version']['m_baseBuild']
        try:
            self.protocol = versions.build(self.base_build)
        except ImportError:
            # fall back version
            next_lower = closest_version(self.base_build, versions)[0]
            log.info(f"Missing Protocol {self.base_build}. Using Next Lower {next_lower}")
            self.protocol = versions.build(next_lower)

        self.fallback_versions = closest_version(self.base_build, versions)
        self._header = _header
        self._events = None
        self._init_data = None
        self._details = None
        self._players = []
        self._teams = None
        self._attribute_events = None
        self._tracker_events = None
        self.match_events = []
        self.snapshots: typing.List[Snapshot] = []
        self.tracked_units = TrackedUnits()
        self._time = None
        self.units = []
        self._message_lookup = {}
        self._message_keys = []
        self.segments = {
            'early': {},
            'three_teams': {},
            'two_teams': {},
            'final': {}
        }
        meta = json.loads(
            self.archive.read_file('replay.gamemetadata.json')
            .decode('utf-8')
        )
        self.meta = meta
        if meta['Title'] not in ['Zone Control CE', 'Zone Control CE Dev']:
            raise NotZCReplay("Not a valid replay for game")
        # Check to see if the replay is complete or not
        if max([p['m_result'] for p in self.details.get('m_playerList', [])]) == 0:
            raise IncompleteReplay("Replay is incomplete")


    def add_match_event(self, event: Event, key, description, points=0, value=0, raw=""):
        from copy import deepcopy
        obj = MatchEvent(
            event=event,
            key=key,
            description=description,
            profile = deepcopy(self.get_player(event.get('m_controlPlayerId'))),
            opposing_profile = deepcopy(self.get_player(event.get('m_killerPlayerId'))),
            player_state = deepcopy(self.players),
            points=points,
            value=value,
            raw=raw
        )
        # Things like a nuke may place the actual owner as a killer. Transfer this to "owner" and delete killer.
        if obj.profile is None and obj.opposing_profile is not None:
            obj.profile = obj.opposing_profile
            obj.opposing_profile = None

        if obj.profile is None:
            log.error(f"No owner for match event {obj.key} on replay id {self.game_id}")
            return
        # Add a snapshot
        self.add_snapshot(obj)
        self.match_events.append(obj)
        log.debug(f"{event.game_time} Added MatchEvent {key} - {description}")

    def add_snapshot(self, event: MatchEvent):
        obj = Snapshot(event=event,  players=self.players)
        self.snapshots.append(obj)

    def parse(self, failed=False):
        """
        Attempt to safely parse a replay in the case of a missing protocol
        Returns
        -------
        None

        Raises
        -------
        ReplayParseError
        """
        a, b = closest_version(self.base_build, versions)

        try:
            self._parse()
        except:
            raise
            if failed:
                msg = f"Missing Protocol {self.base_build}. Failed to parse with {a} and {b}"
                raise ReplayParseError(msg)
            # Maybe some protocol error if one was missing. This had defaulted
            # to the higher one, so try the lower one.
            log.info(f"Parse failed. Trying higher version {b}")
            self.protocol = versions.build(b)
            return self.parse(failed=True)

    @property
    def game_length(self):
        return self.segments['final'].get('game_time', 0)

    @property
    def game_id(self):
        for e in self.game_events:
            if e.get('_event') == 'NNet.Game.SSetSyncLoadingTimeEvent':
                return e.get('m_syncTime')


    def pid_to_positions(self) -> typing.Dict[int, typing.Optional[int]]:
        """
        Legacy to make sure that older models in the database work.
        We typically view bunker placements in ZC with an index that represents
        each build-square on the map. This index starts in the Top Left (GhostAcademy)
        at number 0 and increases by 1 each square to the right and down each row.

        In our database, we refer to Player Positions. This is legacy in how
        we assigned them and how we track who is in what "lane".

        We use starting bunker positions to get the "Position" of a player.
        We cannot rely on lobby state, and due to the map randomizing positions,
        this is the best way to reliably get them.

        BUNKER STARTING INDEXES            DATABASE POSITIONS

        ---[1]-----------[6]--          ----[1]-----------[2]--
        [8][9]         [14][15]          [0][8]          [9][3]



        [48][49]        [54][55]          [7][11]        [10][4]
        ---[57]--------[62]----         ----[6]----------[5]----

        We'll cycle over all the starting bunker spawns and return a map that
        has player_id -> position. We do it all at once so we don't need to
        iterate the object multiple times.

        None will be assigned for any route thats not found.

        Returns
        -------
        Dict[int, int] a mapping of playerId -> position
        """
        mapping = {
            1: 1,
            6: 2,
            8: 0,
            9: 8,
            14: 9,
            15: 3,
            48: 7,
            49: 11,
            54: 10,
            55: 4,
            57: 6,
            62: 5,
        }
        pid_map = {}
        for e in self.tracker_events:
            if e['_gameloop'] > 0:
                break
            if e.unit_born and e.unit == 'Bunker':
                pid_map[e['m_controlPlayerId']] = mapping.get(e.position)
        return pid_map



    def get_player(self, id: typing.Optional[int], lookup='player_id') -> typing.Optional[Player]:
        for p in self.players:
            if hasattr(p, lookup):
                if getattr(p, lookup)== id:
                    return p
    @property
    def attribute_events(self):
        if self._attribute_events is None:
            contents = self.archive.read_file('replay.attributes.events')
            self._attribute_events = self.protocol.decode_replay_attributes_events(contents)
        return self._attribute_events

    @property
    def tracker_events(self):
        if self._tracker_events is None:
            contents = self.archive.read_file('replay.tracker.events')
            for event in self.protocol.decode_replay_tracker_events(contents):
                yield Event(**event)
        #return self._tracker_events
    @property
    def init_data(self):
        if self._init_data is None:
            contents = self.archive.read_file('replay.initData')
            self._init_data = self.protocol.decode_replay_initdata(contents)
        return self._init_data

    @property
    def details(self):
        if self._details is None:
            contents = self.archive.read_file('replay.details')
            self._details = self.protocol.decode_replay_details(contents)
        return self._details

    @property
    def game_events(self):
        if self._events is None:
            contents = self.archive.read_file('replay.game.events')
            for event in self.protocol.decode_replay_game_events(contents):
                event = Event(**event)
                yield event

        return self._events

    @property
    def message_events(self):
        contents = self.archive.read_file('replay.message.events')
        for event in self.protocol.decode_replay_message_events(contents):
            yield Event(**event)


    @property
    def observers(self):
        return [p for p in self._players if p.observer]


    @property
    def game_time(self) -> datetime:
        if self._time is None:
            # Just get the first one to make this faster:
            for event in self.game_events:
                if event.time_event:
                    self._time = datetime.fromtimestamp(event['m_syncTime'], tz=timezone.utc)
                    break


        return self._time

    def user_id(self, working_set_slot_id: int):
        """
        Finds the relationship between Working Slot ID and retrieves the User ID
        Parameters
        ----------
        working_slot_id

        Returns
        -------
        """
        for slot in self.init_data['m_syncLobbyState']['m_lobbyState']['m_slots']:
            if slot['m_workingSetSlotId'] == working_set_slot_id:
                return slot['m_userId']


    def create_uid_pid_mapping(self):
        """
        Make this a bit faster and terminate when we have enough
        Returns
        -------

        """
        # Set this flag to true when we start hitting the PlayerSetupEvents
        last_index = None
        uid_pid_mapping = {}
        for index, event in enumerate(self.tracker_events):
            if event.player_setup:
                last_index = index
                uid_pid_mapping[event['m_userId']] = event['m_playerId']
            if last_index is not None and last_index != index:
                # A new Non Player setup event. We've looped through all.
                # break out so we don't consume the entire generator.
                break
        return uid_pid_mapping


    def _load_objects(self):
        """
        Relationships are hard work...
        In order to get Player Ids from the game, we have to dig through a
        couple different events. We cannot rely on lobby state or slot numbers.

        Compounding the problem, we have to jump through quite a bit of
        relationships to get the holy grail of a playerID that is found in all
        game_events.


        - To get player names  etc, we need to look at the "details" of the replay,
            specifically at m_playerList. The only credible id in this section is
            m_workingSetSlotId. This is a problem because every event in
            game_events is tracked by m_controlPlayerId. We need to find a
            relationship.

        - Player ID is found in "NNet.Replay.Tracker.SPlayerSetupEvent"
            inside of tracker_events. The only relationship avaiable is a
            USER ID field m_userId

        - User ID can be found in init_data and has the relationship to  m_slots

        Therefore:
            - Create a mapping of m_workingSetSlotId -> m_userID
            - Create a mapping of m_userID -> m_controlPlayerId

        We also create mappings to get database level "positions" of each spawn.
        This is an index so we know exactly where they are in case we want to
        build future relationships. See the pid_to_positions() function for more
        information.
        Returns
        -------
        None
        """
        # Create a lookup for all messageable events so we can get an accurate
        # snapshot during each segment we want to find.
        for msg in self.message_events:
            if msg['_event'] == 'NNet.Game.SChatMessage':
                loop = msg['_gameloop']
                self._message_lookup[loop] = msg
        self._message_keys = list(self._message_lookup.keys())



        player_container = {}
        team_container = {}
        name_pattern = re.compile(r'&lt;.*<sp/>')

        # TODO: Make sacrificial offering of first-born to make player ids easier
        slot_uid_mapping = {
            e['m_workingSetSlotId']: e['m_userId']
            for e in self.init_data['m_syncLobbyState']['m_lobbyState']['m_slots']
        }
        uid_pid_mapping = self.create_uid_pid_mapping()
        pid_position_mapping = self.pid_to_positions()
        position_pid_mapping = {v:k for k,v in pid_position_mapping.items()}

        for p in self.details.get('m_playerList', []):
            profile_id = "{m_region}-S2-{m_realm}-{m_id}".format(**p['m_toon'])
            color = (
                p['m_color']['m_r'],
                p['m_color']['m_g'],
                p['m_color']['m_b'],
            )
            name = p['m_name'].decode('utf-8')
            slot_id = p['m_workingSetSlotId']
            user_id = slot_uid_mapping.get(slot_id)
            player_id = uid_pid_mapping.get(
                slot_uid_mapping.get(slot_id)
            )
            if player_id is None:
                log.error(f"Could not map {p} playerId from userId")
            position = pid_position_mapping.get(player_id)

            team_id = TEAM_MAP.get(position)
            lane_pos = LANE_POSITION_MAP.get(position)
            lane_player_id = position_pid_mapping.get(lane_pos)

            # Create a team object if one doesn't exist
            team = team_container.get(team_id) or Team(team_id)
            team_container[team_id] = team

            # Fetch to see if the player has already been made, or make one.
            player = player_container.get(player_id) or Player(player_id)
            lane_player = player_container.get(lane_player_id)


            # Load attributes to player
            player.name = re.sub(name_pattern, '', name)
            player.team = team
            player.profile_id = profile_id
            player.slot_id = slot_id
            player.user_id = user_id
            player.position = position
            player.result = p['m_result']
            player.color = color
            if lane_player:
                player.lane = lane_player
                lane_player.lane = player

            team.players.append(player)
            player_container[player_id] = player
        self._players = list(player_container.values())
        self._teams = list(team_container.values())


    @property
    def players(self) -> typing.List[Player]:
        if not self._players:
            self._load_objects()
        return [p for p in self._players if not p.observer]

    @property
    def player_dead_count(self):
        return sum(1 for p in self.players if p.left_game or p.eliminated)

    @property
    def teams(self) -> typing.Optional[typing.List[Team]]:
        if self._teams is None:
            self._load_objects()
        return [t for t in self._teams if t.position is not None]

    def winning_team(self) -> typing.Optional[int]:
        for t in self.teams:
            if t.winner:
                return t


    def is_draw(self):
        return self.winning_team() is None

    @property
    def teams_remaining(self) -> int:
        return sum(1 for t in self.teams if not t.is_eliminated)


    def eliminate_player(self, event, player: Player, killer: typing.Optional[Player]):
        player.victim_number = self.player_dead_count + 1

        player.left_game = killer is None
        player.eliminated = not player.left_game
        player.killer = killer
        player.eliminated_at = event.game_time

        key = "player_leave"
        description = f"{player.name} has left the game."
        if player.eliminated:
            key = "player_died"
            description = f"{player.name} was eliminated by {killer.name}"

        if killer == player:
            key = "player_suicide"
            description = f"{player.name} cancels their last bunker."
        if not player.winner:
            # They already won. Suppress any match event from them leaving.
            self.add_match_event(event, key, description)
        # Check for a win condition and set it on the player class
        remaining_teams = [t for t in self.teams if not t.is_eliminated]
        if len(remaining_teams) == 1:
            for p in remaining_teams[0].players:
                if not p.left_game:
                    p.winner = True

        log.debug(description)

    def _parse_transferred(self, event):
        """
        Called when a transferred event is intercepted by the parser.
        This is typically done when a player leaves the game. There are some
        housekeeping items that we need to do here.

        1. Transfer the created count from the old player to the new player
        2. Revise the initial event in TrackedUnits to store the new owner.
        3. Check for a loss condition on a player (or win condition).
        Parameters
        ----------
        event

        Returns
        -------
        None
        """
        xfer_unit_init = self.tracked_units.fetch(event)
        unit_name = xfer_unit_init['m_unitTypeName']
        player = self.get_player(xfer_unit_init['m_controlPlayerId'])
        if player is None:
            # 5/3/2020 fix
            # Replays are failing with Attribute Error: 'NoneType' has no
            # attribute 'unit_stats'. It looks like this could be failing for
            # some reason. Applicable match ids are
            # │['1573851163', '1572709967', '1585779902', '1585769287', '1585765048  File "/home/zcl/zclreplay/streamparser.py", line 354, in _parse    │', '1573851163', '1560719297', '1560717812', '1585765048', '15857581    self._parse_transferred(event)                                   │85', '1585757576', '1585756364', '1585755051', '1585753845', '158575  File "/home/zcl/zclreplay/parser.py", line 561, in _parse_transferr│3155', '1585748819', '1585747386', '1581196844', '1582656342', '1573ed                                                                   │322055', '1572709967', '1569620215', '1569515687', '1569514917', '15    player.unit_stats.transfer(new_owner, unit_name)                 │69514268', '1569513497', '1567870364', '1567870058', '1566122629', 'AttributeError: 'NoneType' object has no attribute 'unit_stats'      │1554060998', '1585755051', '1568997137', '1569620215', '1569515687',~                                                                    │ '1569514268', '1569513497', '1551303756', '1585765048', '1585734882~']
            log.warning(f'Player is None for Unit Transfer - {xfer_unit_init}')
            self.tracked_units.add(xfer_unit_init)
            return
        new_owner = self.get_player(event['m_controlPlayerId'])

        player.unit_stats.transfer(new_owner, unit_name)
        xfer_unit_init['m_controlPlayerId'] = new_owner.player_id
        xfer_unit_init['m_upkeepPlayerId'] = new_owner.player_id
        self.tracked_units.add(xfer_unit_init)

        if player.has_no_bunkers and not player.is_eliminated:
            self.eliminate_player(event, player, None)

        log.debug(f'Transferred {unit_name} from {player.name} to {new_owner.name}')

    def _parse_initialize_unit(self, event):
        """
        This tracks when a new unit starts building. Initialized means that
        construction has begun, but the unit may not be available if it requires
        building time.

        As of this moment, I don't track cancels. We will need to refactor this
        in case I want to.

        This is responsibile for dispatching different match events that are
        generally found on our stream alerts. Its a good indication of how the
        game is progressing for the match details web page.
        Parameters
        ----------
        event

        Returns
        -------

        """
        player = self.get_player(event['m_controlPlayerId'])
        if player is None:
            # Commonly mineral crystal spawns that do not have a player attached.
            log.debug(f"Init event passed missing PlayerId. {event.unit} not tracked.")
            return

        # TODO: We don't track cancels here. This technically isn't created yet.
        # TODO: But it gets overriden by the unit_born event anyhow.
        player.unit_stats.increment(player, event.unit, 'created')

        # Fire off a match event for the different Unit Types
        if event.is_unit('Bunker') and event['_gameloop'] != 0:
            bunker_type = utils.zc_bunker_type(event.position)
            description = f"{player.name} Builds a {bunker_type} Bunker"
            self.add_match_event(event, 'bunker_started', description)

        if event.is_unit('Tank'):
            description = f"{player.name} Builds a Tank"
            self.add_match_event(event, 'tank_started', description)


    def _parse_stats_update(self, event):
        """
        This is called when a new Stat Update is made. A lot of the time series
        keeping functions for total score etc are managed by tracking state of
        the last stats update since this isn't called in every game loop. Those
        events will reference the last received Stats Update.
        Parameters
        ----------
        event

        Returns
        -------
        None
        """
        player = self.get_player(event['m_playerId'])
        if player is None:
            return

        # Check any deferred states to dispatch events.
        # 1. Nuke. Did the player nuke? Get the updated score.
        if player.nuke_event is not None:
            new_score = player.unit_stats.get_score_from_stats_event(event)
            old_score = player.unit_stats.total_score
            value = new_score - old_score
            description = f"{player.name} nukes for a value of {value}"
            self.add_match_event(player.nuke_event, 'player_nuked', description, value=value)
            player.nuke_event = None

        player.unit_stats.stat_event = event



    def _parse_upgrade(self, event):
        """
        Responsible for keeping track of any upgrades that happen in game.
        These upgrades are tracked on the player class with add_upgrade()
        Parameters
        ----------
        event

        Returns
        -------
        None
        """
        player = self.get_player(event['m_playerId'])
        # These can fire for observers based on Reward Skins.
        if player is not None:
            player.add_upgrade(event)

    def _parse_unit_died(self, event: Event, init_event: Event):
        """
        Responsible for keeping track of unit tallies and tracking when a unit
        dies. There are some odd edge cases here that I haven't been able to
        prove. For example, I thought that mineral collection was here since
        they are a unit spawn. But I cannot see how they are collected in the
        raw tracker events.

        Housekeeping events that we need to do here:
        1. Adjust the Unit Stats
        2. Check for eliminations
        3. Dispatch any match events.

        Parameters
        ----------
        event

        Returns
        -------
        None
        """
        owner = self.get_player(init_event['m_controlPlayerId'])
        killer = self.get_player(event.get('m_killerPlayerId'))

        if owner is None:
            # Normally mineral spawns. They don't have a owner or killer.
            # Re fetch with a flag to get the reference to the owner's unit.
            log.debug(f"{init_event.unit} Received None as Owner: {event}")


        elif killer is not None:
            # 'killer' is none for things like LargeInvisiblePylons,
            # Mineral Crystals (Not sure how to find who collects them)
            # and de-spawning objects like buildings/units from the map when.
            # a player is eliminated.
            if killer == owner:
                # Cancelled unit from init_unit. These are treated just like
                # deaths in s2protocol. We must track it. Unfortunately, no good
                # way to tell which player "caused" them to hit cancel.
                owner.unit_stats.increment(owner, init_event.unit, 'cancelled')
            else:
                owner.unit_stats.increment(killer, init_event.unit, 'lost')
                killer.unit_stats.increment(owner, init_event.unit, 'killed')
        else:
            # This player more than likely despawned and "left the game" without
            # a team mate to transfer units to. Decrement and a win check is below.
            owner.unit_stats.increment(owner, init_event.unit, 'lost')
            log.debug(f"{owner.name}'s {init_event.unit} Received None as killer")


        if init_event.is_unit('Bunker'):
            # A killer is None if the player left or the map despawned their units.
            if killer is not None:
                # Dispatch either 'bunker_killed' or 'bunker_cancelled'
                bunker_type = utils.zc_bunker_type(event.position)
                if killer == owner:
                    description = f"{owner.name} cancels their {bunker_type} bunker"
                    self.add_match_event(event, 'bunker_cancelled', description)
                else:
                    if owner is not None:
                        description = f"{killer.name} destroys {owner.name}'s {bunker_type} bunker."
                        self.add_match_event(event, 'bunker_killed', description)
                    else:
                        # This shouldn't happen. Generally a Nuke Kill on a bunker.
                        log.debug(f"Owner was None for Bunker Kill for {killer.name} at {event.game_time}")
            # We put this into a function so we don't need to worry about order
            # of statements.
            self._check_for_elimination(event, owner, killer)



        if init_event.is_unit('Nuke'):
            # TODO: This seems redundent. Code issue from refactor?
            # owner.unit_stats.increment(owner, init_event.unit, 'lost')
            # In order to get the score, we pass in an attribute to the Player class
            # That they just used a nuke. This gets evaluated in the stat_update class
            # that then dispatches the event. It then resets the state.
            # We have to check that the "Nuke" didn't die to an owner that was eliminated.
            # That just means they forfeited the nuke.
            if owner is not None and not owner.eliminated:
                owner.nuke_event = event
            else:
                log.debug(f"Owner is None for {init_event}")

        # Remove this unit from the tracking pool now that we are all done.
        self.tracked_units.delete(event)

    def _check_for_elimination(self, event, owner: Player, killer: typing.Optional[Player]):
        """
        Helper function from when a bunker is destroyed to check if a player was
        eliminated or left the game.

        There are four scenarios here

        1. The player's bunker died by a player and they have no more bunkers.
        2. The player's bunker was cancelled and they died (owner == killer)
        3. The player left the game without a teammate where units transfer.
        4. The map despawned the player, either because they
            a. Left the game
            b. Were the winners and the map despawned them.

        Parameters
        ----------
        owner
        killer

        Returns
        -------

        """
        if owner.winner:
            # The map is de-spawning them at game end. ignore.
            return
        if owner.has_no_bunkers:
            self.eliminate_player(event, owner, killer)



    def _parse_chat_messages(self, event: Event):
        """
        Parses any chat message event that comes through. We capture stats mainly
        on the number of all chats that go through. We wont' fire off events
        necessarily for allied chats, although it'll be loaded into the Profile
        object.

        This function acts differently since it is seperate from the main tracker
        events iteration. It's relatively smaller so we load it into memory by
        gameloop as a key. This function will get called and we'll track if the
        tracker loop is greater than the next expected loop from this one.
        Returns
        -------

        """
        try:
            next_id = self._message_keys[0]
        except IndexError:
            return

        if event['_gameloop'] < next_id:
            return

        # Load the new event we need
        event = self._message_lookup[next_id]

        recipient_id = event['m_recipient']
        owner_id = event['_userid']['m_userId']
        chat_type = "All Chat" if recipient_id == 0 else "Allied Chat"
        owner = self.get_player(owner_id, 'user_id')
        recipient = self.get_player(recipient_id, 'user_id')
        if owner is not None:
            # Don't log anything for observers.
            payload = {
                'recipient': recipient,
                'game_time': event.game_time,
                'message': event['m_string']
            }
            if recipient is None:
                owner.all_chats.append(payload)
            else:
                owner.allied_chats.append(payload)
        self._message_keys.pop(0)

    def _parse_check_for_segments(self, event: Event):

        # Check for "Early Segment"
        if len(self.segments['early']) == 0 and float(event.game_time) > 480:  # 8m
            self.segments['early']['game_time'] = event.game_time
            self.segments['early']['players'] = deepcopy(self.players)
            self.segments['early']['valid'] = True

        if len(self.segments['three_teams']) == 0 and self.teams_remaining <= 3:
            self.segments['three_teams']['game_time'] = event.game_time
            self.segments['three_teams']['players'] = deepcopy(self.players)
            # Check if this is a valid measurement
            self.segments['three_teams']['valid'] = len(self.teams) > 3

        if len(self.segments['two_teams']) == 0 and self.teams_remaining <= 2:
            self.segments['two_teams']['game_time'] = event.game_time
            self.segments['two_teams']['players'] = deepcopy(self.players)
            # Check if this is a valid measurement
            self.segments['two_teams']['valid'] = len(self.teams) > 2

        if len(self.segments['final']) == 0 and self.teams_remaining <= 1:
            self.segments['final']['game_time'] = event.game_time
            self.segments['final']['players'] = deepcopy(self.players)
            # Check if this is a valid measurement
            self.segments['final']['valid'] = len(self.teams) > 1

            # Fulfill Early if not done
            if len(self.segments['early']) == 0:
                self.segments['early']['game_time'] = event.game_time
                self.segments['early']['players'] = deepcopy(self.players)
                self.segments['early']['valid'] = False



    def _segment_check_team(self, event, key, target) -> bool:
        eliminated_teams = sum(1 for t in self.teams if t.is_eliminated)
        if len(self.teams) - eliminated_teams == target:
            self.segments[key]['game_time'] = event.game_time
            self.segments[key]['players'] = deepcopy(self.players)
            return True
        return False

    def _parse(self):
        i = 0
        log.info(f"{self.game_id} - Parsing Game")
        self.units = []
        for event in self.tracker_events:
            self._parse_chat_messages(event)
            init_event = self.tracked_units.fetch(event)



            #if event.unit_type_changed:
            #    utype = event['m_unitTypeName']
            #    unit = self.tracked_units.fetch(event)
            #    if unit.is_unit('SupplyDepot'):
            #        log.critical(f" {utype} on {unit}")

            if event.unit_owner_transferred:
                self._parse_transferred(event)

            if event.stats_update:
                self._parse_stats_update(event)

            if event.upgrade_event:
                self._parse_upgrade(event)

            if event.unit_init or event.unit_born:
                self.tracked_units.add(event)
                self._parse_initialize_unit(event)

            if event.unit_died and init_event is not None:
                self._parse_unit_died(event, init_event)

            self._parse_check_for_segments(event)
        log.info(f"{self.game_id} - Parsing Complete")

    def get_details(self):
        test = {
            'id': self.game_id,
            'match_date': self.game_time.isoformat(),
            'snapshots': [s.serialize() for s in self.snapshots]
        }
        return test

    def to_dict(self):
        result = {
            'game_id': self.game_id,
            'is_draw': self.is_draw(),
            'players': {},
            'observers': {}
        }
        for p in self.players:
            if p not in self.observers:
                result['players'].update(p.to_dict())
            else:
                result['observers'].update(p.to_dict())
        return result

    def unit_stats(self):
        def find_owner_stats(data: typing.List[typing.Dict[str,str]],
                             profile_id: str) -> typing.Dict[str, str]:
            pass

        container = []
        for p in self.players:
            owner_created = {}
            obj = {
                'id': p.profile_id,
                'name': p.name,
                'data': [],
            }
            for sub_player in p.unit_stats.totals.keys():
                o = p.unit_stats.totals[sub_player]

                player_stat = {
                    'id': sub_player.profile_id,
                    'name':  sub_player.name,
                    'units': []
                }
                for unit in o.keys():
                    uo = o[unit]
                    if sub_player.profile_id == p.profile_id:
                        owner_created[unit] = uo.get('created', 0)
                    # A id exists for the same player where all creations are.
                    player_stat['units'].append({
                        'name': unit,
                        'created': uo.get('created',0) + owner_created.get(unit, 0),
                        'lost': uo.get('lost', 0),
                        'killed': uo.get('killed', 0),
                    })
                if p.profile_id != sub_player.profile_id:
                    obj['data'].append(player_stat)
            container.append(obj)
        return container
