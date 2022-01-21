from datetime import time
from django.conf import settings
from django.core import exceptions
from django.utils import timezone
from django.shortcuts import redirect, render
from django.http import HttpResponse, response
from django.core.exceptions import *
from django.urls import reverse
from .models import *
import logging
import base64

DEFAULT_MAX_POST_PER_PAGE = 50

logger = logging.getLogger(__name__)

MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"]

def getMaxPostsPerPage():
    try:
        p = Variable.objects.get(name="PostsPerPage")
        if not p or not p.integer:
            raise ValueError
        return p.integer
    except Exception as e:
        return DEFAULT_MAX_POST_PER_PAGE

def getGlobalContext():
    return {
        "media_url" : settings.MEDIA_URL,
        "static_url" : settings.STATIC_URL,
        "sidebar_title" : "Day " + str(getDaysFromStartDate()),
        "sidebar_months": MONTHS,
        "page_title" : "onesketchaday",
        "site_name" : "onesketchaday",
        "site_url" : settings.SITE_URL,
    }

def renderMarkdownPost(request, title):
    try:
        post = MarkdownPost.objects.get(title=title)
        if not post:
            return redirect('pageNotFound')
    except Exception as e:
            return redirect('pageNotFound')
        
    context = {
        "html" : str(post.html),
    }
    context.update(getGlobalContext())
    return render(request, "md.html", context)
    
def getAboutPage(request):
    return renderMarkdownPost(request, 'About')
def getUpdatesPage(request):
    return renderMarkdownPost(request, 'Updates')

def getParticipantsPage(request):
    competitors = []
    losers = []

    try:
        users = User.objects.all()

        for user in users:
            if not user.is_a_participant:
                continue
                
            postCount = len(Post.objects.filter(owner=user))

            d = {"user":user, "posts":postCount}
            if user.is_competing:
                competitors.append(d)
            else:
                losers.append(d)

    except Exception as e:
        logger.error(str(e))
        return redirect('internalError')

    context = {
        "competitors": competitors,
        "losers": losers,
        "title": "Participants"
    }
    context.update(getGlobalContext())
    return render(request, "pariticipants.html", context)

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
    except Exception as e:
        logger.error(str(e))
        return redirect('pageNotFound')
    
    context = {
        "post" : post,
        "title" : post.title,
        "show_nsfw" : True,
    }
    context.update(getGlobalContext())
    return render(request, "post.html", context)

def getFocusedPost(request, transition_url, pk, posts):
    post = None
    next_page = None
    previous_page = None

    try:
        post = Post.objects.get(id=pk)

        if post.is_nsfw:
            transition_url = "getPost"

        i = 0
        for p in posts:
            if post == p:
                break
            i += 1
        
        if i < len(posts)-1:
            next_page = posts[i+1].id
        if i > 0 and len(posts) > i:
            previous_page = posts[i-1].id
    except Exception as e:
        logger.error(str(e))
        return redirect('pageNotFound')
    
    context = {
        "post" : post,
        "title" : post.title,
        "next" : next_page,
        "previous": previous_page,
        "transition_url" : transition_url,
        "focused_url" : transition_url

    }
    context.update(getGlobalContext())
    return render(request, "post.html", context)
    

def getFocusedMonthPost(request, pk):
    posts = []

    try:
        post = Post.objects.get(id=pk)
        month = post.date.month

        startDate = getStartDate()

        try:
            initialPosts = Post.objects.all().order_by('date')
        except Exception as e:
            return redirect('pageNotFound')
        
        for post in initialPosts:
            if post and post.date >= startDate and post.date.month == month:
                post.date = post.get_local_time()
                posts.append(post)
        
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
    posts = []
    timeStampDate = getDateFromTimestamp(timestamp)

    try:
        # This is done to validate the timestamp, I'm doing it this way because I need timeStampDate
        posts = Post.objects.filter(timestamp=getTimeStampFromDate(timeStampDate)).order_by('date')
    except Exception as e:
        logger.error(str(e))
        return redirect('internalError')
    
    if timestamp == getTimeStampFromDate(timezone.localdate()):
        title = "Today"
    else:
        title = timeStampDate.strftime("%B %d, %Y")

    title = title + " (Day " + str(getDaysFromStartDateToTimestamp(timestamp)) + ")"

    context = {
        "posts" : posts,
        "title" : title,
        "non_gallery" : True,
        "focused_url" : "getFocusedDayPost"
    }
    context.update(getGlobalContext())
    return render(request, "posts.html", context)

def getActiveDaysOfMonth(request, index):
    posts = []
    days = []
    lastTimestamp = 0

    startDate = getStartDate()

    month = index
    if month > 11 or month < 0:
        return redirect('pageNotFound')
    month = month +1

    try:
        posts = Post.objects.all().order_by('date')
    except Exception as e:
            return redirect('internalError')
    
    for post in posts:
        if post and post.date >= startDate and post.date.month == month:
            if lastTimestamp < post.timestamp:
                lastTimestamp = post.timestamp
                days.append(post)

    month = month - 1
    title = MONTHS[month]
    context = {
        "days" : days,
        "title" : title,
        "month" : month
    }
    context.update(getGlobalContext())
    return render(request, "month.html", context)

def getGallery(request, posts, page, transition_url, transition_index, extra, focused_url=None):
    pages = []

    next_page = None
    previous_page = None
    maxPostPerPage = getMaxPostsPerPage()
    if len(posts) < page * maxPostPerPage:
        return redirect('pageNotFound')
    else:
        for i in range(int(len(posts)/maxPostPerPage)):
            pages.append(i)
        if len(pages) < 2:
            pages = []
        
        if page > 0:
            previous_page = page - 1
        if len(pages) > page+1:
            next_page = page + 1
        
        posts = posts[page*maxPostPerPage:]
        posts = posts[:maxPostPerPage]

    context = {
        "posts" : posts,
        "pages" : pages,
        "transition_url" : transition_url,
        "transition_index" : transition_index,
        "previous" : previous_page,
        "next" : next_page,
        "focused_url" : focused_url,
        "page": page,
    }
    context.update(getGlobalContext())
    context.update(extra)
    return render(request, "posts.html", context)

def getPostsFromUser(request, index, page=0):
    
    username = index
    try:
        posts = Post.objects.filter(owner=User.objects.get(username=username)).order_by('date')
    except Exception as e:
        logger.error(str(e))
        return redirect('internalError')
    
    title = username

    context = {
        "title" : title,
    }
    return getGallery(request, posts, page, "getPostsFromUser", username, context, focused_url="getFocusedUserPost")

def getGalleryOfMonth(request, index, page=0):
    initialPosts = []
    curatedPosts = []

    startDate = getStartDate()
    month = index
    if month > 11 or month < 0:
        return redirect('pageNotFound')
    month = month +1

    try:
        initialPosts = Post.objects.all().order_by('date')
    except Exception as e:
            return redirect('internalError')
    
    for post in initialPosts:
        if post and post.date >= startDate and post.date.month == month:
            post.date = post.get_local_time()
            curatedPosts.append(post)

    title = MONTHS[month-1]
    context = {
        "title" : title
    }
    return getGallery(request, curatedPosts, page, "getGalleryOfMonth", month-1, context, focused_url="getFocusedMonthPost")
    

def getTodaysPosts(request):
    return getPostsOfDay(request, getTimeStampFromDate(timezone.localdate()))