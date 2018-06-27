from django.contrib import admin
from django.urls import re_path, path, include
from .views import Participants, index, Teams, leaderbords, teams

urlpatterns = [
    path('', index),
    path('leaderbords', leaderbords),
    path('teams', teams),
    path('api/participants', Participants.as_view()),
    path('api/participants/<str:name>', Participants.as_view()),
    path('api/teams', Teams.as_view()),
    path('api/teams/<str:name>', Teams.as_view())
]