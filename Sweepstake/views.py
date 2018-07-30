from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
from django.views import View
from .models import Player, Participant, Team, Fixture
from datetime import datetime, timezone
import json
import requests


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


class Update(View):

    def get(self, request, **kwargs):
        self.get_results(**kwargs)

        participants = Participant.objects.all()
        for participant in participants:
            with participant:
                participant.set_points()

        return HttpResponseRedirect('leaderbords')

    def set_filters(self, **kwargs):
        kwargs['dateFrom'] = Fixture.objects.last_counted()
        kwargs['dateTo'] = '2018-07-16'

        template = '&{filter}={value}'
        filters = ''
        for filter, value in kwargs.items():
            filters += template.format(filter=filter, value=value)
        return filters

    def get_results(self):
        """Updates the game scores in the DB"""
        headers = {'X-Auth-Token': '36b47a042ef748fe913405438dd5bbf4'}
        data = requests.get('http://api.football-data.org/v2/competitions/{competition}/matches?'
                            '{filter}'.format(competition=Fixture.objects.competition, filter=self.set_filters()),
                            headers=headers)
        data = data.json()
        print(data)
        fixtures = data['matches']

        for fixture in fixtures:
            not_saved = ('TIMED', 'IN_PLAY')
            if fixture['status'] in not_saved:
                continue

            try:
                db_fixture = Fixture.objects.get(fd_id=fixture['id'])
            except ObjectDoesNotExist:
                db_fixture = self.new_fixture(fixture)

            if db_fixture.status == 'FINISHED':
                with db_fixture as db:
                    db.score = fixture['score']
                    db.give_points()

    def new_fixture(self, fixture):
        """Creates a new fixture in the database only when the status returns finished"""

        kwargs = {
            'fd_id': fixture['id'],
            'home_team': Team.objects.get(name=fixture['homeTeam']['name']),
            'away_team': Team.objects.get(name=fixture['awayTeam']['name']),
            'status': fixture['status'],
            'stage': fixture['stage'],
            'matchday': fixture['matchday']
        }

        date, time = fixture['utcDate'].split('T')  # date = yyyy-mm-dd, time = hh:mm:ssZ
        date = date.split('-')
        time = time.split(':')

        kwargs['time'] = datetime(int(date[0]), int(date[1]), int(date[2]), int(time[0]), int(time[1]),
                                  tzinfo=timezone.utc)

        new_fixture = Fixture(**kwargs)
        print('points are {}'.format(new_fixture.points))
        with new_fixture:
            new_fixture.set_points()

        print('successfully created {}'.format(new_fixture.__str__()))
        print('points are {}'.format(new_fixture.points))
        return new_fixture
