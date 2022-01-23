from datetime import time
from django.core.management.base import BaseCommand, CommandError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.exceptions import *
from django.core.files import File
from django.utils import timezone
from urllib.parse import urlparse
from discord.ext import commands
from dotenv import load_dotenv
from app.models import *
from app.utils import *
from onesketchaday.bot.globals import *
import logging, os
import discord
import asyncio
from app.utils import *

class DiscordBot():
    help = 'Updates the Participants page'
    bot = commands.Bot(command_prefix='.', description="A bot for the onesketchaday.art website")

    def syncGetVariable(self, name):
        return Variable.objects.get(name=name)
    def syncSetVariable(self, name, text=None, label=None, date=None, integer=None, file=None):
        reminder = self.syncGetVariable(name)
        if text:
            reminder.text = text
        if label:
            reminder.label = label
        if date:
            reminder.date = date
        if integer:
            reminder.integer = integer
        if file:
            reminder.file = file
        reminder.save()

    async def getReminder(self):
        return await sync_to_async(self.syncGetVariable)("ReminderMessage")
    async def setReminder(self, text):
        await sync_to_async(self.syncSetVariable)(name="ReminderMessage", text=text)
    
    async def getVariable(self, name):
        return await sync_to_async(self.syncGetVariable)(name)
    async def setVariable(self, name, text=None, label=None, date=None, integer=None, file=None):
        return await sync_to_async(self.syncSetVariable)(name, text=text, label=label, date=date, integer=integer, file=file)

    def syncGetPostsOnTimestamp(self, timestamp):
        posts = Post.objects.filter(timestamp=timestamp)
        return posts, len(posts)
    def syncGetTodaysPosts(self):
        return self.syncGetPostsOnTimestamp(getTodaysTimestamp())
    async def getTodaysPosts(self):
        return await sync_to_async(self.syncGetTodaysPosts)()

    def syncGetUser(self, index):
        users = User.objects.filter(discord_username=index)
        if (len(users) < 1):
            return None
        return users[0]
    
    def syncCreatePost(self, owner, file, title, isVideo=False, is_nsfw=False):
        if isVideo:
            return Post.objects.create(owner=owner, video=file, title=title, is_nsfw=is_nsfw)
        else:
            return Post.objects.create(owner=owner, image=file, title=title, is_nsfw=is_nsfw)

    async def createPost(self, owner, file, title, isVideo=False, is_nsfw=False):
        return await sync_to_async(self.syncCreatePost)(owner, file, title, isVideo, is_nsfw)

    def syncDeletePost(self, owner, id):
        Post.objects.get(owner=owner, id=id).delete()
        
    async def deletePost(self, owner, id):
        await sync_to_async(self.syncDeletePost)(owner, id)

    async def getUser(self, index):
        try:
            return await sync_to_async(self.syncGetUser)(index)
        except ObjectDoesNotExist as e:
            return None
        
    async def validateUser(self, username, context):
        user = await self.getUser(username)
        if not user or not user.is_a_participant:
            await self.sendUserReply("Sorry, but you are not allowed to interact with this bot", context)
            logger.error("Rejected request from {}: Not in the registered list".format(username))
            return None
        
        return user

    async def sendUserReply(self, message, context):
        await context.message.reply(message)
    
    async def sendMessageOnChannel(self, channel : str, message : str):
        ch = None
        for c in bot.bot.get_all_channels():
            if c.name == channel:
                ch = c
                break
        if not ch:
            raise IOError("Cannot find channel \"{}\"".format(channel))
        await ch.send(message)

    
    async def downloadFile(self, filePath, attachment):
        await attachment.save(open(filePath, "wb"))

    async def createPostFromUser(self, user, title, fileName, context, attachment, isVideo=False, is_nsfw=False):
        logger.info('Received post request from user {}'.format(user.username))

        if title:
            title = title[:Post._meta.get_field('title').max_length]
        else:
            title = ""

        try:
            absolutePath = settings.MEDIA_ROOT + "/" + fileName
            await self.downloadFile(absolutePath, attachment)

            post = await self.createPost(user, fileName, title, isVideo=isVideo, is_nsfw=is_nsfw)

            await self.sendUserReply("File succesfully uploaded!\nHere's the link to your new post: " + settings.SITE_URL + "post/" + post.id + "", context)
        
        except Exception as e:
            logger.error("Cannot create image post for user {}: {}".format(user.username, str(e)))
            await self.sendUserReply("Cannot upload requested file due to an internal error", context)
            if os.path.exists(absolutePath):
                os.remove(absolutePath)

