from . import views
from django.urls import path

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path('post/<str:pk>', views.getPost, name='getPost'),
    path('', views.getTodaysPosts, name='getTodaysPosts'),
    path('404/', views.pageNotFound, name='pageNotFound'),
    path('500/', views.internalError, name='internalError'),
    path('day/<int:timestamp>', views.getPostsOfDay, name='getPostsOfDay'),
    path('month/active/<int:month>', views.getActiveDaysOfMonth, name='getActiveDaysOfMonth'),
    path('month/gallery/<int:month>', views.getGalleryOfMonth, name='getGalleryOfMonth'),
    path('user/<str:username>', views.getPostsFromUser, name='getPostsFromUser'),

    path('favicon', views.getFavicon, name='favicon'),
    
    path('updates', views.getUpdatesPage, name='updates'),
    path('about', views.getAboutPage, name='about'),
    path('participants', views.getParticipantsPage, name='participants'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)