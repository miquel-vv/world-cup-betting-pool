from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from .models import Player, Participant, Team

import json


# Create your views here.
def index(request):
    return render(request, 'Sweepstake/index.html')


def leaderbords(request):
    return render(request, 'Sweepstake/leaderbords.html')


def teams(request):
    return render(request, 'Sweepstake/teams.html')


class Participants(View):

    item = Participant

    def get(self, request, **kwargs):

        try:
            parts = self.item.objects.filter(name=kwargs['name'])
        except KeyError:
            parts = self.item.objects.all()

        response = {self.__class__.__name__: []}
        for part in parts:
            part_dict = part.__dict__
            del part_dict['_state']
            response[self.__class__.__name__].append(part_dict)
        response = json.dumps(response)
        return HttpResponse(response, content_type='application/json')


class Teams(Participants):
    item = Team
