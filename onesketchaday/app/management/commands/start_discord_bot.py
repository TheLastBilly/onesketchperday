from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import *
from django.core.files import File
from django.utils import timezone
from urllib.parse import urlparse
from discord.ext import commands
from dotenv import load_dotenv
from app.models import *
from app.utils import *
from app.bot import *
import logging, os
import discord
import asyncio

class DiscordBot():
    help = 'Updates the Participants page'
    bot = commands.Bot(command_prefix='.', description="A bot for the onesketchaday.art website")

    def syncGetUser(self, index):
        return User.objects.filter(discord_username=index)[0]
    
    def syncCreatePost(self, owner, file, title, isVideo=False):
        if isVideo:
            return Post.objects.create(owner=owner, video=file, title=title)
        else:
            return Post.objects.create(owner=owner, image=file, title=title)

    async def createPost(self, owner, file, title, isVideo=False):
        return await sync_to_async(self.syncCreatePost)(owner, file, title, isVideo)

    def syncDeletePost(self, owner, id):
        Post.objects.get(owner=owner, id=id).delete()
        
    async def deletePost(self, owner, id):
        await sync_to_async(self.syncDeletePost)(owner, id)

    async def getUser(self, index):
        try:
            return await sync_to_async(self.syncGetUser)(index)
        except ObjectDoesNotExist as e:
            return None
        
    async def validateUser(self, username):
        user = await self.getUser(username)
        if not user:
            await self.sendUserReply("Sorry, but you are not allowed to interact with this bot", context)
            logger.error("Rejected request from {}: {}".format(username, str(e)))
            return None
        
        return user

    async def sendUserReply(self, message, context):
        await context.message.reply(message)
    
    async def downloadFile(self, filePath, attachment):
        await attachment.save(open(filePath, "wb"))

    async def createPostFromUser(self, user, title, fileName, context, attachment, isVideo=False):
        logger.info('Received post request from user {}'.format(user.username))

        if title:
            title = title[:Post._meta.get_field('title').max_length]
        else:
            title = ""

        try:
            absolutePath = settings.MEDIA_ROOT + "/" + fileName
            await self.downloadFile(absolutePath, attachment)

            post = await self.createPost(user, fileName, title, isVideo)

            await self.sendUserReply("File succesfully uploaded!\nHere's the link yo your new post: " + settings.SITE_URL + "post/" + post.id + "", context)
        
        except Exception as e:
            logger.error("Cannot create image post for user {}: {}".format(user.username, str(e)))
            await self.sendUserReply("Cannot upload requested picture due to an internal error", context)
            if os.path.exists(absolutePath):
                os.remove(absolutePath)

bot = DiscordBot()

@bot.bot.command(name='post', pass_context=True)
async def createPost(context, *, arg=None):
    username = str(context.message.author)
    title = arg
    if not title:
        title = ""
    user = await bot.validateUser(username)
    if not user:
        return

    attachmentCount = len(context.message.attachments)
    if attachmentCount < 1:
        await bot.sendUserReply('Cannot create post since no attachment was provided :p', context)
        return
    
    i = 0
    for attachment in context.message.attachments:
        fileName = attachment.filename
        ext = ""
        for e in IMAGE_EXTENSIONS:
            if e in fileName:
                ext = e
                break

        for e in VIDEO_EXTENSIONS:
            if e in fileName:
                ext = e
                isVideo = True
                break
        
        if ext == "":
            await bot.sendUserReply('Can only accept attachments with the following extensions: {}'.format(', '.join(IMAGE_EXTENSIONS)), context)
            return
        fileName = str(attachment.id) + ext

        i = i + 1
        if attachmentCount > 1:
            await bot.createPostFromUser(user, title + "(" + str(i) + "/" + str(attachmentCount)+ ")", fileName, context, attachment, isVideo=isVideo)
        else:
            await bot.createPostFromUser(user, title, fileName, context, attachment, isVideo=isVideo)

@bot.bot.command(name='delete', pass_context=True)
async def deletePost(context, link):
    username = str(context.message.author)
    user = await bot.validateUser(username)
    if not user:
        return

    if not link:
        await bot.sendUserReply('I need the link to your post first', context)

    try:
        uniqueId = urlparse(link).path.rsplit("/", 1)[-1]
        await bot.deletePost(user, uniqueId)

        await bot.sendUserReply('Done!', context)
    except Exception as e:
        logger.error("Cannot delete post on link \"{}\" from user {}: {}".format(link, username, str(e)))
        await bot.sendUserReply('Sorry, but I couldn\'t find a post with that link, or that post doesn\'t belong to you', context)

class Command(BaseCommand):
    def handle(self, *args, **options):
        load_dotenv()

        bot.bot.run(settings.DISCORD_API_TOKEN)