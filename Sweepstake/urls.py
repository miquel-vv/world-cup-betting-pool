from django.urls import re_path, path, include
from django.contrib.auth import views as auth_views
from .views import *

urlpatterns = [
    path('', index),
    re_path('^login/$', auth_views.login, {'template_name': 'Sweepstake/login.html'}),
    re_path('^logout/$', auth_views.logout, {'next_page': '/'}),
    re_path('create_user', create_user),
    re_path('^teams/(?P<name>\w+)$', TeamDashboard.as_view()),
    re_path('^participants/(?P<name>[a-zA-Z0-9_&é]+)$', ParticipantDashboard.as_view()),
    re_path('^teams', TeamLeaderbord.as_view()),
    re_path('^participants', ParticipantLeaderbord.as_view()),
    re_path('^teams$', teams),
    re_path('^api/participants$', Participants.as_view()),
    re_path('^api/participants/<str:name>', Participants.as_view()),
    re_path('^api/teams$', Teams.as_view()),
    re_path('^api/teams/(?P<name>[a-zA-Z]+)$', Teams.as_view()),
    re_path('^api/v2/teams/(?P<name>\w+)$', TeamPosition.as_view()),
    re_path('^api/v2/participants/(?P<name>[a-zA-Z0-9_&é]+)$', ParticipantPosition.as_view()),
    re_path('update_scores', update),
]