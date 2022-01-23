from urllib.parse import urlparse
from discord.ext import commands
from dotenv import load_dotenv

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .globals import *
from .utils import *

class OnesketchadayBot(commands.Bot):
    # Commands
    def add_commands(self):
        @commands.command(name='post')
        async def post_command(context, *, arg=None):
            await self.create_post(context, arg)
        self.add_command(post_command)

        @commands.command(name='delete')
        async def delete_command(context, link):
            try:
                await self.delete_post(context, link)
            except Exception as e:
                logger.error("Error on delete: {}".format(str(e)))
                await self.send_reply_to_user("Sorry, but I couldn't delete your post due to an internal error, please try again later", context)
        self.add_command(delete_command)

        @commands.command(name="set_reminder")
        async def set_reminder_command(context, *, arg):
            try:
                if not await self.validate_user(str(context.message.author), context):
                    return

                await set_reminder(arg)
                await self.send_reply_to_user('Reminder message has been changed!', context)
            except Exception as e:
                logger.error("Cannot set reminder: {}".format(str(e)))
                await self.send_reply_to_user('Sorry, but I couldn\'t change the reminder message due to an internal errror', context)
        self.add_command(set_reminder_command)
    
        @commands.command(name="set_bio")
        async def set_bio_command(context, *, arg=None):
            await self.set_user_bio(context, arg)
        self.add_command(set_bio_command)

    # Internals
    def __init__(self):
        super().__init__(command_prefix='.', description="A bot for the https://onesketchaday.art website")

        load_dotenv()
        self.add_commands()

    async def on_ready(self):
        try:
            scheduler = AsyncIOScheduler()
            reminder = await get_reminder()
            post_count_message = await get_variable("PostCountMessage")

            reminder.date = timezone.localtime(reminder.date)
            post_count_message.date = timezone.localtime(post_count_message.date)

            scheduler.add_job(self.send_reminder, CronTrigger(hour=reminder.date.hour, minute=reminder.date.minute, second=reminder.date.second)) 
            logger.info("Reminder message set to be sent every day at {}:{}:{}".format(reminder.date.hour, reminder.date.minute, reminder.date.second))
            scheduler.add_job(self.send_todays_post_count, CronTrigger(hour=post_count_message.date.hour, minute=post_count_message.date.minute, second=post_count_message.date.second)) 
            logger.info("Post count message set to be sent every day at {}:{}:{}".format(post_count_message.date.hour, post_count_message.date.minute, post_count_message.date.second))

            scheduler.start()
        except Exception as e:
            logger.error("Cannot setup reminder: {}".format(str(e)))

    async def send_reply_to_user(self, message, context):
        await context.message.reply(message)
    
    async def validate_user(self, discord_username, context):
        user = await get_user(discord_username)
        if not user or not user.is_a_participant:
            await self.send_reply_to_user("Sorry, but you are not allowed to interact with this bot", context)
            logger.error("Rejected request from {}: Not in the registered list".format(discord_username))
            return None
        
        return user

    async def send_message_on_channel(self, channel : str, message : str):
        ch = None
        for c in self.get_all_channels():
            if c.name == channel:
                ch = c
                break
        if not ch:
            raise IOError("Cannot find channel \"{}\"".format(channel))
        await ch.send(message)


    async def download_file(self, filePath, attachment):
        absolute_path = settings.MEDIA_ROOT + "/" + filePath
        await attachment.save(open(absolute_path, "wb"))
        return absolute_path

    async def create_post_from_user(self, user, title, file_name, context, attachment, is_video=False, is_nsfw=False):
        logger.info('Received post request from user {}'.format(user.username))

        if title:
            title = title[:Post._meta.get_field('title').max_length]
        else:
            title = ""

        absolute_path = ""
        try:
            absolute_path = await self.download_file(file_name, attachment)

            post = await create_post(owner = user, title = title, is_nsfw = is_nsfw)
            if is_video:
                post.video = file_name
            else:
                post.image = file_name
            await save_post(post)

            await self.send_reply_to_user("File succesfully uploaded!\nHere's the link to your new post: " + await get_post_page(post), context)
        
        except Exception as e:
            logger.error("Cannot create image post for user {}: {}".format(user.username, str(e)))
            await self.send_reply_to_user("Cannot upload requested file due to an internal error", context)
            if post:
                await delete_post(post)

    async def set_user_bio(self, context, arg=None):
        username = str(context.message.author)
        bio = arg

        if not bio:
            await self.send_reply_to_user('Kinda hard to set your bio if you don\'t say what your bio is first', context)
        user = await self.validate_user(username, context)
        if not user:
            return
        
        attachment_count = len(context.message.attachments)

        file_name = ""
        if attachment_count > 0:
            if attachment_count > 1:
                await self.send_reply_to_user('I can only use one attachment, so I will only use the first one your provided ;)', context)

            attachment = context.message.attachments[0]
            file_name = attachment.filename
            for e in IMAGE_EXTENSIONS:
                if e in file_name:
                    ext = e
                    break
            if ext == "":
                await self.send_reply_to_user('Can only accept attachments with the following extensions: {}'.format(', '.join(IMAGE_EXTENSIONS)), context)
                return
            file_name = str(attachment.id) + ext

        absolute_path = ""
        try:
            if file_name:
                absolute_path = await self.download_file(file_name)
                user.image = absolute_path
            user.biography = bio
            await save_user(user)

            await self.send_reply_to_user("Done! You can now check your biography at {}".format(await get_user_page(user)), context)
        except Exception as e:
            logger.error("Cannot set user bio for user {}: {}".format(user.username, str(e)))
            await self.send_reply_to_user("Couldn't set your bio due to an internal error ;p", context)
            if os.path.exists(absolute_path):
                os.remove(absolute_path)

    async def create_post(self, context, arg=None):
        username = str(context.message.author)
        title = arg
        is_video = False

        if not title:
            title = ""
        user = await self.validate_user(username, context)
        if not user:
            return

        attachment_count = len(context.message.attachments)
        if attachment_count < 1:
            await self.send_reply_to_user('Cannot create post since no attachment was provided :p', context)
            return
        
        i = 0
        for attachment in context.message.attachments:
            is_nsfw = attachment.is_spoiler()
            file_name = attachment.filename
            ext = ""

            for e in IMAGE_EXTENSIONS:
                if e in file_name:
                    ext = e
                    break

            for e in VIDEO_EXTENSIONS:
                if e in file_name:
                    ext = e
                    is_video = True
                    break
            
            if ext == "":
                await self.send_reply_to_user('Can only accept attachments with the following extensions: {}'.format(', '.join(IMAGE_EXTENSIONS)), context)
                return
            file_name = str(attachment.id) + ext

            i = i + 1
            if attachment_count > 1:
                title = title + " (" + str(i) + "/" + str(attachment_count)+ ")"
            
            await self.create_post_from_user(user, title, file_name, context, attachment, is_video=is_video, is_nsfw=is_nsfw)

    async def delete_post(self, context, link):
        username = str(context.message.author)
        user = await self.validate_user(username, context)

        if not user:
            return

        if not link:
            await self.send_reply_to_user('I need the link to your post first', context)
            return

        try:
            id = urlparse(link).path.rsplit("/", 1)[-1]
            await delete_post(user, id)

            await self.send_reply_to_user('Done!', context)
        except Exception as e:
            logger.error("Cannot delete post on link \"{}\" from user {}: {}".format(link, username, str(e)))
            await self.send_reply_to_user('Sorry, but none of your posts match that link', context)

    async def send_reminder(self):
        try:
            reminder = await get_reminder()
            await self.send_message_on_channel(reminder.label, "@everyone " + reminder.text + " (Day {})".format(await sync_to_async(getDaysFromStartDate)()))
        except Exception as e:
            logger.error("Cannot send reminder: {}".format(str(e)))

    async def send_todays_post_count(self):
        try:
            post_count_message = await get_variable("PostCountMessage")
            posts, posts_size = await get_todays_posts()
            await self.send_message_on_channel(post_count_message.label, "@everyone I have received a grand total of {} {}!, and with that we conclude today's session.\nSee you tomorrow!".format(posts_size, "posts" if posts_size != 1 else "post"))
        except Exception as e:
            logger.error("Cannot send post count: {}".format(str(e)))