from datetime import time
from django.conf import settings
from django.core import exceptions
from django.utils import timezone
from django.shortcuts import redirect, render
from django.http import HttpResponse, response
from django.core.exceptions import *
from django.urls import reverse
from django.db.models.functions import Length

from .posts import PostsGroup
from .models import *
import logging
import base64

logger = logging.getLogger(__name__)

DEFAULT_MAX_POST_PER_PAGE = 50
DEFAULT_MAX_CHAR_PER_BIO = 300

MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"]

def getMaxPostsPerPage():
    try:
        return Variable.objects.get(name="PostsPerPage").read(int)
    except Exception as e:
        return DEFAULT_MAX_POST_PER_PAGE

def getMaxCharactersPerBiography():
    try:
        return Variable.objects.get(name="MaxBiographyCharacters").read(int)
    except Exception as e:
        return DEFAULT_MAX_CHAR_PER_BIO

def getGlobalContext():
    return {
        "media_url" : settings.MEDIA_URL,
        "static_url" : settings.STATIC_URL,
        "sidebar_title" : "Day " + str(getDaysFromStartDate()),
        "sidebar_months": MONTHS,
        "page_title" : "onesketchaday",
        "site_name" : "onesketchaday",
        "site_url" : settings.SITE_URL + "/",
    }

def renderMarkdownPost(request, title):
    try:
        post = MarkdownPost.objects.get(title=title)
        if not post:
            return redirect('pageNotFound')
    except Exception as e:
            return redirect('pageNotFound')
        
    context = {
        "html" : str(post.get_html()),
    }
    context.update(getGlobalContext())
    return render(request, "md_post.html", context)

def renderMarkdownPosts(request, label):
    try:
        objects = MarkdownPost.objects.filter(label=label).order_by('date')
        if not objects:
            return redirect('pageNotFound')
        posts = []
        for object in objects:
            posts.append({"html" : object.get_html(), "date" : object.date})
    except Exception as e:
            return redirect('internalError')
        
        
    context = {
        "posts" : posts,
    }
    context.update(getGlobalContext())
    return render(request, "md_posts.html", context)
    
def getAboutPage(request):
    return renderMarkdownPost(request, 'About')
def getUpdatesPage(request):
    return renderMarkdownPosts(request, 'update')

def getParticipantsPage(request):
    competitors = []

    try:
        users = User.objects.all().order_by(Length('biography').asc())
        max_bio_len = getMaxCharactersPerBiography()

        for user in users:
            if not user.is_a_participant:
                continue
            
            postCount = len(Post.objects.filter(owner=user))
            if not user.profile_picture.name or not user.biography:
                continue

            if len(user.biography) > max_bio_len:
                user.biography = user.biography[:max_bio_len] + "..."
            
            d = {"user":user, "posts":postCount}
            if user.is_competing:
                competitors.append(d)

    except Exception as e:
        logger.error(str(e))
        return redirect('internalError')

    context = {
        "competitors": competitors,
        "title": "Participants"
    }
    context.update(getGlobalContext())
    return render(request, "participants.html", context)

def returnError(request, code, message=""):
    context = {
        "title" : str(code),
        "message" : message
    }
    context.update(getGlobalContext())
    response = render(request, "error.html", context)
    response.status_code = code
    return response

def pageNotFound(request, *args, **argv):
    return returnError(request, 404, "Sorry, but I can't find what you were looking for :p")

def internalError(request, *args, **argv):
    return returnError(request, 500, "Something went wrong... I wish I know what it was")

def getFavicon(request):
    icon = None
    try:
        icon = Variable.objects.get(name="PageIcon")
        
        icon_file = open(icon.file.path, "rb")
        if not icon_file:
            raise IOError
        
        response = HttpResponse(content=icon_file)
        response['Content-Type'] = '/image/png'

        return response
    except Exception as e:
        return redirect('pageNotFound')

def getPost(request, pk):
    post = None

    try:
        post = Post.objects.get(id=pk)
        post.increase_click_count()
    except Exception as e:
        logger.error(str(e))
        return redirect('pageNotFound')
    
    context = post.getContext(show_nsfw = True)
    context.update(getGlobalContext())
    return render(request, "post.html", context)

