from re import T
from asgiref.sync import SyncToAsync
from django.core.exceptions import *
from bot.globals import *
from datetime import time
from app.models import *
from app.utils import *
from app.utils import *
import logging, os
import asyncio

from django.db import close_old_connections

DATETIME_STRING_FORMAT      = "%H:%M:%S,%d/%m/%Y"
DATE_STRING_FORMAT          = "%d/%m/%Y"

# Taken from https://github.com/django/channels/blob/main/channels/db.py
class DatabaseSyncToAsync(SyncToAsync):
    """
    SyncToAsync version that cleans up old database connections when it exits.
    """

    def thread_handler(self, loop, *args, **kwargs):
        close_old_connections()
        try:
            return super().thread_handler(loop, *args, **kwargs)
        finally:
            close_old_connections()

database_sync_to_async = DatabaseSyncToAsync

async def get_new_member_role():
    return (await get_variable("NewMemberDefaultRole")).text

async def get_new_member_message():
    return (await get_variable("NewMembersWelcomeMessage")).text
    
async def get_new_member_announcement_message():
    return (await get_variable("NewMembersAnnouncementMessage")).text

async def get_announcements_channel():
    return (await get_variable("AnnouncementsChannel")).text

async def get_models(model):
    def get_all():
        programmed_events = []
        for p in model.objects.all():
            programmed_events.append(p)
        return programmed_events
    
    return await database_sync_to_async(get_all)()

async def get_challenge_submissions(challenge: Challenge):
    def get():
        submissions = []
        for p in challenge.submissions.all():
            submissions.append(p)
        return submissions

    return await database_sync_to_async(get)()

async def get_challenge(id : str):
    challenge = await database_sync_to_async(Challenge.objects.filter)(id=id)
    challenge = await database_sync_to_async(challenge.first)()
    
    return challenge

async def get_challenges():
    return await get_models(Challenge)

async def get_programmed_events():
    return await get_models(ProgrammedEvent)

async def parse_time_string(fmt : str, time_str : str):
    t = await database_sync_to_async(timezone.datetime.strptime)(time_str, fmt) 
    t = await database_sync_to_async(timezone.make_aware)(t)

    return t

async def get_datetime_from_string(datetime_str : str):
    return await parse_time_string(DATETIME_STRING_FORMAT, datetime_str)
    
async def get_date_from_string(date_str : str):
    return await parse_time_string(DATE_STRING_FORMAT, date_str)

async def get_nsfw_channel_name():
    return (await get_variable("NSFWChannel")).label

async def get_day_suffix(day):
    return await database_sync_to_async(getDaySuffix)(day)

async def get_start_date():
    return await database_sync_to_async(getStartDate)()

async def get_max_strikes():
    return await database_sync_to_async(getMaxStrikes)()

async def get_days_from_start_date():
    return await database_sync_to_async(getDaysFromStartDate)()

async def get_session_time_remaining():
    return await database_sync_to_async(getTimeRemainingForSession)()

async def get_post_page(post : Post):
    return await database_sync_to_async(post.get_page)()

async def get_user_page(user : User):
    return await database_sync_to_async(user.get_page)()

async def save_user(user : User):
    return await database_sync_to_async(user.save)()

async def create_variable(**kwargs):
    return await database_sync_to_async(Variable.objects.create)(**kwargs)

async def get_variable(name : str) -> Variable:
    return await database_sync_to_async(Variable.objects.get)(name=name)
async def set_variable(variable : Variable):
    return await database_sync_to_async(variable.save)()

async def get_date_from_timestamp(timestamp : int):
    return await database_sync_to_async(getDateFromTimestamp)(timestamp)

async def make_datetime_aware(datetime : timezone.datetime):
    return await database_sync_to_async(makeDatetimeAware)(datetime)

async def get_date():
    return await database_sync_to_async(timezone.localdate)()

async def get_reminder():
    return await database_sync_to_async(Variable.objects.get)(name="ReminderMessage")
async def set_reminder(reminder : str):
    var = await get_reminder()
    var.text = reminder
    await database_sync_to_async(var.save)()

async def create_post(**kwargs):
    return await database_sync_to_async(Post.objects.create)(**kwargs)
async def get_post(owner : User, id : str):
    return await database_sync_to_async(Post.objects.get)(owner = owner, id = id)
async def delete_post(id : str):
    post = await get_post(id)
    await database_sync_to_async(post.delete)()
async def save_post(post : Post):
    return await database_sync_to_async(post.save)()

async def get_todays_posts():
    timestamp = await database_sync_to_async(getTodaysTimestamp)()
    posts = await database_sync_to_async(Post.objects.filter)(timestamp=timestamp)
    return posts, await database_sync_to_async(len)(posts)

async def delete_post(onwer, id):
    post = await get_post(onwer, id) 
    await database_sync_to_async(post.delete)()

async def get_user_from_id(discord_id : int):
    try:
        return await database_sync_to_async(User.objects.get)(discord_id=discord_id)
    except ObjectDoesNotExist as e:
        return None

async def get_user_from_name(username : str):
    try:
        return await database_sync_to_async(User.objects.get)(username=username)
    except ObjectDoesNotExist as e:
        return None

async def get_user(id : int = None, username : str = None):
    if id:
        return await get_user_from_id(id)
    if username:
        return await get_user_from_name(username)
    return None
