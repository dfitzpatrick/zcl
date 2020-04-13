import logging
import re

import requests
from django.dispatch import receiver

import ws
import ws.types
from api.models import *
from api.models import TwitchStream
from api.serializers import SC2ProfileSerializer
from websub.signals import webhook_update
from websub.views import WebSubView

"""
This is the match system that is called from the api endpoint.

update_client

SIGNALS
replay_added

"""

log = logging.getLogger(__name__)

@receiver(webhook_update, sender=WebSubView)
def stream_webhook_update(sender: WebSubView, webhook_name, uuid, data, **kwargs):
    data = data.get('data')
    if webhook_name != 'streams':
        return
    if not isinstance(data, list):
        return
    try:
        ts = TwitchStream.objects.get(uuid=uuid)
        log.info(f"Got Twitchstream instance with {uuid}")
        ts.active = data != []
        ts.save()
        type = ws.types.STREAM_START if ts.active else ws.types.STREAM_STOP
        payload = {
            'type': type,
            'user_id': ts.user.id,
            'data': data,
        }
        ws.send_notification(payload)
    except TwitchStream.DoesNotExist:
        log.info(f"Could not get TwitchStream Instance with {uuid}")
        pass
    log.info("Got stream event. Populated Instance {request}")


def get_player_name(profile: SC2Profile) -> str:

    base_url = "https://starcraft2.com/en-us/profile"
    url = "{0}/{1.region}/{1.realm}/{1.profile_id}".format(base_url, profile)
    r = requests.get(url, allow_redirects=True)
    pattern = re.compile("<title>(.+?)</title>")
    matches = re.findall(pattern, r.content.decode('utf-8'))
    name = matches[0].split('-')
    name = name[1].strip()
    if name == "StarCraft II Official Game Site":
        return "Unknown"
    return name

def get_or_create_profile(id):
    obj, created = SC2Profile.objects.get_or_create(
        id=id,
        defaults={'name': 'FOO'}
    )
    if created:
        obj.name = get_player_name(obj)
        obj.save()
    return obj


def get_or_create_match(payload):
    """
    Retrieve the match or creating all the tables needed for one.
    Parameters
    ----------
    id

    Returns
    -------

    """
    id = payload.get('game_id')
    match, created = Match.objects.get_or_create(
        guild=Guild.objects.first(),
        arcade_map=Game.objects.first(),
        id=id,
        defaults={
            'status': payload.get('status') or 'initial'
        }
    )

    for p in payload.get('players'):
        profile = get_or_create_profile(p.get('handle'))
        Roster.objects.get_or_create(
            match=match,
            sc2_profile=profile,
            team_number=p.get('team'),
            position_number=p.get('slot'),
            defaults={
                'color': p.get('color')
            }
        )

    return match, created

def create(user, payload):
    m, created = get_or_create_match(payload)
    update_client(user, m, connected=True)

    players = payload.get('players')
    if isinstance(players, list):
        # Serialize object from profile id
        container = []
        for p in players:
            profile = get_or_create_profile(p['handle'])
            container.append(SC2ProfileSerializer(profile).data)
        payload['players'] = container

    if created:
        print("Notification Sent")
        ws.send_notification(payload)
    else:
        print("Match existed")
    return m

def remove_client(payload):
    """
    This assumes that a payload is given that could be a profile string
    Parameters
    ----------
    payload

    Returns
    -------

    """
    game_id = payload.get('game_id')
    try:
        match = Match.objects.get(id=game_id)
    except Match.DoesNotExist:
        return
    player = payload.get('player')
    if isinstance(player, str):
        # Try to get a valid user.
        try:
            profile = SC2Profile.objects.get(id=player)
        except SC2Profile.DoesNotExist:
            print("No client")
            return

        # If any of this profiles discord accounts are found disconnect them.
        if profile.discord_users is not None:
            filtered = match.clients.filter(user__in=profile.discord_users.all())
            print(filtered)
            for c in filtered:
                update_client(c.user, match, connected=False)


def update_client(user, match, connected=True):

    """

    Parameters
    ----------
    user
    payload: The match_start payload
    connected: True for connected, False if disconnected.
    Returns
    -------

    """
    client, created = MatchClient.objects.get_or_create(
        match=match,
        user=user,
        defaults={
            'connected': connected,
        }
    )
    if not created:
        client.connected = connected
        client.save()

            # TODO: Signal
    # TODO: Add handling for connected

    from social_django.models import UserSocialAuth
    try:
        twitch = UserSocialAuth.objects.get(user=user, provider='twitch')

    except UserSocialAuth.DoesNotExist:
        pass

