from asgiref.sync import sync_to_async
from django.core.exceptions import *
from bot.globals import *
from datetime import time
from app.models import *
from app.utils import *
from app.utils import *
import logging, os
import asyncio

async def get_days_from_start_date():
    return await sync_to_async(getDaysFromStartDate)()

async def get_session_time_remaining():
    return await sync_to_async(getTimeRemainingForSession)()

async def get_post_page(post : Post):
    return await sync_to_async(post.get_page)()

async def get_user_page(user : User):
    return await sync_to_async(user.get_page)()

async def save_user(user : User):
    return await sync_to_async(user.save)()

async def create_variable(**kwargs):
    return await sync_to_async(Variable.objects.create)(**kwargs)

async def get_variable(name : str):
    return await sync_to_async(Variable.objects.get)(name=name)
async def set_variable(variable : Variable):
    return await sync_to_async(variable.save)()

async def get_reminder():
    return await sync_to_async(Variable.objects.get)(name="ReminderMessage")
async def set_reminder(reminder : str):
    var = await get_reminder()
    var.text = reminder
    await sync_to_async(var.save)()

async def create_post(**kwargs):
    return await sync_to_async(Post.objects.create)(**kwargs)
async def get_post(owner : User, id : str):
    return await sync_to_async(Post.objects.get)(owner = owner, id = id)
async def delete_post(id : str):
    post = await get_post(id)
    await sync_to_async(post.delete)()
async def save_post(post : Post):
    return await sync_to_async(post.save)()

async def get_todays_posts():
    timestamp = await sync_to_async(getTodaysTimestamp)()
    posts = await sync_to_async(Post.objects.filter)(timestamp=timestamp)
    return posts, await sync_to_async(len)(posts)

async def delete_post(onwer, id):
    post = await get_post(onwer, id) 
    await sync_to_async(post.delete)()

async def get_user(discord_username : str):
    try:
        return await sync_to_async(User.objects.get)(discord_username=discord_username)
    except ObjectDoesNotExist as e:
        return None