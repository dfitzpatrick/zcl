import logging

from django.core.management.base import BaseCommand

from api.models import SC2Profile
from api.tasks import get_profile_details
from services.blizzard import BlizzardAPI

log = logging.getLogger('zcl.api.management')

class Command(BaseCommand):

    def handle(self, *args, **options):
        # We'll pass in the instnace to avoid auth hits on the database
        b = BlizzardAPI()
        profiles = SC2Profile.objects.all().order_by('-created')
        for p in profiles:
            get_profile_details.delay(p.id, api_class=b, ignore_missing=True)


