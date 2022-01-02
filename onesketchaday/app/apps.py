from django.apps import AppConfig
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        try:
            from .models import Post, MarkdownPost, Variable
            posts = Post.objects.all()
            for post in posts:
                post.update_timestamp()
            
            if not MarkdownPost.objects.filter(title='About').exists():
                MarkdownPost.objects.create(title='About',contents='# About')

            if not MarkdownPost.objects.filter(title='Updates').exists():
                MarkdownPost.objects.create(title='Updates',contents='# Updates')
            
            if not Variable.objects.filter(name='StartDate').exists():
                Variable.objects.create(name='StartDate', date=timezone.now())
        except Exception as e:
            logger.error("Cannot apply initial db setup: {}".format(str(e)))
