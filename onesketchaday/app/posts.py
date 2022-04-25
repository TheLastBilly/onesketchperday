from datetime import date
from sqlite3 import Timestamp
from xmlrpc.client import boolean
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
    
    def __len__(self):
        return len(self.posts)
    
    def __str__(self):
        return str(self.posts)
    
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
            username        : str = None,
            first_of_month  : boolean = None
        ):
        months_buffer = []
        posts = []

        if date:
            date = timezone.localtime(date)

        if month is not None:
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

                if(first_of_month and post.date.month in months_buffer):
                    continue
                else:
                    months_buffer.append(post.date.month)

                posts.append(post)

        return PostsGroup(posts)

    def getContext(self, 
            title           : str = None, 
            focused_url     : str = None, 
            display         : str = None,
            page            : int = None,
            transition_url  : str = None,
            post_per_age    : int = None,

            next            : int = None,
            previous        : int = None,

            transition_index = None
        ):

        posts = []
        for post in self.posts:
            post.date = post.get_local_time()
            posts.append(post)

        if display == "gallery" and page is not None and transition_url is not None and post_per_age is not None:
            pages = range(int(len(posts)/post_per_age) + (1 if len(posts) % post_per_age > 0 else 0))
            if len(pages) < 2:
                pages = []
            
            if page > 0 and previous is None:
                previous = page - 1
            if len(pages) > page+1 and next is None:
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
                "display" : display,
                "title" : title
            }
        else:
            return {
                "posts" : posts,
                "title" : title,
                "display" : display,
                "focused_url" : focused_url,
                "next" : next,
                "previous" : previous,
                "transition_url" : transition_url
            }

