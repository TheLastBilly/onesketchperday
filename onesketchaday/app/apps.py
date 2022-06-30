from django.apps import AppConfig
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        try:
            from .models import User, Post, MarkdownPost, Variable, Tag
            posts = Post.objects.all()
            for post in posts:
                post.update_timestamp()
            
            if not MarkdownPost.objects.filter(title='About').exists():
                MarkdownPost.objects.create(title='About',contents='# About')

            if not MarkdownPost.objects.filter(title='Updates').exists():
                MarkdownPost.objects.create(title='Updates',contents='# Updates')
            
            for variable in settings.DEFAULT_VARIABLES:
                if not Variable.objects.filter(name=variable).exists():
                    Variable.objects.create(name=variable)
            
            for tag in settings.DEFAULT_TAGS:
                if not Tag.objects.filter(name=tag).exists():
                    Tag.objects.create(name=tag)

            from .utils import getStartDate
            for user in User.objects.all():
                if not user.started_on:
                    user.started_on = getStartDate()
        except Exception as e:
            logger.error("Cannot apply initial db setup: {}".format(str(e)))
