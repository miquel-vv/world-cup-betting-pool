from django.urls import re_path, path, include
from .views import Participants, index, Teams, leaderbords, teams, update

urlpatterns = [
    path('', index),
    re_path('^leaderbords$', leaderbords),
    re_path('^teams$', teams),
    re_path('^api/participants$', Participants.as_view()),
    re_path('^api/participants/<str:name>', Participants.as_view()),
    re_path('^api/teams$', Teams.as_view()),
    re_path('^api/teams/(?P<name>[a-zA-Z]+)$', Teams.as_view()),
    re_path('update_scores', update),
]