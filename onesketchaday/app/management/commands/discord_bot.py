import onesketchaday.settings

from bot.bot import OnesketchadayBot
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        bot = OnesketchadayBot()
        bot.run(onesketchaday.settings.DISCORD_API_TOKEN)