from __future__ import absolute_import, unicode_literals
import typing
import zclreplay
from celery import shared_task
from celery.utils.log import get_task_logger

import ws
import ws.types
from . import annotations
from . import models, utils, serializers

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
    """

    Parameters
    ----------
    pk: Primary Key of Replay Model

    Returns
    -------

    """
    profile_cache = {}

    try:
        replay_model = models.Replay.objects.get(id=pk)
        replay = zclreplay.Replay(replay_model.file)
    except (zclreplay.NotZCReplay, zclreplay.IncompleteReplay) as e:
        log.error(f"Error Not valid replay: {e}")
        return
    except models.Replay.DoesNotExist:
        log.error(f"Cannot find Database Object with pk {pk}")
        return

    game_id = int(replay.game_id)

    try:
        replay.parse()
    except Exception:
        return



    match, match_created = models.Match.objects.get_or_create(
        id=game_id,
        guild=models.Guild.objects.first(),
        arcade_map=models.Game.objects.first(),
        game_id=replay.game_id,
        defaults = {
            'game_length': float(replay.game_length)
        }
    )
    match.match_date = replay.game_time
    mid = match.save()
    if not match_created:
        # Re-parse. Clear out any match events or anything that could have different lengths
        match.game_events.all().delete()

    match_team_container = {}
    # Create team objects
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


    for p in replay.players:
        p: zclreplay.Player
        # Get player profile:
        team_profiles = [utils.fetch_or_create_profile(tp, profile_cache) for tp in p.team.players]
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


    time_series = []
    i = 0
    for me in replay.match_events:
        me: zclreplay.MatchEvent
        game_event_name, created = models.GameEventName.objects.get_or_create(
            id=me.key,
            defaults={'title': f'New Game Event {me.key}'}
        )
        if me.profile.unit_stats.total_score == 0:
            print(f"Warning 0 score for {me.profile.name} at {me.game_time} on {me.key}")
        ge_profile = utils.fetch_or_create_profile(me.profile, profile_cache)
        ge_opposing_profile = utils.fetch_or_create_profile(me.opposing_profile, profile_cache)
        game_event, updated = models.GameEvent.objects.update_or_create(
            key=game_event_name,
            match=match,
            profile=ge_profile,
            opposing_profile=ge_opposing_profile,
            game_time=me.game_time,
            defaults = {
                'game_time': me.game_time,
                'value': me.value,
                'description': me.description,
                'total_score': me.profile.unit_stats.total_score,
                'minerals_on_hand': me.profile.unit_stats.minerals_on_hand,
            }
        )

        # Generate the information for the Total Score and Minerals Floating
        # Charts here. We'll upload them to S3 down below.
        on_hand = lambda o: o.get('created', 0) - o.get('lost', 0)
        for event_player_state in me.player_state:
            payload = {
                'id': event_player_state.profile_id,
                'name': event_player_state.name,
                'game_time': me.game_time,
                'total_score': event_player_state.unit_stats.total_score,
                'minerals_floated': event_player_state.unit_stats.minerals_on_hand,
                'bunkers': on_hand(event_player_state.unit_stats.bunkers),
                'tanks': on_hand(event_player_state.unit_stats.tanks),
                'depots': on_hand(event_player_state.unit_stats.depots),
                'nukes': on_hand(event_player_state.unit_stats.nukes),
                'current_supply': on_hand(event_player_state.unit_stats.biological_stats)

            }
            time_series.append(payload)

    for p in replay.players:
        profile = utils.fetch_or_create_profile(p, profile_cache)
        if p.winner:
            obj, _ = models.MatchEvent.objects.update_or_create(
                match=match,
                handle=profile,
                key='WIN',

                defaults={
                    'description': f"{p.name} Wins",
                    'points': 5,
                }
            )
        else:
            obj, _ = models.MatchEvent.objects.update_or_create(
                match=match,
                handle=profile,
                key='LOSS',
                defaults={
                    'points': 1,
                    'description': f"{p.name} Loses"
                }
            )


    # Load in Segment Data
    for seg_measure in replay.segments:
        segment, created = models.Segment.objects.update_or_create(
            measure=seg_measure,
            match=match,
            defaults={
                'game_time': replay.segments[seg_measure].get('game_time', 0.0),
                'valid': replay.segments[seg_measure]['valid'],
            }
        )
        for p in replay.segments[seg_measure].get('players', []):
            p:zclreplay.Player
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
                    map_name = u
                )

                models.SegmentUnitStat.objects.update_or_create(
                    segment_profile=profile_item,
                    segment=segment,
                    unit=unit,
                    created=p.unit_stats.totals[p][u].get('created', 0),
                    killed = p.unit_stats.totals[p][u].get('killed', 0),
                    lost=p.unit_stats.totals[p][u].get('lost', 0),
                    cancelled=p.unit_stats.totals[p][u].get('cancelled',0)
                )

    replay_model.match = match
    replay_model.save()

    # Upload Chart Data to S3.
    all_ups = [p.upgrades for p in replay.players]
    utils.gzip_chart_to_s3(all_ups, match_id=replay.game_id, name='upgrades')

    feed = [p.feed for p in replay.players]
    utils.gzip_chart_to_s3(feed, match_id=replay.game_id, name='feed')

    utils.gzip_chart_to_s3(time_series, match_id=replay.game_id, name='time_series')
    utils.gzip_chart_to_s3(replay.unit_stats(), match_id=replay.game_id, name='unit_stats')

    log.info(f"{replay.game_id} - Loaded to Database")

    qs_match = annotations.matches.qs_with_players().get(id=match.id)
    match_serialized = serializers.MatchSerializer(qs_match).data
    payload = {
        'type': ws.types.PARSED_MATCH,
        'match': match_serialized,
    }
    ws.send_notification(payload)
