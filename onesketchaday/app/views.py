from datetime import time
from django.conf import settings
from django.core import exceptions
from django.utils import timezone
from django.shortcuts import redirect, render
from django.http import HttpResponse, response
from django.core.exceptions import *
from .models import *
import logging
import base64

logger = logging.getLogger(__name__)

MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"]

def getStartDate():
    start = Variable.objects.filter(name="StartDate").first()
    if not start:
        raise ObjectDoesNotExist("Variable \"StartDate\" was not defined")
    
    return start.date

def getDaysFromStartDate():
    return getDaysFromStartDateToTimestamp(getTimeStampFromDate(timezone.localdate()))

def getDaysFromStartDateToTimestamp(timestamp):
    start = getStartDate()
    offset = timezone.datetime(start.year, start.month, start.day)
    target = getDateFromTimestamp(timestamp)
    return (target - offset).days + 1

def getGlobalContext():
    return {
        "media_url" : settings.MEDIA_URL,
        "static_url" : settings.STATIC_URL,
        "sidebar_title" : "Day " + str(getDaysFromStartDate()),
        "sidebar_months": MONTHS,
        "page_title" : "onesketchaday",
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
    post = Post.objects.filter(id=pk).first()
    if post == None:
        return redirect('pageNotFound')
    
    context = {
        "post" : post,
        "title" : post.title
    }
    context.update(getGlobalContext())
    return render(request, "post.html", context)

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
        "title" : title
    }
    context.update(getGlobalContext())
    return render(request, "posts.html", context)

def getPostsFromUser(request, username):
    
    try:
        posts = Post.objects.filter(owner=User.objects.get(username=username)).order_by('date')
    except Exception as e:
        logger.error(str(e))
        return redirect('internalError')
    
    title = "Posts from " + username

    context = {
        "posts" : posts,
        "title" : title
    }
    context.update(getGlobalContext())
    return render(request, "posts.html", context)

def getPostsOfMonth(request, month):
    posts = []
    days = []
    lastTimestamp = 0

    startDate = getStartDate()

    if month > 11 or month < 0:
        return redirect('pageNotFound')
    month = month +1

    try:
        posts = Post.objects.all().order_by('timestamp')
    except Exception as e:
            return redirect('internalError')
    
    for post in posts:
        if post and post.date >= startDate and post.date.month == month:
            if lastTimestamp < post.timestamp:
                lastTimestamp = post.timestamp
                days.append({"timestamp" : str(lastTimestamp), "name" : timezone.localtime(post.date).strftime("%A %d, %B %Y")})

    title = MONTHS[month-1]
    context = {
        "days" : days,
        "title" : title
    }
    context.update(getGlobalContext())
    return render(request, "month.html", context)

def getTodaysPosts(request):
    return getPostsOfDay(request, getTimeStampFromDate(timezone.localdate()))