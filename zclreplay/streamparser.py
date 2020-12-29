from . import Replay, utils
from .objects import MatchEvent, Event, Player, StreamItem, SegmentEvent, UpgradeEvent, MessageEvent
import logging
import typing
from time import sleep


log = logging.getLogger('zclreplay.streamparser')



class StreamParser(Replay):

    def __init__(self, path):
        super(StreamParser, self).__init__(path)
        self._load_objects(load_messages=False)
        self._container = []
        self.stream_game_length = 0
        self.stream_segments = {
            'early': None,
            'three_teams': None,
            'two_teams': None,
            'final': None,
        }
        self._load_objects()

    def __iter__(self):
        return iter(self.parse())

    def add_match_event(self, event: Event, key, description, points=0, value=0, raw=""):

        obj = MatchEvent(
            event=event,
            key=key,
            description=description,
            profile = self.get_player(event.get('m_controlPlayerId')),
            opposing_profile = self.get_player(event.get('m_killerPlayerId')),
            player_state = self.players,
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
        #self.add_snapshot(obj)
        log.debug(f"{event.game_time} Yielding MatchEvent {key} - {description}")
        return obj





    def _parse_initialize_unit(self, event):
        player = self.get_player(event['m_controlPlayerId'])
        if player is None:
            # Commonly mineral crystal spawns that do not have a player attached.
            log.debug(f"Init event passed missing PlayerId. {event.unit} not tracked.")
            log.debug(event)
            return

        # TODO: We don't track cancels here. This technically isn't created yet.
        # TODO: But it gets overriden by the unit_born event anyhow.
        player.unit_stats.increment(player, event.unit, 'created')

        # Fire off a match event for the different Unit Types
        if event.is_unit('Bunker') and event['_gameloop'] != 0:
            bunker_type = utils.zc_bunker_type(event.position)
            description = f"{player.name} Builds a {bunker_type} Bunker"
            # TODO: Stream event
            return self.add_match_event(event, 'bunker_started', description)

        if event.is_unit('Tank'):
            description = f"{player.name} Builds a Tank"
            # TODO: Stream event
            return self.add_match_event(event, 'tank_started', description)



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
        result = None
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

            # TODO: Send event
            result = self.add_match_event(player.nuke_event, 'player_nuked', description, value=value)
            player.nuke_event = None

        player.unit_stats.stat_event = event
        return result

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
        result = None
        player = self.get_player(event['m_playerId'])
        # These can fire for observers based on Reward Skins.
        if player is not None:
            upgrade_name = event['m_upgradeTypeName']
            count = event['m_count']
            if upgrade_name.startswith('Reward'):
                return
            new_count = player.upgrade_totals.get(upgrade_name, 0) + count
            player.upgrade_totals[upgrade_name] = new_count
            result = UpgradeEvent()
        return result


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

        We need to test for quite a few different conditions here that are modeled
        by the data

        What if the owner is None?
        - Mineral spawns... ignore
        What if the killer is none?
        - Player left the game. Count as units lost, but none killed



        Parameters
        ----------
        event

        Returns
        -------
        None
        """
        owner = self.get_player(init_event['m_controlPlayerId'])
        killer = self.get_player(event.get('m_killerPlayerId'))
        result = []
        tank = False
        self.tracked_units.delete(event)

        if owner is None:
            # Normally mineral spawns. They don't have a owner or killer.
            # Re fetch with a flag to get the reference to the owner's unit.
            log.debug(f"{init_event.unit} Received None as Owner: {event} Possible Mineral")
        elif killer is None:
            # This is caused by either the player leaving or the player's bunker being eliminated
            # and an automatic despawn.
            # Player eliminated -> Find the killer and give them credit as well
            # If the player left, make sure to only increment lost if the game is not over.
            if not owner.winner:
                log.debug(f"{owner.name} NO KILLER {init_event.unit}  Winner: {owner.winner} INCREMENT LOST")
                owner.unit_stats.increment(owner, init_event.unit, 'lost')

            if owner.is_eliminated and owner.killer is not None and owner.killer != owner:
                log.debug(f"{owner.name} Eliminated By {owner.killer.name} Despawn {init_event.unit}")
                # We increased units lost from the check above already. Just adjust the killer.
                owner.killer.unit_stats.increment(owner, init_event.unit, 'killed')


        elif killer == owner:
            # Cancelled unit from init_unit. These are treated just like
            # deaths in s2protocol. We must track it. Unfortunately, no good
            # way to tell which player "caused" them to hit cancel.
            owner.unit_stats.increment(owner, init_event.unit, 'cancelled')
        else:
            # Normal unit died. Tally up
            if tank:
                log.debug(f"Calling increment on both owner/killer for '{init_event.unit}'")
            owner.unit_stats.increment(killer, init_event.unit, 'lost')
            killer.unit_stats.increment(owner, init_event.unit, 'killed')


        if init_event.is_unit('Bunker'):
            # A killer is None if the player left or the map despawned their units.
            if killer is not None:
                # Dispatch either 'bunker_killed' or 'bunker_cancelled'
                bunker_type = utils.zc_bunker_type(event.position)
                if killer == owner:
                    description = f"{owner.name} cancels their {bunker_type} bunker"
                    result.append(self.add_match_event(event, 'bunker_cancelled', description))
                else:
                    if owner is not None:
                        description = f"{killer.name} destroys {owner.name}'s {bunker_type} bunker."
                        result.append(self.add_match_event(event, 'bunker_killed', description))
                    else:
                        # This shouldn't happen. Generally a Nuke Kill on a bunker.
                        log.debug(f"Owner was None for Bunker Kill for {killer.name} at {event.game_time}")
            # We put this into a function so we don't need to worry about order
            # of statements.
            result.append(self._check_for_elimination(event, owner, killer))




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
        #self.tracked_units.delete(event)
        return [r for r in result if r is not None]

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
        result = None
        if owner is None:
            # Some type of map despawn?
            return

        if owner.winner:
            # The map is de-spawning them at game end. ignore.
            return
        if owner.has_no_bunkers:
            result = self.eliminate_player(event, owner, killer)
        return result

    def eliminate_player(self, event, player: Player, killer: typing.Optional[Player]):
        result = None
        player.victim_number = self.player_dead_count + 1

        player.left_game = killer is None
        player.eliminated = not player.left_game
        player.killer = killer
        player.eliminated_at = event.game_time
        if player.team.is_eliminated:
            player.team.victim_number = self.team_dead_count

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
            result = self.add_match_event(event, key, description)
        # Check for a win condition and set it on the player class
        remaining_teams = [t for t in self.teams if not t.is_eliminated]
        if len(remaining_teams) == 1:
            for p in remaining_teams[0].players:
                if not p.left_game:
                    p.winner = True

        log.debug(description)
        return result


    def _stream_segments(self, stream_item):
        event = stream_item.event
        state = stream_item.state
        result = []
        # Check for "Early Segment"
        if self.stream_segments['early'] is None and float(event.game_time) > 480:  # 8m
            item = StreamItem(event, state=self, payload=SegmentEvent(key='early', valid=True))
            result.append(item)
            self.stream_segments['early'] = item



        if self.stream_segments['three_teams'] is None and state.teams_remaining <= 3:
            # Check if this is a valid measurement
            valid = len(self.teams) > 3
            item = StreamItem(event, state=self, payload=SegmentEvent(key='three_teams', valid=valid))
            result.append(item)
            self.stream_segments['three_teams'] = item


        if self.stream_segments['two_teams'] is None and state.teams_remaining <= 2:
            # Check if this is a valid measurement
            valid = len(self.teams) > 2
            item = StreamItem(event, state=self, payload=SegmentEvent(key='two_teams', valid=valid))
            result.append(item)
            self.stream_segments['two_teams'] = item

        if self.stream_segments['final'] is None and state.teams_remaining <= 1:
            # Check if this is a valid measurement
            valid = len(self.teams) > 1
            item = StreamItem(event, state=self, payload=SegmentEvent(key='final', valid=valid))
            result.append(item)
            self.stream_segments['final'] = item
            self.stream_game_length = event.game_time

            # Fulfill Early if not done
            if self.stream_segments['early'] is None:
                item = StreamItem(event, state=self, payload=SegmentEvent(key='early', valid=False))
                result.append(item)
                self.stream_segments['early'] = item
        return result


    @property
    def messages(self):
        for m in self.message_events:
            m = Event(m)
            if not m['_event'] == 'NNet.Game.SChatMessage':
                continue
            recipient_id = m['m_recipient']
            owner_id = m['_userid']['m_userId']
            chat_type = "all_chat" if recipient_id == 0 else "allied_chat"
            owner = self.get_player(owner_id, 'user_id')
            if owner is None:
                continue
            payload = MessageEvent(
                profile=owner,
                game_time=m.game_time,
                message_type=chat_type,
                message=m['m_string']
            )
            yield payload


    def _parse(self):
        log.info(f"{self.game_id} - Parsing Game")

        for event in self.tracker_events:
            item = StreamItem(event)
            init_event = self.tracked_units.fetch(event)

            if event.unit_init or event.unit_born:
                self.tracked_units.add(event)
                item.payload = self._parse_initialize_unit(event)


            if event.unit_owner_transferred:
                self._parse_transferred(event)

            if event.stats_update:
                item.payload = self._parse_stats_update(event)

            if event.upgrade_event:
                item.payload = self._parse_upgrade(event)

            if event.unit_died and init_event is not None:
                item.payload = self._parse_unit_died(event, init_event)

            self._parse_check_for_segments(event)


            item.state = self
            if isinstance(item.payload, list):
                for i in item.payload:
                    yield StreamItem(item.event, payload=i, state=self)
            else:
                yield item

            # We check this last as it could yield a duplicate event per the above.
            segment_stream_items = self._stream_segments(item)
            for ssi in segment_stream_items:
                yield ssi





