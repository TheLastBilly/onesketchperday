from urllib.parse import urlparse

import discord
from discord.ext import commands
from dotenv import load_dotenv

import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from django.utils import timezone

from .globals import *
from .utils import *

NEW_MEMBER_TAG="NEW_MEMBER"
MAX_DISCORD_MESSAGE_LEN = 2000

class OnesketchadayBot(commands.Bot):
    # Commands
    def add_commands(self):
        @commands.command(name='post', brief="post [TITLE] ATTACHMENT", description="Creates a post based on the provided attachments. The text provided by the message would be used as the post's title")
        async def post_command(context, *, arg=None):
            await self.create_post(context, arg)
        self.add_command(post_command)

        @commands.command(name='delete', brief="delete URL", description="Deletes your post from the site. The text provided with the message most be a link to your post")
        async def delete_command(context, link):
            try:
                await self.delete_post(context, link)
            except Exception as e:
                logger.error("Error on delete: {}".format(str(e)))
                await self.send_reply_to_user("Sorry, but I couldn't delete your post due to an internal error, please try again later", context)
        self.add_command(delete_command)

        @commands.command(name="reminder", brief="reminder REMINDER", description="Sets the reminder message that will be sent every day by the bot (not the posts count message)")
        async def set_reminder_command(context, *, arg):
            try:
                if not await self.validate_user(context):
                    return

                await set_reminder(arg)
                await self.send_reply_to_user('Reminder message has been changed!', context)
            except Exception as e:
                logger.error("Cannot set reminder: {}".format(str(e)))
                await self.send_reply_to_user('Sorry, but I couldn\'t change the reminder message due to an internal errror', context)
        self.add_command(set_reminder_command)
    
        @commands.command(name="bio", brief="bio BIOGRAPHY [ATTACHMENT]", description="Sets your biography and profile picture based on the provided message and attachment. Only the first attachment will be used for your bio. Your biography will only show up in the participants page if you set both your bio and profile picture")
        async def set_bio_command(context, *, arg=None):
            await self.set_user_bio(context, arg)
        self.add_command(set_bio_command)

        @commands.command(name="incognito", brief="incognito", description="Clears your biography. If you don't have a biography, your name won't show up on the participants page (you will still be able to make posts however)")
        async def clear_bio_command(context):
            await self.clear_user_bio(context)
        self.add_command(clear_bio_command)
        
        @commands.command(name="hurry", brief="hurry", description="Shows the time left before the end of the current session")
        async def time_left_command(context):
            await self.time_left(context)
        self.add_command(time_left_command)

        @commands.command(name="commands", brief="commands [COMMAND]", description="Send a list of all the available commands")
        async def commands_command(context, command=None):
            await self.send_commands(context, command)
        self.add_command(commands_command)

        @commands.command(name="manual", brief="manual", description="Shows a list of all the available commands with their full description")
        async def manual_commands(context):
            await self.send_manual(context)
        self.add_command(manual_commands)

        @commands.command(name="strikes", brief="strikes", description="Shows the amount of misses during the current month")
        async def strikes_command(context):
            await self.show_strikes(context)
        self.add_command(strikes_command)

        @commands.command(name="junior", brief="junior ROLE", description="Sets the role that will be assigned to new members by default (only for staff)")
        async def set_new_member_role_command(context, *, arg):
            await self.set_variable_from_command(context, "NewMemberDefaultRole", arg)
        self.add_command(set_new_member_role_command)

        @commands.command(name="welcome", brief="welcome MESSAGE", description=f"Sets message that will be sent to new memebers on arrival (only for staff). Use the {NEW_MEMBER_TAG} to tag the new member")
        async def set_new_member_message_command(context, *, arg):
            await self.set_variable_from_command(context, "NewMembersWelcomeMessage", arg)
        self.add_command(set_new_member_message_command)

        @commands.command(name="greeting", brief="greeting MESSAGE", description=f"Sets message that will be sent on the announcements channel when a new member arrives (only for staff). Use the {NEW_MEMBER_TAG} to tag the new member")
        async def set_new_member_announcement_message_command(context, *, arg):
            await self.set_variable_from_command(context, "NewMembersAnnouncementMessage", arg)
        self.add_command(set_new_member_announcement_message_command)

        @commands.command(name="announcements", brief="announcements CHANNEL", description="Sets the channel that will be used for sending announcements")
        async def set_announcements_channel_command(context, *, arg):
            await self.set_variable_from_command(context, "AnnouncementsChannel", arg)
        self.add_command(set_announcements_channel_command)

        @commands.command(name="schedule", brief=f"schedule CHANNEL {DATETIME_STRING_FORMAT} MESSAGE", description="Schedules message to be send on channel at a future date")
        async def schedule_message_command(context, *, arg):
            await self.schedule_message(context, arg)
        self.add_command(schedule_message_command)

        @commands.command(name="scheduled", brief="scheduled", description="Lists scheduled events/messages")
        async def scheduled_command(context):
            await self.send_scheduled_messages(context)
        self.add_command(scheduled_command)

        @commands.command(name="challenges", brief="challenges", description="Lists scheduled challenges with their id")
        async def challenges_command(context):
            await self.send_scheduled_challenges(context)
        self.add_command(challenges_command)

        @commands.command(name="giveup", brief="giveup CHALLENGE_ID", description="Deletes a challenge")
        async def giveup_command(context, arg):
            await self.giveup_challenge(context, arg)
        self.add_command(giveup_command)

        @commands.command(name="nevermind", brief="nevermind EVENT_NUMBER", description="Removes scheduled message. Please use \"scheduled\" to see a list of all the scheduled messages.")
        async def nevermind_command(context, arg):
            await self.nevermind(context, arg)
        self.add_command(nevermind_command)

        @commands.command(name="challenge", brief="challenge START_DATE END_DATE TITLE:\nDESCRIPTION\n", description="Starts a challenge at the given datetime (can only be used by staff)")
        async def challenge_command(context, *, arg=None):
            await self.challenge(context, arg)
        self.add_command(challenge_command)
    
        @commands.command(name="face", brief="face CHALLENGE_ID [TITLE] ATTACHMENT", description="Used to submit a post for (face) a challenge, works pretty much the same as the post command, with the exception that a challenge ID needs to be included. Posts need to be reated during the challenge's runtime. Challenge IDs can be seen using the \"challenges\" command")
        async def face_command(context, *, arg=None):
            await self.face_challenge(context, arg)
        self.add_command(face_command)

        @commands.command(name="submissions", brief="submissions CHALLENGE_ID", description="Lists all the submissions made for a challenge")
        async def list_submissions_command(context, *, arg=None):
            await self.list_submissions(context, arg)
        self.add_command(list_submissions_command)

        @commands.command(name="pardon", brief=f"pardon USERNAME {DATE_STRING_FORMAT}", description="Allows an user to skip a day (can only be used by staff). Timestamp must be on numeric [YEAR][MONTH][FORMAT].")
        async def pardon_command(context, *, arg=None):
            await self.pardon(context, arg)
        self.add_command(pardon_command)

        @commands.command(name="refresh", brief=f"refresh", description="Syncs messages and other elements of the bot with the current state of the database (can only be used by staff)")
        async def refresh_command(context, arg=None):
            user = await self.validate_staff_user(context)

            if not user:
                return

            try:
                await self.update_scheduled_messages()
                await self.send_reply_to_user("Done!", context)
            except Exception:
                await self.send_reply_to_user("There seems to have been an error, please try again later", context)

        self.add_command(refresh_command)
   
    async def on_member_join(self, member):
        role_name = await get_new_member_role()
        announcements_channel = await get_announcements_channel()

        new_member_message = await get_new_member_message()
        announcements_message = await get_new_member_announcement_message()

        try:
            new_member_message = new_member_message.replace(NEW_MEMBER_TAG, f"{member.mention}")
        except:
            pass

        try:
            announcements_message = announcements_message.replace(NEW_MEMBER_TAG, f"{member.mention}")
        except:
            pass

        role = discord.utils.get(member.guild.roles, name=role_name)
        await member.add_roles(role)

        await self.send_message_on_channel(announcements_channel, announcements_message)
        await member.send(new_member_message)

    # Internals
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content=True

        super().__init__(command_prefix='.', description="A bot for the https://onesketchaday.art website", intents=intents)

        load_dotenv()
        self.add_commands()

    # Creates the scheduler and adds the scheduled messages to it
    async def on_ready(self):
        self.scheduled_messages_jobs = {}

        self.message_scheduler = AsyncIOScheduler()
        self.announcements_scheduler = AsyncIOScheduler()

        reminder = await get_reminder()
        post_count_message = await get_variable("PostCountMessage")

        # Setup reminders
        reminder.date = timezone.localtime(reminder.date)
        post_count_message.date = timezone.localtime(post_count_message.date)
        self.announcements_scheduler.add_job(self.send_reminder, CronTrigger(
            hour=reminder.date.hour, minute=reminder.date.minute, second=reminder.date.second)
        ) 
        logger.info("Reminder message set to be sent every day at {}:{}:{}".format(
            reminder.date.hour, reminder.date.minute, reminder.date.second
        ))
        self.announcements_scheduler.add_job(self.send_todays_post_count, CronTrigger(
            hour=post_count_message.date.hour, minute=post_count_message.date.minute, second=post_count_message.date.second
        )) 
        logger.info("Post count message set to be sent every day at {}:{}:{}".format(
            post_count_message.date.hour, post_count_message.date.minute, post_count_message.date.second
        ))

        self.announcements_scheduler.start()
        self.message_scheduler.start()

        await self.update_scheduled_messages()
    
    async def set_variable_from_command(self, context, variable, arg):
        user = await self.validate_staff_user(context)

        if not user or not arg:
            return
        
        def set_message():
            message = Variable.objects.get(name=variable)
            message.text = arg

            message.save()
        
        try:
            await sync_to_async(set_message)()
            await self.send_reply_to_user("Done!", context)
        except:
            await self.send_reply_to_user("There seems to be a problem with the backend, please try again later", context)
    
    async def list_submissions(self, context, arg):
        user = await self.validate_user(context)

        if not user:
            return

        if not arg:
            await self.send_commands(context, "submissions")
            return
        
        challenge = await sync_to_async(Challenge.objects.filter)(id=arg)
        challenge = await sync_to_async(challenge.first)()
        if not challenge:
            await self.send_reply_to_user(f"Sorry, but I couldn't find any challenges with that ID", context)
            return
        
        submissions = await get_challenge_submissions(challenge)

        if len(submissions) < 1:
            await self.send_reply_to_user("No submissions have been made yet!", context)
            return

        message = "```\n"
        message += f"Submisssions for the {challenge.title} challenge:\n\n"
        for i,submission in enumerate(submissions):
            url = await sync_to_async(submission.get_page)()
            
            def get_owner():
                return submission.owner.username
            owner = await sync_to_async(get_owner)()

            message += f"{i+1}.- {url} by {owner}\n"
        message += "```"

        await self.send_reply_to_user(message, context)

    async def giveup_challenge(self, context, arg):
        user = await self.validate_user(context)

        if not user:
            return
        
        challenge = await sync_to_async(Challenge.objects.filter)(id=arg)
        challenge = await sync_to_async(challenge.first)()
        if not challenge:
            await self.send_reply_to_user(f"Sorry, but I couldn't find any challenges with that ID", context)
            return
        
        await sync_to_async(challenge.delete)()
        await self.update_scheduled_messages()

        await self.send_reply_to_user(f"Challenge \"{challenge.title}\" has been deleted!", context)

    async def face_challenge(self, context, arg):
        user = await self.validate_user(context)

        if not user:
            return
            
        args = []
        if arg:
            args = arg.split(" ")
        if len(args) < 1:
            await self.send_commands(context, "face")
            return
        
        try:
            challenge_id = args[0]
            
            challenge = await get_challenge(challenge_id)
            if not challenge:
                await self.send_reply_to_user(f"Sorry, but I couldn't find any challenges with that ID", context)
                return
        
            now = timezone.localtime()
            
            if now >= challenge.start_date and now <= challenge.end_date:
                title = " ".join(args[1:]) if len(args) > 1 else ""
                posts = await self.create_post(context, title)

                for post in posts:
                    if not post:
                        return
                    await sync_to_async(challenge.add_submission)(post)

                s = "s" if len(posts) > 1 else ""
                await self.send_reply_to_user(f"Your post{s} have been submited to the \"{challenge.title}\" challenge!", context)
                return
            else:
                await self.send_reply_to_user("Sorry, but I can only accept posts created during the challenge's runtime", context)
                return
            
        except Exception as e:
            await self.send_reply_to_user(f"Cannot add post to challenge submissions: \"{e}\"", context)

    async def send_scheduled_messages(self, context):
        user = await self.validate_user(context)

        if not user:
            return

        programmed_events = []
        try:
            programmed_events = await get_programmed_events()
        except:
            await self.send_reply_to_user("Looks like something went wrong, please try again later", context)
            return
        
        message = ""

        if len(programmed_events):     
            message = "```\n"
            for i, scheduled in enumerate(programmed_events):
                message += f"{i+1}.- [{await sync_to_async(scheduled.programmed_date_str)()}] {scheduled.message[:20]}"
                if len(scheduled.message) > 20:
                    message += "..."
                message += "\n"
            message += "```"
        else:
            message = "No events have been scheduled so far"

        await self.send_reply_to_user(message, context)
    
    async def send_scheduled_challenges(self, context):
        user = await self.validate_user(context)

        if not user:
            return

        challenges = []
        try:
            challenges = await get_challenges()
        except:
            await self.send_reply_to_user("Looks like something went wrong, please try again later", context)
            return
        
        i = 0
        message = "Here a list with all the active challenges!\n"
        message += "```\n"
        for scheduled in challenges:
            if scheduled.end_date < timezone.localtime():
                continue
            
            def print_challengers():
                for challenger in scheduled.get_participants():
                    print(challenger)
            await sync_to_async(print_challengers)()

            message += f"{i+1}.- [{await sync_to_async(scheduled.programmed_date_str)()}] [{scheduled.id}] {scheduled.title[:40]}"
            i += 1
            
            if len(scheduled.title) > 20:
                message += "..."
            message += "\n"
        message += "```"
        
        if i < 1:
            message = "No challenges have been scheduled so far"

        await self.send_reply_to_user(message, context)

    async def update_scheduled_messages(self):
        now = timezone.localtime()

        for key in self.scheduled_messages_jobs:
            try:
                self.scheduled_messages_jobs[key].remove()
            except:
                pass
        
        self.scheduled_messages_jobs.clear()
        
        scheduled_messages = await get_programmed_events()

        # Do scheduled messages
        for scheduled_message in scheduled_messages:
            if scheduled_message.programmed_date < now:
                await sync_to_async(scheduled_message.delete)()
                continue

            async def sendScheduledMessage():
                await self.send_message_on_channel(scheduled_message.channel, scheduled_message.message)
                await sync_to_async(scheduled_message.delete)()
            
            datetime = timezone.localtime(scheduled_message.programmed_date)

            job = self.message_scheduler.add_job(sendScheduledMessage, CronTrigger(
                hour=datetime.hour, minute=datetime.minute, second=datetime.second, year=datetime.year, month=datetime.month, day=datetime.day 
            ))

            self.scheduled_messages_jobs.update({scheduled_message.id : job})
        
        challenges = await get_challenges()
        announcements_channel = await get_announcements_channel()

        # Do challenges messages
        for challenge in challenges:
            start_time = await get_variable("ChallengesStartTime")
            end_time = await get_variable("ChallengesEndTime")

            challenge.start_date = timezone.localtime(challenge.start_date)
            challenge.end_date = timezone.localtime(challenge.end_date)

            # If dates are not valid, move on to the next challenge
            if challenge.start_date < now or challenge.start_date > challenge.end_date:
                continue
                
            start_date_str = await sync_to_async(challenge.get_start_date_str)()
            end_date_str = await sync_to_async(challenge.get_end_date_str)()

            async def startChallenge(challenge):
                message = "Hello @everyone, we have a new challenge for you today!\n\n"

                message += f"**{challenge.title}**\n"
                message += f"{challenge.description}\n\n"

                message += f"This challenge will start on the **{start_date_str}** and will end on the **{end_date_str}**"

                await self.send_message_on_channel(announcements_channel, message)
            
            datetime = challenge.start_date

            job = self.message_scheduler.add_job(startChallenge, args=[challenge], trigger=CronTrigger(
                hour=datetime.hour, minute=datetime.minute, second=datetime.second, 
                year=datetime.year, month=datetime.month, day=datetime.day 
            ))
            self.scheduled_messages_jobs.update({f"start_{challenge.id}_{datetime}" : job})

            async def endChallenge(challenge):
                participants = await sync_to_async(challenge.get_participants)()
                pardons_per_challenge = await get_variable("PardonsPerChallenge")
                pardons_per_challenge = pardons_per_challenge.integer
    
                message = f"@everyone Aaaaaand it's done!, the **{challenge.title}** challenge is over!\n"

                if len(participants) > 0:
                    message += f"Here are the winners:\n"

                    for (participant, posts) in participants:
                        discord_recipient = await self.fetch_user(int(participant.discord_id))
                        s = "s" if len(posts) > 1 else ""
                        message += f"{discord_recipient.mention} with {len(posts)} submission{s}!\n"

                    await sync_to_async(challenge.pardon_participants)(pardons_per_challenge)

                    s = "s" if pardons_per_challenge > 0 else ""
                    message += f"They have all received {pardons_per_challenge} pardon{s} each!"

                await self.send_message_on_channel(announcements_channel, message)

            datetime = challenge.end_date

            job = self.message_scheduler.add_job(endChallenge, args=[challenge], trigger=CronTrigger(
                hour=datetime.hour, minute=datetime.minute, second=datetime.second, 
                year=datetime.year, month=datetime.month, day=datetime.day 
            ))
            self.scheduled_messages_jobs.update({f"end_{challenge.id}_{datetime}" : job})

        # Do misc messages

        # First of month message
        first_of_next_month = await sync_to_async(getFirstOfNextMonth)()
        first_of_month_message = await get_variable("BeginningOfTheMonthMessage")

        async def sendFirstOfMonthMessage():
            print("This is is a test" + first_of_month_message.text)
            await self.send_message_on_channel(announcements_channel, first_of_month_message.text)
        
        datetime = timezone.localtime(first_of_month_message.date)
        job = job = self.message_scheduler.add_job(sendFirstOfMonthMessage, CronTrigger(
            hour=datetime.hour, minute=datetime.minute, second=datetime.second, 
            year=now.year, month=now.month, day=1
        ))

        self.scheduled_messages_jobs.update({f"First of Next Month" : job})

    async def challenge(self, context, arg=None):
        start_date, end_date, title, description = None, None, None, None

        user = await self.validate_staff_user(context)
        if not user:
            return

        try:
            args = arg.split()
            start_date = await get_date_from_string(args[0])
            end_date = await get_date_from_string(args[1])

            text = " ".join(args[2:]).split(":")
            title = text[0]
            description = "\n".join(text[1:])
        except Exception as e:
            await self.send_commands(context, "challenge")
            return
        
        try:
            start_date = timezone.localtime(start_date)
            end_date = timezone.localtime(end_date)

            start_time = timezone.localtime((await get_variable("ChallengesStartTime")).date)
            end_time = timezone.localtime((await get_variable("ChallengesEndTime")).date)

            start_date = start_date.replace(hour=start_time.hour, minute=start_time.minute, second=start_time.second)
            end_date = end_date.replace(hour=end_time.hour, minute=end_time.minute, second=end_time.second)
            
        except Exception as e:
            await self.send_reply_to_user("Sorry, but I cannot create challenges at the moment, please try again later", context)
            logger.error(f"cannot create challenge right now: {str(e)}")
            return
        
        if start_date < timezone.localtime():
            await self.send_reply_to_user("Sorry, but I cannot create challenges that start in the past", context)
            return

        if end_date < start_date:
            await self.send_reply_to_user("The end date cannot come before the start date bud!", context)
            return
        
        if end_date < await sync_to_async(timezone.localtime)():
            await self.send_reply_to_user("Sorry, but I can't create challenges that end in the past", context)
            return
        
        challenge = await self.create_challenge(title=title, description=description,
            start_date=start_date, end_date=end_date)
        
        start_date_str = await sync_to_async(challenge.get_start_date_str)()
        end_date_str = await sync_to_async(challenge.get_end_date_str)()
        message = f"Done!, your challenge has been scheduled to start on the {start_date_str}, and will end on the {end_date_str}"

        await self.send_reply_to_user(message, context)

    async def nevermind(self, context, arg):
        user = await self.validate_staff_user(context)

        if not user or not arg:
            return

        index = 0
        try:
            index = int(arg)
        except:
            pass
        
        programmed_events = []
        try:
            programmed_events = await get_programmed_events()
        except:
            await self.send_reply_to_user("Looks like something went wrong, please try again later", context)
            return
        
        if index < 1 or index > len(programmed_events):
            await self.send_reply_to_user("Wrong event number, please check the scheduled events")
            return
        
        datetime_str = await sync_to_async(programmed_events[index-1].programmed_date_str)()
        await sync_to_async(programmed_events[index-1].delete)()

        await self.send_reply_to_user(f"The event scheduled for {datetime_str} has been deleted!", context)

    async def schedule_message(self, context, arg):
        user = await self.validate_staff_user(context)

        args = arg.split() if arg else []
        if not user or len(args) < 3:
            return

        print(args)
        channel = args[0]
        datetime = await get_datetime_from_string(args[1])
        message = " ".join(args[2:])

        if datetime < timezone.now():
            await self.send_reply_to_user(f"Sorry, but I cannot set reminders for past dates", context)
            return

        event = await self.schedule_message_on_channel(channel, message, datetime)
        await self.send_reply_to_user(f"Message scheduled for {await sync_to_async(event.programmed_date_str)()}", context)

    async def pardon(self, context, arg):
        username = None
        date_str = ""

        if arg:    
            args = arg.split()
            if len(args) > 0:
                username = args[0]
            if len(args) > 1:
                date_str = args[1]

        await self.pardon_user(context, username=username, date_str=date_str)

    async def send_manual(self, context):
        user = await self.validate_user(context)
        if not user:
            return

        command_list = "[OneSketchADay's Bot User Manual]\n\n"
        messages = []
        max_len = MAX_DISCORD_MESSAGE_LEN - 8

        for command in self.walk_commands():
            if not command.brief:
                continue

            c = "Command: {}{}\nDescription:\n\t{}\n\n".format(self.command_prefix, command.brief, command.description)
            if (len(command_list) + len(c)) >= max_len:
                messages.append(command_list)
                command_list = c
            else:
                command_list += c
        command_list += "[Notes]\n"
        command_list +=f"DATE       Must be in the following format: {DATE_STRING_FORMAT}\n"
        command_list +=f"DATETIME   Must be in the following format: {DATETIME_STRING_FORMAT}\n"
        command_list += "VAL        Means that including VAL value is mandatory\n"
        command_list += "[VAL]      Means that including VAL value is optional\n"
        messages.append(command_list)

        for message in messages:
            m = "```\n" + message + "\n```"
            await self.send_reply_to_user(m, context)

    # Send a message with all the available commands
    async def send_commands(self, context, arg=None):
        user = await self.validate_user(context)
        if not user:
            return

        if arg:
            for command in self.walk_commands():
                if command.name == arg:
                    await self.send_reply_to_user("```{}{} \n{}```".format(
                        self.command_prefix, command.brief, command.description), context)
                    return
            await self.send_reply_to_user("\"{}\" is not an available command".format(arg), context)
            return
        else:
            command_list = "```\n[Available Commands]\n\n"
            for command in self.walk_commands():
                if not command.brief:
                    continue
                command_list += f"* {self.command_prefix}{command.brief}\n"
            command_list += "```"

            await self.send_reply_to_user(command_list, context)

    # Reply to user message
    async def send_reply_to_user(self, message, context):
        if not message or len(message) < 1:
            return

        m = message
        while len(m) > 0:
            await context.message.reply(m[:MAX_DISCORD_MESSAGE_LEN])
            m = m[MAX_DISCORD_MESSAGE_LEN+1:]
    
    # See if user is authorized to use this bot. If they are not, return None.
    # If they are, return an user object for that username
    async def validate_user(self, context):
        user = await get_user(context.author.id)
        if not user or not user.is_a_participant:
            await self.send_reply_to_user("Sorry, but you are not allowed to interact with this bot", context)
            logger.error("Rejected request from {}: Not in the registered list".format(str(context.author)))
            return None
        return user
    
    async def create_challenge(self, title : str, description : str, start_date : timezone.localtime, end_date : timezone.localtime):
        challenge = await sync_to_async(Challenge.objects.create)(title=title, description=description, start_date=start_date, end_date=end_date)
        await self.update_scheduled_messages()

        return challenge

    async def validate_staff_user(self, context):
        user = await self.validate_user(context)

        if not user:
            return user
        
        if not user.is_staff:
            await self.send_reply_to_user("Slow down there bucko!, only staff members can use this command", context)
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

    async def schedule_message_on_channel(self, channel : str, message : str, datetime : timezone.datetime):
        event = await sync_to_async(ProgrammedEvent)(channel=channel, message=message, programmed_date=datetime)
        await sync_to_async(event.save)()

        await self.update_scheduled_messages()

        return event

    # Download attachment on MEDIA_ROOT
    async def download_file(self, file_path, attachment):
        absolute_path = settings.MEDIA_ROOT + "/" + file_path
        logger.info("Starting download for \"{}\"".format(absolute_path))
        await attachment.save(open(absolute_path, "wb"))
        logger.info("Done downloading \"{}\"".format(absolute_path))
        return absolute_path

    # Create an user post based on an attachment
    async def create_post_from_user(self, user, title, file_name, context, attachment, is_video=False, is_nsfw=False):
        logger.info('Received post request from user {}'.format(user.username))
        post = None

        if title:
            title = title[:Post._meta.get_field('title').max_length]
        else:
            title = ""

        try:
            await self.download_file(file_name, attachment)
            post = await create_post(owner = user, title = title, is_nsfw = is_nsfw)
            
            if is_video:
                post.video = file_name
            else:
                post.image = file_name
            await save_post(post)

            await self.send_reply_to_user("File succesfully uploaded!\nHere's the link to your new post: " 
                    + await get_post_page(post), context)
            
            return post
        
        except Exception as e:
            logger.error("Cannot create image post for user {}: {}".format(user.username, str(e)))
            await self.send_reply_to_user("Sorry I couldn't create your post due to an internal error", context)
            if post:
                await delete_post(post)

    # Remove the biography and profile picture from the user
    async def clear_user_bio(self, context):
        user = await self.validate_user(context)
        if not user:
            return
        
        try:
            await sync_to_async(user.delete_profile_picture)()

            user.biography = ""
            user.profile_picture = ""

            await save_user(user)
        
            await self.send_reply_to_user(
                "Done!, your biography has been cleared. It will no longer show up in the participants page", context
            )
        except Exception as e:
            logger.error("Cannot clear biography for {}: {}".format(user.username, str(e)))
            await self.send_reply_to_user("Sorry, I couldn't clear your biography due to an internal error", context)

    async def time_left(self, context):
        user = await self.validate_user(context)
        if not user:
            return
        
        try:
            hours, minutes, seconds = await get_session_time_remaining()
            await self.send_reply_to_user("You still have **{:02d} hours**, **{:02d} minutes** and **{:02d} seconds** left to submit your post!".format(hours, minutes, seconds), context)

        except Exception as e:
            logger.error("Cannot retrieve remaining time on todays session for user {}: {}".format(user.username, str(e)))
            await self.send_reply_to_user("Sorry, but I couldn't show you time left on today's session due to an internal error", context)

    async def show_strikes(self, context):
        user = await self.validate_user(context)
        if not user:
            return
        
        try:
            msg = ""
            max_strikes = await get_max_strikes()
            misses = await sync_to_async(user.get_missed_days)()
            miss_count = await sync_to_async(len)(misses)
            
            if miss_count < max_strikes:
                msg += "You are still in the game!"
            else:
                msg += "Aaaaaaaand you're out!"

            msg += f" (you've got {miss_count} strikes out of a max of {max_strikes})"

            if miss_count > 0:
                msg += "\n```\n"
                msg += "Days missed:\n"
                i = 0

                for miss in misses:
                    s = await sync_to_async(miss.strftime)("%d %B, %Y")
                    msg += f"{i+1}: {s}\n"
                    i += 1
                
                msg += "\n```"

            await self.send_reply_to_user(msg, context)
        
        except Exception as e:
            logger.error("Cannot retrieve strikes for \"{}\": {}".format(user.username, str(e)))
            await self.send_reply_to_user("Sorry, but I couldn't retrieve how many strikes you've got right now", context)

    async def pardon_user(self, context, username = None, date_str = None):
        user = await self.validate_staff_user(context)
        if not user:
            return
        
        if not username:
            await self.send_reply_to_user("Who do you want to pardon?", context)
            return

        recipient = await get_user(username = username)
        if not recipient:
            await self.send_reply_to_user(f"Sorry, but I don't know who {username} is", context)
            return
        discord_recipient = await self.fetch_user(int(recipient.discord_id))

        if not date_str:
            await self.send_reply_to_user(f"For which day would you like to pardon {username}?", context)
            return

        try:
            date = await get_date_from_string(date_str)

            pardon = await sync_to_async(Pardon)(user = recipient, date = date)
            date_str = await sync_to_async(pardon.date_str)()
            
            if date < await get_start_date():
                await self.send_reply_to_user(f"Sorry, but the {date_str} happened before the challenge started", context)
                return

            if await sync_to_async(recipient.has_pardon_for_date)(date):
                await self.send_reply_to_user(f"Looks like {discord_recipient.mention} has already received a pardon for the {date_str}!", context)
                return
            
            await sync_to_async(pardon.save)()
            await self.send_reply_to_user(f"Done! {discord_recipient.mention} you will no longer have to worry about making a post on the {date_str}!", context)

        except Exception as e:
            logger.error(f"Cannot pardon {recipient} for {date_str}: {str(e)}")
            await self.send_reply_to_user("Sorry, but I cannot give pardons right now", context)

    # Set the user biography and profile picture
    async def set_user_bio(self, context, arg=None):
        attachment = None
        bio = arg

        # The user needs to at least provide a biography
        if not bio:
            await self.send_reply_to_user('Kinda hard to set your bio if you don\'t say what your bio is first', context)
            return
        user = await self.validate_user(context)
        if not user:
            return
        
        attachment_count = len(context.message.attachments)

        # Only use the frist attachment
        file_name = ""
        if attachment_count > 0:
            if attachment_count > 1:
                await self.send_reply_to_user(
                    'I can only use one attachment, so I will only use the first one your provided ;)', context)

            attachment = context.message.attachments[0]
            file_name = str(attachment.filename).lower()
            for e in IMAGE_EXTENSIONS:
                if file_name.endswith(e):
                    ext = e
                    break
            if ext == "":
                logger.info("File \"{}\" declined due to bad extension".format(file_name)) 
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

    async def program_message(self, context, time, channel, message):
        user = await self.validate_user(context)
        if not user:
            return


    # Create an user based on the user message. The args are going to be used for the
    # post's title
    async def create_post(self, context, arg=None):
        title = arg
        is_video = False

        channel_name = context.channel.name
        nsfw_channel_name = await get_nsfw_channel_name()

        if not title:
            title = ""
        user = await self.validate_user(context)
        if not user:
            return

        attachment_count = len(context.message.attachments)
        if attachment_count < 1:
            await self.send_reply_to_user('Cannot create post since no attachment was provided :p', context)
            return
        
        i = 0
        posts = []
        for attachment in context.message.attachments:
            is_nsfw = attachment.is_spoiler() or channel_name == nsfw_channel_name
            file_name = str(attachment.filename).lower()
            ext = ""

            for e in IMAGE_EXTENSIONS:
                if file_name.endswith(e):
                    ext = e
                    break

            for e in VIDEO_EXTENSIONS:
                if file_name.endswith(e):
                    ext = e
                    is_video = True
                    break
            
            if ext == "":
                logger.info("File \"{}\" declined due to bad extension".format(file_name)) 
                await self.send_reply_to_user('Can only accept attachments with the following extensions: {}'.format(', '.join(IMAGE_EXTENSIONS)), context)
                return
            file_name = str(attachment.id) + ext

            i = i + 1
            post_title = ""
            if attachment_count > 1:
                post_title = title + " (" + str(i) + "/" + str(attachment_count)+ ")"
            else:
                post_title = title
            
            post = await self.create_post_from_user(user, post_title, file_name, context, attachment, is_video=is_video, is_nsfw=is_nsfw)

            posts.append(post)
        
        return posts

    # Delete the users post based on the link provided to that post. Only the owner of those posts can delete them.
    # TODO: Maybe allow the admins to delete any posts also
    async def delete_post(self, context, link):
        username = str(context.message.author)
        user = await self.validate_user(context)

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
            announcements_message = await get_announcements_channel()
            await self.send_message_on_channel(announcements_message, "@everyone " + reminder.text + " (Day {})".format(await sync_to_async(getDaysFromStartDate)()))
        except Exception as e:
            logger.error("Cannot send reminder: {}".format(str(e)))

    # Send the daily message with the amount of posts received that day
    async def send_todays_post_count(self):
        try:
            post_count_message = await get_variable("PostCountMessage")
            posts, posts_size = await get_todays_posts()
            announcements_message = await get_announcements_channel()
            await self.send_message_on_channel(announcements_message, "@everyone I have received a grand total of {} {}!, and with that we conclude today's session.\nSee you tomorrow!".format(posts_size, "posts" if posts_size != 1 else "post"))
        except Exception as e:
            logger.error("Cannot send post count: {}".format(str(e)))

    async def get_username_from_id(self, id : int):
        return await self.get_user(id)
