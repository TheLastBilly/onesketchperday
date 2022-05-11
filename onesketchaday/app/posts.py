from datetime import date
from pydoc import resolve
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
        if self.posts:
            return len(self.posts)
        else:
            return 0
    
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
    
    def revert(self):
        return PostsGroup(self.posts[::-1])

    def filter(self, 
            made_after      : date = None,
            date            : date = None,
            month           : int = None,
            timestamp       : str = None,
            owner           : User = None,
            username        : str = None,
            first_of_month  : boolean = None,
            first_of_day    : boolean = None,
            check_strikes   : boolean = None
        ):
        months_buffer = []
        days_buffer = []
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

                if(check_strikes and post.owner.is_striked_out()):
                    continue

                if(first_of_month and post.date.month in months_buffer):
                    continue
                else:
                    months_buffer.append(post.date.month)
                
                if(first_of_day and post.date.day in days_buffer):
                    continue
                else:
                    days_buffer.append(post.date.day)

                posts.append(post)

        return PostsGroup(posts)
    
    def search(self, search : str):
        matching_posts = []

        if search:
            search = search.lower()

        if not search or len(search) < 1 or search == "all":
            return self

        tags = search.split()
        for post in self.posts:
            if len(matching_posts) >= len(self):
                break

            if search in str(post.title).lower() and post not in matching_posts:
                matching_posts.append(post)
            
            for tag in post.tags.all():
                if str(tag.title).lower() in tags and post not in matching_posts:
                    matching_posts.append(post)
            
            username = str(post.owner.username).lower()
            for tag in tags:
                if tag in username and post not in matching_posts:
                    matching_posts.append(post)

        return PostsGroup(matching_posts)

    def getContext(self, 
            title           : str = None, 
            focused_url     : str = None, 
            display         : str = None,
            page            : int = None,
            transition_url  : str = None,
            post_per_age    : int = None,
            has_search_bar  : boolean = None,
            placeholder     : str = None,

            next            : int = None,
            previous        : int = None,

            transition_index = None
        ):

        posts = []
        for post in self.posts:
            post.date = post.get_local_time()
            posts.append(post)
        
        context = {
            "posts" : posts,
            "title" : title,
            "display" : display,
            "focused_url" : focused_url,
            "next" : next,
            "previous" : previous,
            "transition_url" : transition_url,
            "transition_index" : transition_index,
            "has_search_bar" : has_search_bar,
            "placeholder" : placeholder
        }

        if display == "gallery" and page is not None and transition_url is not None and post_per_age is not None:
            pages = range(int(len(posts)/post_per_age) + (1 if len(posts) % post_per_age > 0 else 0))
            pages_len = len(pages)
            if pages_len < 2:
                pages = []

            if page >= pages_len-1:
                page = pages_len-1
            
            if page > 0 and previous is None:
                previous = page - 1
            if pages_len > page+1 and next is None:
                next = page + 1
            
            posts = posts[page*post_per_age:]
            posts = posts[:post_per_age]
            
            context.update({
                "posts" : posts,
                "pages" : pages,
                "page" : page,
                "previous" : previous,
                "next" : next,
            })
            return context
        else:
            return context