bot = DiscordBot()

# Post Command
@bot.bot.command(name='post', pass_context=True)
async def postCommand(context, *, arg=None):
    # try:
        await createPost(context, arg)
    # except Exception as e:
    #     logger.error("Error on post: {}".format(str(e)))
    #     await bot.sendUserReply("Sorry, but I couldn't create your post due to an internal error, please try again later", context)

async def createPost(context, arg=None):
    username = str(context.message.author)
    title = arg
    isVideo = False

    if not title:
        title = ""
    user = await bot.validateUser(username, context)
    if not user:
        return

    attachmentCount = len(context.message.attachments)
    if attachmentCount < 1:
        await bot.sendUserReply('Cannot create post since no attachment was provided :p', context)
        return
    
    i = 0
    for attachment in context.message.attachments:
        is_nsfw = attachment.is_spoiler()
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
            await bot.createPostFromUser(user, title + " (" + str(i) + "/" + str(attachmentCount)+ ")", fileName, context, attachment, isVideo=isVideo, is_nsfw=is_nsfw)
        else:
            await bot.createPostFromUser(user, title, fileName, context, attachment, isVideo=isVideo, is_nsfw=is_nsfw)

# Delete Command
@bot.bot.command(name='delete', pass_context=True)
async def deleteCommand(context, link):
    try:
        await deletePost(context, link)
    except Exception as e:
        logger.error("Error on delete: {}".format(str(e)))
        await bot.sendUserReply("Sorry, but I couldn't delete your post due to an internal error, please try again later", context)

async def deletePost(context, link):
    username = str(context.message.author)
    user = await bot.validateUser(username, context)
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

# Reminder
async def sendReminder():
    try:
        reminder = await bot.getReminder()
        await bot.sendMessageOnChannel(reminder.label, "@everyone " + reminder.text + " (Day {})".format(await sync_to_async(getDaysFromStartDate)()))
    except Exception as e:
        logger.error("Cannot send reminder: {}".format(str(e)))

async def sendTodaysPostCount():
    try:
        post_count_message = await bot.getVariable("PostCountMessage")
        posts, posts_size = await bot.getTodaysPosts()
        await bot.sendMessageOnChannel(post_count_message.label, "@everyone I have received a grand total of {} {}!, and with that we conclude today's session.\nSee you tomorrow!".format(posts_size, "posts" if posts_size != 1 else "post"))
    except Exception as e:
        logger.error("Cannot send post count: {}".format(str(e)))

@bot.bot.event
async def on_ready():
    try:
        scheduler = AsyncIOScheduler()
        reminder = await bot.getReminder()
        post_count_message = await bot.getVariable("PostCountMessage")

        reminder.date = timezone.localtime(reminder.date)
        post_count_message.date = timezone.localtime(post_count_message.date)

        scheduler.add_job(sendReminder, CronTrigger(hour=reminder.date.hour, minute=reminder.date.minute, second=reminder.date.second)) 
        logger.info("Reminder message set to be sent every day at {}:{}:{}".format(reminder.date.hour, reminder.date.minute, reminder.date.second))
        scheduler.add_job(sendTodaysPostCount, CronTrigger(hour=post_count_message.date.hour, minute=post_count_message.date.minute, second=post_count_message.date.second)) 
        logger.info("Post count message set to be sent every day at {}:{}:{}".format(post_count_message.date.hour, post_count_message.date.minute, post_count_message.date.second))

        scheduler.start()
    except Exception as e:
        logger.error("Cannot setup reminder: {}".format(str(e)))

@bot.bot.command(name="set_reminder", pass_context=True)
async def setReminder(context, *, arg):
    try:
        if not await bot.validateUser(str(context.message.author), context):
            return

        await bot.setReminder(arg)
        await bot.sendUserReply('Reminder message changed!', context)
    except Exception as e:
        logger.error("Cannot set reminder: {}".format(str(e)))
        await bot.sendUserReply('Sorry, but I couldn\'t change the reminder message due to an internal errror', context)


# Entrypoint
class Command(BaseCommand):
    def handle(self, *args, **options):
        load_dotenv()

        bot.bot.run(settings.DISCORD_API_TOKEN)