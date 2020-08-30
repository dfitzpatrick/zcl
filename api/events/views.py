

import logging
import typing

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import DiscordUser
from api import utils
from api.models import Match as TempMatch

from api.models import Roster as TempRoster
from datetime import datetime, timedelta, timezone

import random
import ws
import json
from zcl.signals import new_match


log = logging.getLogger('zcl.api.event')
EventPayload = typing.Dict[str, typing.Any]

CACHE = []
CACHE_MAX_SIZE = 32

class HeroTeam(typing.NamedTuple):
    hero: TempRoster
    teammates: utils.QueryType[TempRoster]

    def __str__(self):
        return f"[hero={self.hero} teammates={self.teammates}]"


class EventView(APIView):
    """
    The event view endpoint will capture match "events" that are sent up from
    our match client. We then will broadcast this over a websocket so it can be
    used in different overlays.

    The challenge is we need to maintain anonymity of events per streamer. The events
    from the game will not be filtered and we must find a way to only report relevent events.

    - Events will be posted from a "team" to each team mate.
    - The HERO team will have the avatar and names explicitly caleld out.
    - The non-HERO team will have colors sent out

    Examples:
        "Fred destroys Blue's bunker!"
        ---> "Roz's bunker was destroyed by Light Pink"

    """

    def send_event_to_observers(self, payload: EventPayload, game_id):
        """
        Sends an event to player observers. This is usually unfiltered payload.
        Parameters
        ----------
        payload
        match

        Returns
        -------

        """
        match = TempMatch.objects.get(id=game_id)
        observers = match.observers.all()
        log.debug(f'sending to observers. Observers {observers}')
        for o in observers:
            for user in o.discord_users.all():
                log.debug(f'sending to {user}')
                self.send_event(payload, user)



    def send_event_to_team(self, payload: EventPayload, hero_team: HeroTeam):
        """
        This will loop through and broadcast the same message to all team mates
        That way if there are independent streamers they will also catch the event.
        Parameters
        ----------
        payload
        hero_team

        Returns
        -------

        """
        # Send to the hero first
        for user in hero_team.hero.sc2_profile.discord_users.all():
            self.send_event(payload, user)

        # Send to other team mates
        for roster in hero_team.teammates.all():
            for user in roster.sc2_profile.discord_users.all():
                self.send_event(payload, user)

    def send_event_to_rosters(self, payload: EventPayload, rosters: utils.QueryType[TempRoster]):
        for roster in rosters.all():
            for user in roster.sc2_profile.discord_users.all():
                self.send_event(payload, user)

    def send_event(self, payload: EventPayload, user: DiscordUser):
        action_type = payload.get('type')
        if action_type is None:
            log.error(f"Received Payload without 'type' {payload}")
            return
        if user is None:
            log.error(f"Received null user associated with {payload}")

        user_id = user.id

        channel_layer = get_channel_layer()
        log.debug(f"Sending match_event/{action_type} to {user_id} channel")
        async_to_sync(channel_layer.group_send)(
            user_id,
            {
                'type': 'match_event',
                'action': action_type,
                'guild': settings.GUILD_ID,
                'payload': payload
            }
        )

    def get_bunker_type(self, index: int) -> str:
        marine = [
            1, 2, 3, 4, 5, 6, 8, 15, 16, 23, 24, 31, 32, 39, 40, 47, 48, 55, 57, 58, 59, 60, 61, 62
        ]
        reaper = [
            9, 10, 11, 12, 13, 14, 17, 22, 25, 30, 33, 38, 41, 46, 49, 50, 51, 52, 53, 54
        ]
        marauder = [
            18, 19, 20, 21, 26, 29, 34, 37, 42, 43, 44, 45,
        ]
        ghost = [
            27, 28, 35, 36
        ]
        if index in marine:
            return "Marine"
        elif index in reaper:
            return "Reaper"
        elif index in marauder:
            return "Marauder"
        elif index in ghost:
            return "Ghost"
        else:
            return "Unknown"

    def get_teammates(self, payload, profile_key) -> typing.Optional[HeroTeam]:
        """
        This is a bit unfortunate and will result in two queries of the database.
        We are using Roster objects because they are quite agnostic to stats.
        I didn't want to pollute MatchTeam as they do have active stats associated to them,
        but clearly this is the better way to do it to get players with only one api call.
        Parameters
        ----------
        payload
        profile_key

        Returns
        -------

        """
        try:
            profile_id = payload[profile_key]
            game_id = payload['game_id']
            hero = TempRoster.objects.get(
                match__id=game_id,
                sc2_profile__id=profile_id
            )
            teammates = TempRoster.objects.filter(
                match__id=game_id,
                team_number=hero.team_number
            ).exclude(sc2_profile__id=profile_id)
            return HeroTeam(hero=hero, teammates=teammates)

        except KeyError as e:
            log.error(f"Events: Could not get required key from payload {payload} - {profile_key} - {e}")
        except TempRoster.DoesNotExist:
            log.error(f"Events: Unable to fetch Roster for hero or team mates in {payload}")

    def make_unique_stub(self, payload):
        stub = {
            'type': payload['type'],
            'time': payload['time'],
            'game_id': payload['game_id']
        }
        return stub

    def stub_in_cache(self, stub):
        game_id = stub['game_id']

    def post(self, request: Request):
        global CACHE
        data = request.data.get('data')
        stub = self.make_unique_stub(data)
        if stub in CACHE:
            return Response(status=status.HTTP_200_OK)


        key = data.get('type')
        user = request.user
        if key is not None:

            key_func = getattr(self, key)
            key_func(data, user)

        CACHE = CACHE[1:CACHE_MAX_SIZE+1] + [stub]
        return Response(status=status.HTTP_200_OK)

    def default_event(self, payload: typing.Dict[str, typing.Any], user: DiscordUser):
        log.debug(f"in default event with {payload} from {user}")

    def to_color_name(self, roster: TempRoster) -> str:
        color = roster.color
        names = {
            '31,1,201': 'Light Blue',
            '84,0,129': 'Purple',
            '180,20,30': 'Red',
            '229,91,176': 'Pink',
            '16,98,70': 'Green',
            '28,167,234': 'Teal',
            '78,42,4': 'Brown',
            '35,35,35': 'Grey',
            '204,166,252': 'Lighter Pink',
            '82,84,148': 'Light Pink',
            '22,128,0': 'Green',
            '254,138,14': 'Orange',
            '0,66,255': 'Blue',
            '235,225,41': 'Lighter Blue',
            '150,255,145': 'Light Green',
        }
        return names.get(color, 'Unknown')

    @transaction.atomic()
    def player_leave(self, payload: EventPayload, user: DiscordUser):
        owner_team = self.get_teammates(payload, 'player')
        game_id = str(payload['game_id'])
        if owner_team is None:
            # Probably the match was destroyed and people are just leaving after the game ended.
            return

        messages = [
            "{owner} raged out of the game!",
            "{owner} has left the game!",
            "{owner} ez'd out from the game",
        ]
        owner_message = random.choice(messages).format(owner=owner_team.hero.sc2_profile.name)
        owner_payload = {
            'alert_message': owner_message,
            'alert_avatar': owner_team.hero.sc2_profile.avatar_url
        }


        owner_payload.update(payload)
        self.send_event_to_team(owner_payload, owner_team)
        self.send_event_to_observers(owner_payload, game_id)

        # Check if this was a connected client
        try:
            match = TempMatch.objects.get(id=game_id)
            for u in owner_team.hero.sc2_profile.discord_users.all():
                if u in match.clients.all():
                    match.clients.remove(u)
                    match.save()
            # If there are no more connected clients, no more events will be streamed.
            if match.clients.count() == 0:
                match.delete()
        except TempMatch.DoesNotExist:
            pass


    def player_died(self, payload: EventPayload, user: DiscordUser):
        game_id = str(payload['game_id'])
        owner_team = self.get_teammates(payload, 'player')
        messages = [
            "{owner} was eliminated!",
            "{owner} got ez'd and is eliminated!",
            "{owner} lost all their bunkers and died!",
        ]
        owner_message = random.choice(messages).format(owner=owner_team.hero.sc2_profile.name)
        owner_payload = {
            'alert_message': owner_message,
            'alert_avatar': owner_team.hero.sc2_profile.avatar_url
        }
        owner_payload.update(payload)
        self.send_event_to_team(owner_payload, owner_team)
        self.send_event_to_observers(owner_payload, game_id)

    def player_nuke(self, payload: EventPayload, user: DiscordUser):
        game_id = str(payload['game_id'])
        owner_team = self.get_teammates(payload, 'player')
        owner_name = owner_team.hero.sc2_profile.name
        avatar = owner_team.hero.sc2_profile.avatar_url
        value = payload['value']
        if value > 1300:
            owner_message = "{owner} made an EPIC NUKE of {value}".format(owner=owner_name, value=value)
        elif value < 50:
            owner_message = "{owner} failed with their nuke of {value}".format(owner=owner_name, value=value)
        else:
            messages = [
                "{owner} called down destruction from the heavens with a NUKE value of {value}",
                "{owner} rained fire from the sky with their NUKE value of {value}",
                "{owner} just wtfpwned everyone with their nuke with a value of {value}",
                "{owner} EZ-Nuked for a total value of {value}"
            ]
            owner_message = random.choice(messages).format(owner=owner_name, value=value)
        owner_payload = {
            'alert_message': owner_message,
            'alert_avatar': avatar
        }
        owner_payload.update(payload)
        self.send_event_to_team(owner_payload, owner_team)
        self.send_event_to_observers(owner_payload, game_id)

    def bunker_started(self, payload: EventPayload, user: DiscordUser):
        game_id = str(payload['game_id'])
        owner_team = self.get_teammates(payload, 'player')
        owner_name = owner_team.hero.sc2_profile.name
        avatar = owner_team.hero.sc2_profile.avatar_url
        bunker_type = self.get_bunker_type(payload['index'])
        messages = [
            "{owner} started making a {bt} Bunker!",
            "{owner} just threw down a {bt} Bunker!",
            "{owner} started constructing a {bt} Bunker!"
        ]
        owner_message = random.choice(messages).format(owner=owner_name, bt=bunker_type)
        owner_payload = {
            'alert_message': owner_message,
            'alert_avatar': avatar
        }
        owner_payload.update(payload)
        self.send_event_to_team(owner_payload, owner_team)
        self.send_event_to_observers(owner_payload, game_id)

    def match_end(self, payload: EventPayload, user: DiscordUser):
        ws.send_notification('match_event', payload)
        game_id = str(payload['game_id'])
        try:
            match = TempMatch.objects.get(id=game_id)
            match.delete()
        except TempMatch.DoesNotExist:
            pass

    def bunker_cancelled(self, payload: EventPayload, user: DiscordUser):
        game_id = str(payload['game_id'])
        owner_team = self.get_teammates(payload, 'player')
        owner_name = owner_team.hero.sc2_profile.name
        avatar = owner_team.hero.sc2_profile.avatar_url
        bunker_type = self.get_bunker_type(payload['index'])
        messages = [
            "{owner} changed their mind about their {bt} Bunker",
            "{owner} cancelled their {bt} Bunker!",
        ]
        owner_message = random.choice(messages).format(owner=owner_name, bt=bunker_type)
        owner_payload = {
            'alert_message': owner_message,
            'alert_avatar': avatar
        }
        owner_payload.update(payload)
        self.send_event_to_team(owner_payload, owner_team)
        self.send_event_to_observers(owner_payload, game_id)

    def bunker_killed(self, payload: EventPayload, user: DiscordUser):
        """
        This event impacts 2 teams due to the nature of it.
        We need to anonymize for each side we send
        Parameters
        ----------
        payload
        user

        Returns
        -------

        """
        game_id = str(payload['game_id'])
        anon_avatar = 'https://cdn.discordapp.com/embed/avatars/0.png'
        log.debug("in bunker_killed event view")
        owner_team = self.get_teammates(payload, 'owner')
        killer_team = self.get_teammates(payload, 'killer')
        owner_color = self.to_color_name(owner_team.hero)
        killer_color = self.to_color_name(killer_team.hero)
        bunker_type = self.get_bunker_type(payload['index'])

        # Need to add new payload information with avatar and message
        messages = [
            "{owner}'s {bt} bunker was destroyed by {killer}!",
            "{killer} devastated {owner}'s {bt} bunker!",
            "{owner} built his {bt} rauder just to get it destroyed by {killer}!",
            "{killer} just ez'd {owner}'s {bt} bunker!",
            "{owner}'s {bt} bunker was just sniped by {killer}"

        ]
        owner_message = random.choice(messages).format(
            owner=owner_team.hero.sc2_profile.name,
            bt=bunker_type,
            killer=killer_color
        )
        killer_message = random.choice(messages).format(
            owner=owner_color,
            bt=bunker_type,
            killer=killer_team.hero.sc2_profile.name
        )
        obs_message = random.choice(messages).format(
            owner=owner_color,
            bt=bunker_type,
            killer=killer_color
        )
        obs_payload = {
            'alert_message': obs_message,
            'alert_avatar': anon_avatar,
        }
        owner_payload = {
            'alert_message': owner_message,
            'alert_avatar': owner_team.hero.sc2_profile.avatar_url
        }
        killer_payload = {
            'alert_message': killer_message,
            'alert_avatar': killer_team.hero.sc2_profile.avatar_url
        }
        killer_payload.update(payload)
        owner_payload.update(payload)
        obs_payload.update(payload)

        # Send the events to the websocket stream
        self.send_event_to_team(owner_payload, owner_team)
        self.send_event_to_team(killer_payload, killer_team)
        self.send_event_to_observers(obs_payload, game_id)

    @transaction.atomic()
    def match_start(self, payload: typing.Dict[str, typing.Any], user: DiscordUser):
        """
        We will scaffold a basic match into the database and give it a status of
        'initial'. This status changes when the replay parser successfully runs
        in which case the status will change to 'final'. We will have a background
        cron job that will destroy any match that is 'initial' when it has elapsed
        4 hours from its creation time to account for "abandoned" matches.

        Parameters
        ----------
        payload
        user

        Returns
        -------

        """
        log.debug('In match start')
        game_id = str(payload['game_id'])
        observers = payload['observers']
        players = payload['players']


        match, match_created = TempMatch.objects.get_or_create(
            id=game_id,
            defaults={
                'status': 'initial',
            }
        )
        for o in observers:
            if o['handle'] == '':
                continue

            log.debug(f'creating {o}')
            obs = utils.fetch_or_create_profile(o['handle'])
            match.observers.add(obs)
        match.save()


        for p in players:
            profile = utils.fetch_or_create_profile(p['handle'])
            TempRoster.objects.get_or_create(
                match=match,
                sc2_profile=profile,
                defaults={
                    'team_number': p['team'],
                    'position_number': p['slot'],
                    'color': p['color'],
                }
            )
            # Look for current connected clients
            for user in profile.discord_users.all():
                heartbeat = user.client_heartbeat
                now = datetime.now(timezone.utc)
                if now - heartbeat < timedelta(minutes=10):
                    match.clients.add(user)

        print('done!')
        new_match.send(sender=self.__class__, instance=match)

    @transaction.atomic()
    def match_end(self, payload: typing.Dict[str, typing.Any], user: DiscordUser):
        game_id = str(payload['game_id'])
        try:
            match = TempMatch.objects.get(id=game_id)
            match.delete()
        except TempMatch.DoesNotExist:
            pass
