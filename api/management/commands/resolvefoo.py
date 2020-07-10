from services.twitch import Helix
import logging
from django.core.management.base import BaseCommand
from api.models import SC2Profile
from services.blizzard import BlizzardAPI
from api.tasks import get_profile_details

log = logging.getLogger('zcl.api.management')

class Command(BaseCommand):

    def handle(self, *args, **options):
        # We'll pass in the instnace to avoid auth hits on the database
        b = BlizzardAPI()
        foos = SC2Profile.objects.filter(name='FOO').order_by('-created')
        for foo in foos:
            get_profile_details.delay(foo.id, api_class=b, ignore_missing=True)


