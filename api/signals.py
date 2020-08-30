import logging

from django.conf import settings
from django.db.models.signals import pre_delete, post_delete, post_save
from django.dispatch.dispatcher import receiver

from accounts.models import SocialAccount, DiscordUser
from api.models import Replay, TwitchStream, SC2Profile, Match
from websub.models import Subscription
from websub.signals import webhook_update
from websub.views import WebSubView
from api.tasks import get_profile_details
from .serializers import TwitchStreamSerializer, DiscordUserSerializer
from services.twitch import Helix
from api import serializers
from zcl.signals import new_match
import ws
from api.events.views import EventView

log = logging.getLogger('zcl.api')


@receiver(post_save, sender=DiscordUser)
def user_update(sender, instance, created, **kwargs):
    """
    Sends updates to the user model being changed. One common reason is
    updating a client heartbeat. Send this out.
    Parameters
    ----------
    sender
    instance
    created
    kwargs

    Returns
    -------

    """
    payload = DiscordUserSerializer(instance).data
    ws.send_notification(ws.types.USER_UPDATE, payload)

@receiver(post_save, sender=SC2Profile)
def profile_get_details(sender, instance, created, **kwargs):
    """
    If a new Profile is created when parsing matches, use the Blizzard API
    to fetch the player details (name, avatar, clan etc) in a celery task.
    Parameters
    ----------
    sender
    instance
    created: Was this a newly created instance?
    kwargs

    Returns
    -------

    """
    if created:
        return get_profile_details.delay(instance.id)

@receiver(post_delete, sender=Replay)
def replay_delete(sender, instance, **kwargs):
    """
    Handle cleanup of S3 file to auto delete the replay if the record is removed.
    Parameters
    ----------
    sender
    instance
    kwargs

    Returns
    -------

    """
    pass
    # Temporarily disabled

    #print("deleting file   from S3")
    # False so FileField doesn't save the model
    #instance.file.delete(False)

@receiver(webhook_update)
def twitch_stream_update(sender: WebSubView, webhook_name: str, uuid, data, **kwargs):
    if not webhook_name == 'streams':
        return
    try:
        active = data != []
        ts = TwitchStream.objects.get(uuid=uuid)
        ts.extra_data = data
        ts.active = active
        ts.save()

        action = ws.types.STREAM_START if active else ws.types.STREAM_STOP
        ws.send_notification(action, TwitchStreamSerializer(ts).data)
    except TwitchStream.DoesNotExist:
        log.error(f"Missing TwitchStream object for {uuid}")


@receiver(pre_delete, sender=SocialAccount)
def social_account_delete(sender, instance: SocialAccount, **kwargs):
    # Get any Twitch stream and remove it
    log.debug('in delete signal for SocialAccount')
    log.debug(f"# of Twitch Streams: {len(instance.twitch_streams.all())}")

    for t in instance.twitch_streams.all():
        t:TwitchStream
        try:
            h = Helix(instance)
            h.refresh_token()
            headers = h.headers
            uuid = t.uuid
            twitch_name = t.username
            username = t.user.username
            sub = Subscription.objects.get(uuid=uuid)
            sub.unsubscribe(headers=headers)
            log.debug(f'WebSub Twitch ({twitch_name}/{username}) unsubscribed and deleted')
        except Subscription.DoesNotExist:
            log.error(f"DELETE Failed for WebSub {instance.provider} username: {username}")
            continue

    instance.twitch_streams.all().delete()
    # TODO: Any stream stop events

@receiver(post_delete, sender=Match)
def match_delete(sender, instance: Match, **kwargs):
    serialized = serializers.MatchSerializer(instance)
    ws.send_notification(ws.types.MATCH_DELETE, serialized.data)


@receiver(new_match, sender=EventView)
def new_match(sender, instance: Match, **kwargs):
    """
    Fires whenever a new match is made. We'll serialize a response with this
    and Rosters as they are most commonly used.
    Parameters
    ----------
    sender
    instance
    kwargs

    Returns
    -------

    """
    log.debug('in new_match signal')
    match = serializers.MatchFullSerializer(instance).data
    streamers = serializers.MatchStreamersSerializer(instance.streamers, many=True).data


    payload = {
        'match': match,
        'streamers': streamers
    }
    log.debug('sending new match notification')
    ws.send_notification('new_match', payload)