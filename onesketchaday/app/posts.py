from datetime import date
from .models import Post
from .models import User

from django.utils import timezone

from . import utils

class PostsGroup:
    posts = None

    def __init__(self, posts = None, all : bool = False):
        if all:
            self.posts = Post.objects.all().order_by('date')
        else:
            self.posts = posts
    
    def made_after_start_date(self):
        return self.filter(made_after = utils.getStartDate())

    def made_in_month(self, month : int):
        return self.filter(month = month)

    def was_made_on_date(self, date : date):
        return self.filter(date = date)

    def has_timestamp(self, timestamp : int):
        return self.filter(timestamp = timestamp)

    def made_by_user(self, user : User):
        return self.filter(owner = user)

    def filter(self, 
            made_after      : date = None,
            date            : date = None,
            month           : int = None,
            timestamp       : str = None,
            owner           : User = None,
            username        : str = None
        ):
        posts = []

        if date:
            date = timezone.localtime(date)
        if month:
            month = month +1

        for post in self.posts:
            post.date = timezone.localtime(post.date)
            if                                                                  \
                (True if not made_after else post.date >= made_after)       and \
                (True if not date else post.date == date)                   and \
                (True if not month else post.date.month == month)           and \
                (True if not timestamp else post.timestamp == timestamp)    and \
                (True if not username else post.owner.username == username) and \
                (True if not owner else post.owner == owner):
                posts.append(post)

        return PostsGroup(posts)

    def getContext(self, 
            title           : str = None, 
            focused_url     : str = None, 
            gallery         : bool = None,
            page            : int = None,
            transition_url  : str = None,
            post_per_age    : int = None,

            transition_index = None
        ):
        if not self.posts:
            return {
                "title" : title
            }

        posts = []
        for post in self.posts:
            post.date = post.get_local_time()
            posts.append(post)

        if gallery and page and transition_url:
            pages = range(int(len(posts)/post_per_age) + (1 if len(posts) % post_per_age > 0 else 0))
            if len(pages) < 2:
                pages = []
            
            if page > 0:
                previous = page - 1
            if len(pages) > page+1:
                next = page + 1
            
            posts = posts[page*post_per_age:]
            posts = posts[:post_per_age]
            
            return {
                "posts" : posts,
                "pages" : pages,
                "page" : page,
                "transition_url" : transition_url,
                "transition_index" : transition_index,
                "previous" : previous,
                "next" : next,
                "focused_url" : focused_url,
                "display_type" : "gallery" if gallery else "list"
            }

        else:
            return {
                "posts" : posts,
                "title" : title,
                "display_type" : "gallery" if gallery else "list",
                "focused_url" : focused_url
            }