def getFocusedPost(request, transition_url, pk, posts):
    post = None

    try:
        post = Post.objects.get(id=pk)
        post.increase_click_count()
    except Exception as e:
        logger.error(str(e))
        return redirect('pageNotFound')
    
    context = post.getFocusedContext(transition_url = transition_url, posts = posts)
    context.update(getGlobalContext())
    return render(request, "post.html", context)
    
def getFocusedMonthPost(request, pk):
    posts = []

    try:
        posts = PostsGroup(all=True).filter(month = Post.objects.get(id = pk).date.month, date=getStartDate())
        
    except Exception as e:
        logger.error(str(e))
        return redirect('internalError')
    
    return getFocusedPost(request, "getFocusedMonthPost", pk, posts)

def getFocusedDayPost(request, pk):
    timestamp = None

    try:
        timestamp = Post.objects.get(id=pk).timestamp
    except Exception as e:
        logger.error(str(e))
        return redirect('pageNotFound')
    
    return getFocusedPost(request, "getFocusedDayPost", pk, Post.objects.filter(timestamp=timestamp).order_by('date'))

def getFocusedUserPost(request, pk):
    owner = None

    try:
        owner = Post.objects.get(id=pk).owner
    except Exception as e:
        logger.error(str(e))
        return redirect('pageNotFound')

    return getFocusedPost(request, "getFocusedUserPost", pk, Post.objects.filter(owner=owner).order_by('date'))

def getPostsOfDay(request, timestamp):
    timeStampDate = getDateFromTimestamp(timestamp)

    try:
        posts = PostsGroup(all=True).filter(timestamp = timestamp)
    except Exception as e:
        logger.error(str(e))
        return redirect('internalError')
    
    if timestamp == getTimeStampFromDate(timezone.localdate()):
        title = "Today"
    else:
        title = timeStampDate.strftime("%B %d, %Y")

    title = title + " (Day " + str(getDaysFromStartDateToTimestamp(timestamp)) + ")"

    context = posts.getContext(title = title, focused_url = "getFocusedDayPost", gallery = False)
    context.update(getGlobalContext())
    return render(request, "posts.html", context)

def getActiveDaysOfMonth(request, index):
    month = index
    
    if month > 11 or month < 0:
        return redirect('pageNotFound')
    
    try:
        days = PostsGroup(all=True).filter(month = month, made_after = getStartDate()).posts
    except Exception as e:
            return redirect('internalError')

    title = MONTHS[month]
    context = {
        "days" : days,
        "title" : title,
        "month" : month
    }
    context.update(getGlobalContext())
    return render(request, "month.html", context)

def getGallery(request, posts : PostsGroup, page, transition_url, transition_index, extra, focused_url=None):
    pages = []

    maxPostPerPage = getMaxPostsPerPage()
    if len(posts) < page * maxPostPerPage:
        return redirect('pageNotFound')
    else:
        context = posts.getContext(title)
    context.update(getGlobalContext())
    return render(request, "posts.html", context)

def getPostsFromUser(request, index, page=0):
    
    username = index
    try:
        posts = PostsGroup(all=True).filter(username = username)
    except Exception as e:
        logger.error(str(e))
        return redirect('internalError')
    
    title = username

    context = posts.getContext(title = title, page = page, transition_index = username, focused_url = "getFocusedUserPost", gallery = True)
    context.update(getGlobalContext())

    return render(request, "posts.html", context)

def getGalleryOfMonth(request, index, page=0):
    initialPosts = []
    curatedPosts = []

    startDate = getStartDate()
    month = index
    if month > 11 or month < 0:
        return redirect('pageNotFound')
        
    posts = PostsGroup(all=True).filter(month = month, made_after = getStartDate())
    title = MONTHS[month]
    context = posts.getContext(title = title, page = page, transition_url= "getGalleryOfMonth", transition_index = month - 1, focused_url = "getFocusedMonthPost")
    context.update(getGlobalContext())
    
    return render(request, "posts.html", context)
    
def getTodaysPosts(request):
    return getPostsOfDay(request, getTimeStampFromDate(timezone.localdate()))