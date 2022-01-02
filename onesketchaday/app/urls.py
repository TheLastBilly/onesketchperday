from . import views
from django.urls import path

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.getTodaysPosts, name='getTodaysPosts'),
    path('day/<int:timestamp>', views.getPostsOfDay, name='getPostsOfDay'),
    path('month/<int:month>', views.getPostsOfMonth, name='getPostsOfMonth'),
    path('post/<str:pk>', views.getPost, name='getPost'),
    path('user/<str:username>', views.getPostsFromUser, name='getPostsFromUser'),
    path('404/', views.pageNotFound, name='pageNotFound'),
    path('500/', views.internalError, name='internalError'),
    
    path('updates', views.getUpdatesPage, name='updates'),
    path('about', views.getAboutPage, name='about'),
    path('participants', views.getParticipantsPage, name='participants'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)