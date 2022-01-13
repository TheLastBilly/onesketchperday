from . import views
from django.urls import path

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path('post/<str:pk>', views.getPost, name='getPost'),
    
    path('focused/month/<str:index>/<str:page>', views.getFocusedMonthPost, name='getFocusedMonthPost'),
    path('focused/user/<str:index>/<str:page>', views.getFocusedUserPost, name='getFocusedUserPost'),
    path('focused/day/<str:index>/<str:page>', views.getFocusedDayPost, name='getFocusedDayPost'),

    path('', views.getTodaysPosts, name='getTodaysPosts'),
    path('404/', views.pageNotFound, name='pageNotFound'),
    path('500/', views.internalError, name='internalError'),
    path('day/<int:timestamp>', views.getPostsOfDay, name='getPostsOfDay'),
    
    path('month/active/<int:index>', views.getActiveDaysOfMonth, name='getActiveDaysOfMonth'),
    path('month/active/<int:index>/<int:page>', views.getActiveDaysOfMonth, name='getActiveDaysOfMonth'),

    path('month/gallery/<int:index>', views.getGalleryOfMonth, name='getGalleryOfMonth'),
    path('month/gallery/<int:index>/<int:page>', views.getGalleryOfMonth, name='getGalleryOfMonth'),

    path('user/<str:index>', views.getPostsFromUser, name='getPostsFromUser'),
    path('user/<str:index>/<int:page>', views.getPostsFromUser, name='getPostsFromUser'),

    path('favicon', views.getFavicon, name='favicon'),
    
    path('updates', views.getUpdatesPage, name='updates'),
    path('about', views.getAboutPage, name='about'),
    path('participants', views.getParticipantsPage, name='participants'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)