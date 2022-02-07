from glob import escape
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
        @commands.command(name='post', brief="post [title] ATTACHMENT", description="Creates a post based on the provided attachments. The text provided by the message would be used as the post's title")
        async def post_command(context, *, arg=None):
            await self.create_post(context, arg)
        self.add_command(post_command)

        @commands.command(name='delete', brief="delete POST_URL", description="Deletes your post from the site. The text provided with the message most be a link to your post")
        async def delete_command(context, link):
            try:
                await self.delete_post(context, link)
            except Exception as e:
                logger.error("Error on delete: {}".format(str(e)))
                await self.send_reply_to_user("Sorry, but I couldn't delete your post due to an internal error, please try again later", context)
        self.add_command(delete_command)

        @commands.command(name="set_reminder", brief="set_reminder REMINDER", description="Sets the reminder message that will be sent every day by the bot (not the posts count message)")
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
    
        @commands.command(name="set_bio", brief="set_bio BIOGRAPHY [ATTACHMENT]", description="Sets your biography and profile picture based on the provided message and attachment. Only the first attachment will be used for your bio. Your biography will only show up in the participants page if you set both your bio and profile picture")
        async def set_bio_command(context, *, arg=None):
            await self.set_user_bio(context, arg)
        self.add_command(set_bio_command)

        @commands.command(name="clear_bio", brief="clear_bio", description="Clears your biography. If you don't have a biography, your name won't show up on the participants page (you will still be able to make posts however)")
        async def clear_bio_command(context):
            await self.clear_user_bio(context)
        self.add_command(clear_bio_command)

        @commands.command(name="commands", brief="commands [COMMAND]", description="Send a list of all the available commands")
        async def commands_command(context, command=None):
            await self.send_commands(context, command)
        self.add_command(commands_command)

    # Internals
    def __init__(self):
        super().__init__(command_prefix='.', description="A bot for the https://onesketchaday.art website")

        load_dotenv()
        self.add_commands()

    # Creates the scheduler and adds the scheduled messages to it
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

    # Send a message with all the available commands
    async def send_commands(self, context, arg=None):
        username = str(context.message.author)
        user = await self.validate_user(username, context)
        if not user:
            return

        if arg:
            for command in self.walk_commands():
                if command.name == arg:
                    await self.send_reply_to_user("```{}{} \n{}```".format(self.command_prefix, command.brief, command.description), context)
                    return
            await self.send_reply_to_user("\"{}\" is not an available command".format(arg), context)
            return
        else:
            command_list = "```\nCommands:\n"
            for command in self.walk_commands():
                if not command.brief:
                    continue
                command_list += "{}{}\n".format(self.command_prefix, command.brief)
            command_list += "\nNotes:\n"
            command_list += "VAL    Means that including VAL value is mandatory\n"
            command_list += "[VAL]  Means that including VAL value is optional\n"
            command_list += "```"
            await self.send_reply_to_user(command_list, context)

    # Reply to user message
    async def send_reply_to_user(self, message, context):
        await context.message.reply(message)
    
    # See if user is authorized to use this bot. If they are not, return None.
    # If they are, return an user object for that username
    async def validate_user(self, discord_username, context):
        user = await get_user(discord_username)
        if not user or not user.is_a_participant:
            await self.send_reply_to_user("Sorry, but you are not allowed to interact with this bot", context)
            logger.error("Rejected request from {}: Not in the registered list".format(discord_username))
            return None
        
        return user

    # Send message on the specified channel
    async def send_message_on_channel(self, channel : str, message : str):
        ch = None
        for c in self.get_all_channels():
            if c.name == channel:
                ch = c
                break
        if not ch:
            raise IOError("Cannot find channel \"{}\"".format(channel))
        await ch.send(message)

    # Download attachment on MEDIA_ROOT
    async def download_file(self, file_path, attachment):
        absolute_path = settings.MEDIA_ROOT + "/" + file_path
        await attachment.save(open(absolute_path, "wb"))
        return absolute_path

    # Create an user post based on an attachment
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
            await self.send_reply_to_user("Sorry I couldn't create your post due to an internal error", context)
            if post:
                await delete_post(post)

    # Remove the biography and profile picture from the user
    async def clear_user_bio(self, context):
        username = str(context.message.author)
        user = await self.validate_user(username, context)
        if not user:
            return
        
        try:
            await sync_to_async(user.delete_profile_picture)()

            user.biography = ""
            user.profile_picture = ""

            await save_user(user)
        
            await self.send_reply_to_user("Done!, your biography has been cleared. It will no longer show up in the participants page", context)
        except Exception as e:
            logger.error("Cannot clear biography for {}: {}".format(user.username, str(e)))
            await self.send_reply_to_user("Sorry, I couldn't clear your biography due to an internal error", context)

    # Set the user biography and profile picture
    async def set_user_bio(self, context, arg=None):
        username = str(context.message.author)
        attachment = None
        bio = arg

        # The user needs to at least provide a biography
        if not bio:
            await self.send_reply_to_user('Kinda hard to set your bio if you don\'t say what your bio is first', context)
            return
        user = await self.validate_user(username, context)
        if not user:
            return
        
        attachment_count = len(context.message.attachments)

        # Only use the frist attachment
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

        # Try downloading the picture and attach it to the user
        absolute_path = ""
        try:
            if file_name:
                absolute_path = await self.download_file(file_name, attachment)
                user.profile_picture = file_name
            user.biography = bio
            await save_user(user)

            await self.send_reply_to_user("Done! You can now check your biography at {}".format(await get_user_page(user)), context)
        except Exception as e:
            logger.error("Cannot set bio for user {}: {}".format(user.username, str(e)))
            await self.send_reply_to_user("Couldn't set your bio due to an internal error ;p", context)
            if os.path.exists(absolute_path):
                os.remove(absolute_path)

    # Create an user based on the user message. The args are going to be used for the
    # post's title
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
            post_title = ""
            if attachment_count > 1:
                post_title = title + " (" + str(i) + "/" + str(attachment_count)+ ")"
            else:
                post_title = title
            
            await self.create_post_from_user(user, post_title, file_name, context, attachment, is_video=is_video, is_nsfw=is_nsfw)

    # Delete the users post based on the link provided to that post. Only the owner of those posts can delete them.
    # TODO: Maybe allow the admins to delete any posts also
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

    # Set the reminder message
    async def send_reminder(self):
        try:
            reminder = await get_reminder()
            await self.send_message_on_channel(reminder.label, "@everyone " + reminder.text + " (Day {})".format(await sync_to_async(getDaysFromStartDate)()))
        except Exception as e:
            logger.error("Cannot send reminder: {}".format(str(e)))

    # Send the daily message with the amount of posts received that day
    async def send_todays_post_count(self):
        try:
            post_count_message = await get_variable("PostCountMessage")
            posts, posts_size = await get_todays_posts()
            await self.send_message_on_channel(post_count_message.label, "@everyone I have received a grand total of {} {}!, and with that we conclude today's session.\nSee you tomorrow!".format(posts_size, "posts" if posts_size != 1 else "post"))
        except Exception as e:
            logger.error("Cannot send post count: {}".format(str(e)))