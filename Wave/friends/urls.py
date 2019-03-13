from django.urls import path, include

from . import views

from django.urls import path, include

from . import views

urlpatterns = [
    path('find/', views.find, name='find_friends'),
    path('following/', views.following, name='following'),
    path('followers/', views.followers, name='followers'),
    path('friends/', views.friends, name='friends'),
    path('friend_requests/', views.friend_requests, name='friend_requests'),
]