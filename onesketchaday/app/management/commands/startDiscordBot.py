from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import *
from django.core.files import File
from django.utils import timezone
from dotenv import load_dotenv
from discord.ext import commands
from app.models import *
from app.utils import *
from app.bot import *
import logging, os
import discord
import asyncio


class DiscordBot(PostingBot):
    help = 'Updates the Participants page'
    bot = commands.Bot(command_prefix='\\', description="A bot for the onesketchaday.art website")

    def syncGetUser(self, index):
        return User.objects.filter(discord_username=index)[0]

    async def getUser(self, index):
        return await sync_to_async(self.syncGetUser)(index)

    async def sendUserReply(self, message, context):
        await context.message.reply(message)
    
    async def downloadImage(self, imagePath, context):
        await context.message.attachments[0].save(open(imagePath, "wb"))
bot = DiscordBot()

@bot.bot.command('post', pass_context=True)
async def imageHandler(context):
    username = str(context.message.author)
    title = context.message.content
    if len(context.message.attachments) < 1:
        await bot.sendUserReply('Cannot create post since no attachment was provided :p', context)
        return
    fleName = context.message.attachments[0].filename

    await bot.asyncCreatePostFromUser(username, title, fleName, context)

class Command(BaseCommand):
    def handle(self, *args, **options):
        load_dotenv()

        bot.bot.run(settings.DISCORD_API_TOKEN)