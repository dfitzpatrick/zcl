from __future__ import absolute_import, unicode_literals
import typing
import zclreplay
from celery import shared_task
from celery.utils.log import get_task_logger
from s2protocol import versions

import ws
import ws.types
from . import annotations
from . import models, utils, serializers
from zclreplay.streamparser import StreamParser, StreamItem
from django.db import transaction
from zclreplay import objects as replayobjects
from copy import copy
import tracemalloc
import services.blizzard
from django.db.utils import IntegrityError

log = get_task_logger('zcl.api.tasks')


def get_or_create_team(profiles: typing.List[models.SC2Profile]) -> models.Team:
    """
    We use a m2m relationship on teams because it makes sense, but we want team
    objects to be unique for easy querying.

    A team can have multiple players on it
    A player can be a member of multiple teams
    ---
    However we want one team object for each unique set.

    Parameters
    ----------
    profiles

    Returns
    -------
    Team
    """
    ids = [p.id for p in profiles]
    teams: typing.List[models.Team] = (
        models.Team
        .objects
        .prefetch_related('profiles')
        .all()
    )
    for t in teams:
        team_profiles = t.profiles.all()
        if len(ids) == len(team_profiles):
            if all(p.id in ids for p in team_profiles):
                return t

    team = models.Team()
    team.save()
    team.profiles.add(*profiles)
    team.save()
    return team

@shared_task
def parse_replay(pk: int):
    try:
        replay_model = models.Replay.objects.get(id=pk)
        replay = StreamParser(replay_model.file)
        do_parse(replay_model, replay)
    except (zclreplay.NotZCReplay, zclreplay.IncompleteReplay) as e:
        log.error(f"Error Not valid replay: {e}")
        return
    except models.Replay.DoesNotExist:
        log.error(f"Cannot find Database Object with pk {pk}")
        return
    except:
        # Some random error occurred. Sometimes this is due to missing protocol
        # We already use the lower protocol if its not found. Try the higher.
        log.error("Failed to Parse Game. Trying Higher Protocol Version.")
        replay_model = models.Replay.objects.get(id=pk)
        replay = StreamParser(replay_model.file)
        replay.protocol = versions.build(replay.fallback_versions[1])
        do_parse(replay_model, replay)


