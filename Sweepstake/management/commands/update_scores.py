from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from Sweepstake.models import Participant, Fixture, Team

import os
import requests
from datetime import datetime, timezone


class Command(BaseCommand):
    help = 'Updates the scores of the fictures and gives points to the teams and participants.'

    def handle(self, *args, **options):
        competition = Fixture.objects.competition
        filters = self.set_filters()
        fixtures = self.get_results(competition, filters)

        self.update_fixtures(fixtures)

        participants = Participant.objects.all()
        for participant in participants:
            with participant:
                participant.set_points()

        self.stdout.write('Succesfully updated fixtures.')

    def set_filters(self, **kwargs):
        """Create the timeframe with only games that need updating."""

        kwargs['dateFrom'] = Fixture.objects.last_counted()
        kwargs['dateTo'] = '2018-07-16'

        template = '&{filter}={value}'
        filters = ''
        for filter, value in kwargs.items():
            filters += template.format(filter=filter, value=value)
        return filters

    def get_results(self, competition, filters):
        """fetches the results from Football-Data"""

        headers = {'X-Auth-Token': os.environ['FOOTBALL_DATA_API']}
        data = requests.get('http://api.football-data.org/v2/competitions/{competition}/matches?{filter}'
                            .format(competition=competition,
                                    filter=filters),
                            headers=headers)
        data = data.json()
        return data['matches']

    def update_fixtures(self, fixtures):
        for fixture in fixtures:
            if fixture['status'] in ('TIMED', 'IN_PLAY'):
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

        kwargs['time'] = datetime(int(date[0]),
                                  int(date[1]),
                                  int(date[2]),
                                  int(time[0]),
                                  int(time[1]),
                                  tzinfo=timezone.utc)

        new_fixture = Fixture(**kwargs)
        print('points are {}'.format(new_fixture.points))
        with new_fixture:
            new_fixture.set_points()

        print('successfully created {}'.format(new_fixture.__str__()))
        print('points are {}'.format(new_fixture.points))
        return new_fixture
