from datetime import time
from django.conf import settings
from django.core import exceptions
from django.utils import timezone
from django.shortcuts import redirect, render
from django.http import HttpResponse, response, HttpRequest
from django.core.exceptions import *
from django.urls import resolve
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
        "sidebar_title" : str(getDaysFromStartDate()),
        "sidebar_months": MONTHS,
        "page_title" : "onesketchaday",
        "site_name" : "onesketchaday",
        "site_url" : settings.SITE_URL + "/"
    }

def renderWithContext(request : HttpRequest, template : str, context : dict):
    context.update(getGlobalContext())
    return render(request, template, context)

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
    return renderWithContext(request, "md_post.html", context)

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
    return renderWithContext(request, "md_posts.html", context)
    
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
        "title": "Participants",
        "display" : "participants"
    }
    return renderWithContext(request, "participants.html", context)

def returnError(request, code, message=""):
    context = {
        "title" : str(code),
        "message" : message
    }
    response = render(request, "error.html", context)
    response.status_code = code
    return response

def pageNotFound(request, *args, **argv):
    return returnError(request, 404, "Sorry, but I can't find what you were looking for :p")

def internalError(request, *args, **argv):
    return returnError(request, 500, "Something went wrong... I wish I knew what it was")

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
    
    context = post.getContext(show_nsfw = True, display="focused")
    return renderWithContext(request, "post.html", context)

def getFocusedPost(request, transition_url, pk, posts, nature):
    post = None

    try:
        post = Post.objects.get(id=pk)
        post.increase_click_count()
    except Exception as e:
        logger.error(str(e))
        return redirect('pageNotFound')
    
    path = resolve(request.path_info).url_name
    context = post.getFocusedContext(
        transition_url = transition_url, 
        posts = posts if not isinstance(posts, PostsGroup) else posts.posts, 
        show_nsfw = nature == "explicit", 
        focused_url = path
    )
    return renderWithContext(request, "post.html", context)

def getFocusedGalleryPost(request, pk, nature = ""):
    return getFocusedPost(request, "getFocusedGalleryPost", pk, PostsGroup(all=True), nature)

def getFocusedMonthPost(request, pk, nature = ""):
    posts = None

    try:
        posts = PostsGroup(all=True).filter(month = Post.objects.get(id = pk).get_local_time().month -1, made_after = getStartDate())
    except Exception as e:
        logger.error(str(e))
        return redirect('internalError')
    
    return getFocusedPost(request, "getFocusedMonthPost", pk, posts, nature)

def getFocusedDayPost(request, pk, nature = ""):
    timestamp = None

    try:
        timestamp = Post.objects.get(id=pk).timestamp
    except Exception as e:
        logger.error(str(e))
        return redirect('pageNotFound')
    
    return getFocusedPost(request, "getFocusedDayPost", pk, Post.objects.filter(timestamp=timestamp).order_by('date'), nature)

def getFocusedUserPost(request, pk, nature = ""):
    owner = None

    try:
        owner = Post.objects.get(id=pk).owner
    except Exception as e:
        logger.error(str(e))
        return redirect('pageNotFound')

    return getFocusedPost(request, "getFocusedUserPost", pk, Post.objects.filter(owner=owner).order_by('date'), nature)

def getPostsOfDay(request, pk):
    return getPostsOfDay(request, pk)

def getPostsOfDay(request, timestamp):
    startDateTimestamp = getTimeStampFromDate(getStartDate())
    timeStampDate = getDateFromTimestamp(timestamp)
    check_strikes = False

    if timestamp < startDateTimestamp:
        return redirect('getPostsOfDay', startDateTimestamp)
    elif timestamp > getTimeStampFromDate(timezone.localtime()):
        return redirect('getTodaysPosts')
        
    if timestamp == getTimeStampFromDate(timezone.localdate()):
        title = "Today"
        check_strikes = True
    else:
        title = timeStampDate.strftime("%B %d, %Y")
        check_strikes = False

    try:
        posts = PostsGroup(all=True).filter(timestamp = timestamp, check_strikes = check_strikes)
    except Exception as e:
        logger.error(str(e))
        return redirect('internalError')

    title = title + "\n(Day " + str(getDaysFromStartDateToTimestamp(timestamp)) + ")"

    previous, next = findPreviousAndNextTimestamps(timestamp)
    context = posts.getContext(
        title = title,
        focused_url = "getFocusedDayPost",
        display = "list",
        transition_url = "getPostsOfDay",
        previous = previous, 
        next = next
    )
    return renderWithContext(request, "posts.html", context)

def getActiveDaysOfMonth(request, index):
    month = index
    
    if month > 11 or month < 0:
        return redirect('pageNotFound')
    
    try:
        days = PostsGroup(all=True).filter(month = month, made_after = getStartDate(), first_of_day = True).posts
    except Exception as e:
            return redirect('internalError')

    title = MONTHS[month]
    context = {
        "days" : days,
        "title" : title,
        "month" : month,
        "display" : "gallery"
    }
    return renderWithContext(request, "month.html", context)

def getUserGallery(request, index, page=0):
    
    username = index
    try:
        posts = PostsGroup(all=True).filter(username = username)
    except Exception as e:
        logger.error(str(e))
        return redirect('internalError')
    
    title = username

    context = posts.getContext(
        title = title, 
        page = page, 
        transition_url= "getUserGallery", 
        transition_index = username, 
        focused_url = "getFocusedUserPost", 
        display = "gallery",
        post_per_age = getMaxPostsPerPage()
    )

    return renderWithContext(request, "posts.html", context)

def getGalleryOfMonth(request, index, page=0):

    month = index
    if month > 11 or month < 0:
        return redirect('pageNotFound')
        
    posts = PostsGroup(all=True).filter(month = month, made_after = getStartDate())

    title = MONTHS[month]
    context = posts.getContext(
        title = title, 
        page = page, 
        transition_url= "getGalleryOfMonth", 
        transition_index = month - 1 if month > 0 else 0, 
        focused_url = "getFocusedMonthPost", 
        display = "gallery",
        post_per_age = getMaxPostsPerPage()
    )
    
    return renderWithContext(request, "posts.html", context)
    
def getTodaysPosts(request):
    print(User.objects.all()[0].get_missed_days())
    return getPostsOfDay(request, getTimeStampFromDate(timezone.localdate()))

def getGallery(request, index = None, page = 0):
    search_bar_value = request.GET.get("search_bar")
    if search_bar_value:
        index = search_bar_value

    posts = PostsGroup(all=True).search(index)
    max_posts_per_page = getMaxPostsPerPage()

    if index is None and page == 0 and len(posts) > 0:
        page = int(len(posts) / max_posts_per_page)

    context = posts.getContext(
        title = "Gallery", 
        page = page, 
        transition_url= "getGallery",
        transition_index= "all" if not index else index,
        focused_url = "getFocusedGalleryPost", 
        display = "gallery",
        post_per_age = max_posts_per_page,
        has_search_bar = True,
        placeholder = index,
    )
    
    return renderWithContext(request, "posts.html", context)