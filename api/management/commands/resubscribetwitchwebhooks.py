from django.core.management.base import BaseCommand
from websub.models import Subscription
from accounts.models import SocialAccount
from api.models import TwitchStream
from services.twitch import Helix
import logging

log = logging.getLogger('zcl.api.management')

class Command(BaseCommand):

    def handle(self, *args, **options):
        for sub in Subscription.objects.all():
            try:
                uuid = sub.uuid
                log.debug(f'Fetching TwitchStream {uuid}')
                ts = TwitchStream.objects.get(uuid=sub.uuid)
                helix = Helix(ts.social_account)
                log.debug(f'Calling Refresh on {uuid} {ts.username}')
                helix.refresh_stream_subscription(sub)
            except TwitchStream.DoesNotExist:
                log.error(f"TwitchStream {uuid} does not exist to refresh")
                continue
