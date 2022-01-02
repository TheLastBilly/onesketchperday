from django.apps import AppConfig

class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        from .models import Post
        posts = Post.objects.all()
        for post in posts:
            post.update_timestamp()