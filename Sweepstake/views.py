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

    def get(self, request):
        self.get_results()

        participants = Participant.objects.all()
        for participant in participants:
            participant.set_points()
            participant.save()

        return HttpResponseRedirect('leaderbords')

    def get_results(self):
        """Updates the game scores in the DB"""
        headers = {'X-Auth-Token': '36b47a042ef748fe913405438dd5bbf4'}
        data = requests.get('http://api.football-data.org/v1/competitions/467/fixtures', headers=headers)
        data = data.json()
        fixtures = data['fixtures']

        for fixture in fixtures:
            try:
                print('Getting first fixture')
                db_fixture = self.get_from_db(fixture)
            except ObjectDoesNotExist:
                continue

            try:
                if db_fixture.status == 'FINISHED':
                    if not db_fixture.counted:
                        print('giving points for the game {}'.format(db_fixture.__str__()))
                        db_fixture.set_points()
                        db_fixture.give_points()
                        db_fixture.save()
            except AttributeError:
                continue

    def get_from_db(self, fixture):
        """Tries to get from db, calls create new entry if not in db."""
        home_team = Team.objects.get(name=fixture['homeTeamName'])
        try:
            db_fixture = Fixture.objects.get(home_team=home_team, matchday=fixture['matchday'])
        except ObjectDoesNotExist:
            db_fixture = self.new_fixture(fixture)

        print('returning {}'.format(db_fixture.__str__()))
        return db_fixture

    def new_fixture(self, fixture):
        """Creates a new fixture in the database"""
        kwargs = {}

        print('creating home team: {} on matchday: {}'.format(fixture['homeTeamName'], fixture['matchday']))

        date, time = fixture['date'].split('T')  # date = yyyy-mm-dd, time = hh:mm:ssZ
        date = date.split('-')
        time = time.split(':')

        kwargs['home_team'] = Team.objects.get(name=fixture['homeTeamName'])
        kwargs['away_team'] = Team.objects.get(name=fixture['awayTeamName'])
        kwargs['status'] = fixture['status']
        kwargs['time'] = datetime(int(date[0]), int(date[1]), int(date[2]), int(time[0]), int(time[1]),
                                  tzinfo=timezone.utc)
        kwargs['matchday'] = fixture['matchday']

        not_saved = ('SCHEDULED', 'TIMED', 'IN PLAY')
        if fixture['status'] in not_saved:
            return

        try:
            kwargs['penalty_home_team'] = fixture['result']['penaltyShootout']['goalsHomeTeam']
            kwargs['penalty_away_team'] = fixture['result']['penaltyShootout']['goalsAwayTeam']
            kwargs['penalties'] = True
        except KeyError:
            try:
                kwargs['goals_home_team'] = fixture['result']['extraTime']['goalsHomeTeam']
                kwargs['goals_away_team'] = fixture['result']['extraTime']['goalsHomeTeam']
            except KeyError:
                kwargs['goals_home_team'] = fixture['result']['goalsHomeTeam']
                kwargs['goals_away_team'] = fixture['result']['goalsAwayTeam']

        new_fixture = Fixture(**kwargs)
        new_fixture.save()

        print('successfully created {}'.format(new_fixture.__str__()))

        return new_fixture
