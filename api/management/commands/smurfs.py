import logging

from django.core.management.base import BaseCommand

from accounts.models import DiscordUser

log = logging.getLogger('zcl.api.management')

class Command(BaseCommand):

    def handle(self, *args, **options):
        discord_id = str(args[0])
        user = DiscordUser.objects.get(id=discord_id)
        for p in user.profiles.all():
            print(p)
            log.info(p)


