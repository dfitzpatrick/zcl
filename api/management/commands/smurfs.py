import logging

from django.core.management.base import BaseCommand

from accounts.models import DiscordUser

log = logging.getLogger('zcl.api.management')

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('discord_id', type=str, help='Discord ID')

    def handle(self, *args, **options):
        discord_id = options['discord_id']
        user = DiscordUser.objects.get(id=discord_id)
        for p in user.profiles.all():
            print(p)
            log.info(p)