@transaction.atomic()
def do_parse(replay_model, replay: StreamParser):
    profile_cache = {}
    match_team_container = {}


    game_id = replay.game_id


    match, match_created = models.Match.objects.get_or_create(
        id=game_id,
        defaults={
            'guild': models.Guild.objects.first(),
            'arcade_map': models.Game.objects.first(),
            'game_id': replay.game_id,
        }
    )
    match.match_date = replay.game_time
    match.legacy = False
    match.status = 'final'
    match.save()
    if not match_created:
        # Re-parse. Clear out any match events or anything that could have different lengths
        match.game_events.all().delete()
        match.teams.all().delete()
        match.rosters.all().delete()
        match.segments.all().delete()
        match.unit_stats.all().delete()
        match.match_winners.all().delete()
        match.matchteam_set.all().delete()
        match.match_losers.all().delete()
        match.messages.all().delete()

    # Create team objects


    upgrade_key_set = set()
    time_series = []
    unit_upgrades = []
    for stream_item in replay._parse():
        stream_item:StreamItem
        payload = stream_item.payload
        state:StreamParser = stream_item.state
        event:replayobjects.Event = stream_item.event

        if isinstance(payload, replayobjects.MatchEvent):
            game_event_name, created = models.GameEventName.objects.get_or_create(
                id=payload.key,
                defaults={'title': f'New Game Event {payload.key}'}
            )

            ge_profile = utils.fetch_or_create_profile(payload.profile, profile_cache)
            ge_opposing_profile = utils.fetch_or_create_profile(payload.opposing_profile, profile_cache)

            game_event, updated = models.GameEvent.objects.update_or_create(
                key=game_event_name,
                match=match,
                profile=ge_profile,
                opposing_profile=ge_opposing_profile,
                game_time=payload.game_time,
                defaults={
                    'game_time': payload.game_time,
                    'value': payload.value,
                    'description': payload.description,
                    'total_score': payload.profile.unit_stats.total_score,
                    'minerals_on_hand': payload.profile.unit_stats.minerals_on_hand,
                }
            )
            # Generate the information for the Total Score and Minerals Floating
            # Charts here. We'll upload them to S3 down below.
            on_hand = lambda o: o.get('created', 0) - o.get('lost', 0) - o.get('cancelled', 0)
            for event_player_state in state.players:
                payload = {
                    'id': event_player_state.profile_id,
                    'name': event_player_state.name,
                    'game_time': event.game_time,
                    'total_score': event_player_state.unit_stats.total_score,
                    'minerals_floated': event_player_state.unit_stats.minerals_on_hand,
                    'bunkers': on_hand(event_player_state.unit_stats.bunkers),
                    'tanks': on_hand(event_player_state.unit_stats.tanks),
                    'depots': on_hand(event_player_state.unit_stats.depots),
                    'nukes': on_hand(event_player_state.unit_stats.nukes),
                    'current_supply': on_hand(event_player_state.unit_stats.biological_stats)

                }
                time_series.append(payload)

        if isinstance(payload, replayobjects.SegmentEvent):
            segment, created = models.Segment.objects.update_or_create(
                measure=payload.key,
                match=match,
                defaults={
                    'game_time': event.game_time,
                    'valid': payload.valid,
                }
            )
            for p in state.players:
                segment_profile = utils.fetch_or_create_profile(p, profile_cache)
                segment_lane = utils.fetch_or_create_profile(p.lane, profile_cache)
                segment_killer = utils.fetch_or_create_profile(p.killer, profile_cache)
                profile_item, created = models.SegmentProfileItem.objects.update_or_create(
                    segment=segment,
                    match=match,
                    profile=segment_profile,
                    defaults={
                        'lane': segment_lane,
                        'left_game': p.left_game,
                        'eliminated': p.eliminated,
                        'eliminated_by': segment_killer,
                        'total_score': p.unit_stats.total_score,
                        'minerals_on_hand': p.unit_stats.minerals_on_hand,
                        'army_value': p.unit_stats.army_value,
                        'tech_value': p.unit_stats.tech_value,
                        'lost_tech_value': p.unit_stats.lost_tech_value,
                        'tech_damage_value': p.unit_stats.tech_damage_value
                    }
                )
                for u in p.unit_stats.totals[p].keys():
                    # Just grab this current player stats and commit that
                    # to the database. No vs data.
                    unit, _ = models.Unit.objects.get_or_create(
                        map_name=u
                    )
                    models.SegmentUnitStat.objects.update_or_create(
                        segment_profile=profile_item,
                        segment=segment,
                        unit=unit,
                        created=p.unit_stats.totals[p][u].get('created', 0),
                        killed=p.unit_stats.totals[p][u].get('killed', 0),
                        lost=p.unit_stats.totals[p][u].get('lost', 0),
                        cancelled=p.unit_stats.totals[p][u].get('cancelled', 0)
                    )
        if isinstance(payload, replayobjects.UpgradeEvent):
            container = []
            for player_unit_upgrades in state.players:
                ups = copy(player_unit_upgrades.upgrade_totals)
                ups['profile_id'] = player_unit_upgrades.profile_id
                ups['name'] = player_unit_upgrades.name
                ups['game_time'] = event.game_time
                ups['total_score'] = player_unit_upgrades.unit_stats.total_score
                upgrade_key_set.update(ups.keys())
                container.append(ups)
            unit_upgrades.append(container)


    for t in replay.teams:
        if len(t.players) == 0:
            continue
        # convert to database instances
        profiles_db = [utils.fetch_or_create_profile(pt, profile_cache) for pt in t.players]
        team_db = get_or_create_team(profiles_db)
        if match.draw:
            outcome = 'draw'
        else:
            outcome = 'win' if t.winner else 'loss'

        match_team, _ = models.MatchTeam.objects.update_or_create(
            match=match,
            team=team_db,
            position=t.position,
            outcome=outcome,
        )
        match_team_container[t.id] = match_team

    # Get Roster information loaded
    for p in replay.players:
        p: zclreplay.Player
        # Get player profile:
        team = match_team_container[p.team.id]
        profile = utils.fetch_or_create_profile(p, profile_cache)
        lane_profile = utils.fetch_or_create_profile(p.lane, profile_cache)
        killer = utils.fetch_or_create_profile(p.killer, profile_cache)

        models.Roster.objects.update_or_create(
            match=match,
            sc2_profile=profile,
            defaults={
                'color': p.color_string,
                'lane': lane_profile,
                'team_number': p.team.id,
                'position_number': p.position,
                'team': team,
            }
        )
        if p.winner:
            models.MatchWinner.objects.update_or_create(
                match=match,
                profile=profile,
                defaults = {
                    'carried': p.eliminated
                }
            )
        else:
            models.MatchLoser.objects.update_or_create(
                match=match,
                profile=profile,
                defaults={
                    'killer': killer,
                    'left_game': p.left_game,
                    'game_time': float(p.eliminated_at),
                    'victim_number': p.victim_number
                }
            )



    for upgrade_iteration in unit_upgrades:
        for player_upgrades in upgrade_iteration:
            for k in upgrade_key_set:
                if k not in player_upgrades.keys():
                    player_upgrades[k] = 0


    match.game_length = replay.stream_game_length
    match.save()
    try:
        if match_created:
            # If we call this every time, it'll throw integrity error. So only
            # update it if there is a new match
            replay_model.match = match
            replay_model.save()
    except IntegrityError:
        print(f"Integrity error on {game_id}")
        print(f"replay.match is")
        print(replay_model.match)
        print('match is')
        print(match)
        print(f'Match created: {match_created}')

    utils.gzip_chart_to_s3(unit_upgrades, match_id=replay.game_id, name='upgrades')
    feed = [p.feed for p in replay.players]
    utils.gzip_chart_to_s3(feed, match_id=replay.game_id, name='feed')
    utils.gzip_chart_to_s3(time_series, match_id=replay.game_id, name='time_series')
    utils.gzip_chart_to_s3(replay.unit_stats(), match_id=replay.game_id, name='unit_stats')

    for replay_msg in replay.messages:
        msg_owner = utils.fetch_or_create_profile(replay_msg.profile, profile_cache)
        models.MatchMessage.objects.create(
            match=match,
            profile=msg_owner,
            message_type=replay_msg.message_type,
            message=replay_msg.message,
            game_time=replay_msg.game_time,
        )

    log.info(f"{replay.game_id} - Loaded to Database")


@shared_task
def get_profile_details(id: str, api_class=None, ignore_missing=False):
    try:
        api = services.blizzard.BlizzardAPI() if api_class is None else api_class
        profile = models.SC2Profile.objects.get(id=id)
        realm_id, game, region_id, profile_id = id.split('-')
        name, portrait, clan_name, clan_tag = 'Deleted', '', '', ''
        data = api.get_profile(id)
        if data is None and ignore_missing:
            return

        if data is not None:
            summary = data['summary']
            name = summary['displayName']
            portrait = summary.get('portrait', '')
            clan_name = summary.get('clanName', '')
            clan_tag = summary.get('clanTag', '')
        profile.profile_url = f'https://starcraft2.com/en-us/profile/{region_id}/{realm_id}/{profile_id}'
        profile.name = name
        profile.avatar_url = portrait
        profile.clan_name = clan_name
        profile.clan_tag = clan_tag
        profile.save()
    except models.SC2Profile.DoesNotExist:
        return

