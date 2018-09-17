from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from Sweepstake.models import Participant, Fixture, Team
from wc2018.football_data import CompetitionData

import os
import requests
from datetime import datetime, timezone
from wc2018.football_data import CompetitionInterface


class Command(BaseCommand):
    help = 'Updates the scores of the fictures and gives points to the teams and participants.'

    def handle(self, *args, **options):
        competition = CompetitionInterface(competition_name=Fixture.objects.competition_name)
        fixtures = competition.get_matches(dateFrom=Fixture.objects.last_counted())

        self.update_fixtures(fixtures)

        participants = Participant.objects.all()
        for participant in participants:
            with participant:
                participant.set_points()

        self.stdout.write('Succesfully updated fixtures.')

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
