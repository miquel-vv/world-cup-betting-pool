from django.shortcuts import render
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

    def get(self, request):
        self.__get_results()
        return HttpResponseRedirect('leaderbords')

    def __get_results(self):
        """Updates the game scores in the DB"""
        headers = {'X-Auth-Token': '36b47a042ef748fe913405438dd5bbf4'}
        data = requests.get('http://api.football-data.org/v1/competitions/467/fixtures', headers=headers)
        data = data.json()
        fixtures = data['fixtures']

        for fixture in fixtures:
            try:
                db_fixture = self.get_from_db(fixture)
            except Team.DoesNotExist:
                continue

            if db_fixture.status == 'FINISHED':
                if not db_fixture.counted:
                    db_fixture.set_points()
                    db_fixture.give_points()

    def get_from_db(self, fixture):
        """Tries to get from db, calls create new entry if not in db."""
        home_team = Team.objects.get(name=fixture['homeTeamName'])
        try:
            db_fixture = Fixture.objects.get(home_team=home_team, matchday=fixture['matchday'])
        except Team.DoesNotExist:
            db_fixture = self.new_fixture(fixture)

        return db_fixture

    def new_fixture(self, fixture):
        """Creates a new fixture in the database"""
        kwargs = {}

        date, time = fixture['date'].split('T')  # date = yyyy-mm-dd, time = hh:mm:ssZ
        date = date.split('-')
        time = time.split(':')

        kwargs['home_team'] = Team.objects.get(name=fixture['homeTeamName'])
        kwargs['away_team'] = Team.objects.get(name=fixture['awayTeamName'])
        kwargs['status'] = fixture['status']
        kwargs['time'] = datetime(date[0], date[1], date[2], time[0], time[1], tzinfo=timezone.utc)
        kwargs['matchday'] = fixture['matchday']

        result_lentgh = len(fixture['result'])
        if result_lentgh == 2:
            return
        elif result_lentgh == 3:
            kwargs['goals_home_team'] = fixture['result']['goalsHomeTeam']
            kwargs['goals_away_team'] = fixture['result']['goalsAwayTeam']
        elif result_lentgh > 3:
            kwargs['goals_home_team'] = fixture['result']['extraTime']['goalsHomeTeam']
            kwargs['goals_away_team'] = fixture['result']['extraTime']['goalsHomeTeam']
            if result_lentgh == 5:
                kwargs['penalties'] = True
                kwargs['penalty_home_team'] = fixture['result']['penaltyShootout']['goalsHomeTeam']
                kwargs['penalty_away_team'] = fixture['result']['penaltyShootout']['goalsAwayTeam']

        new_fixture = Fixture(**kwargs)
        new_fixture.save()

        return new_fixture