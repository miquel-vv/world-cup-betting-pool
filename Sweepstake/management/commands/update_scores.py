from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from Sweepstake.models import Participant, Fixture, Team
from football_data import CompetitionInterface

import logging

from datetime import datetime, timezone


logging.basicConfig(filename='../../log/log.txt',
                    format='%(asctime)s:%(name)s:%(levelname)s:%(message)s',
                    level=logging.DEBUG)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Updates the scores of the fixtures and gives points to the teams and participants.'

    def handle(self, *args, **options):
        competition = CompetitionInterface(competition_name=Fixture.objects.competition_name)
        fixtures = competition.get_matches(dateFrom=Fixture.objects.last_counted(), dateTo=datetime.now())

        logger.info('Got fixtures')

        finished_fixtures = [fixture for fixture in fixtures if fixture['status'] == 'FINISHED']
        logger.debug('{} finished fixtures'.format(len(finished_fixtures)))

        logger.info('Start looping over fixtures')
        for fixture in finished_fixtures:
            kwargs = self.set_kwargs(fixture)
            try:
                self.new_fixture(kwargs)
            except IntegrityError:
                self.old_fixture(kwargs)

        logger.info('Ended looping over fixtures')

        participants = Participant.objects.all()
        logger.info('Start looping over participants')
        for participant in participants:
            with participant:
                participant.set_points()
        logger.info('Ended looping over participants.')

        self.stdout.write('Succesfully updated fixtures.')

    @staticmethod
    def set_kwargs(fixture):
        try:
            fixture['home_team'] = Team.objects.get(name=fixture['home_team'])
            fixture['away_team'] = Team.objects.get(name=fixture['away_team'])
        except ObjectDoesNotExist:
            raise ObjectDoesNotExist("One of the teams {} or {} does not exist in the database. Please create teams"
                                     "first before updating points.".format(fixture['home_team'], fixture['away_team']))

        fixture['time'] = (datetime
                           .strptime(fixture['time'], "%Y-%m-%dT%H:%M:%SZ")
                           .replace(tzinfo=timezone.utc))
        return fixture

    @staticmethod
    def new_fixture(fixture):
        new_fixture = Fixture(**fixture)
        with new_fixture:
            new_fixture.set_points()
            new_fixture.give_points()

    @staticmethod
    def old_fixture(fixture):
        """Gets called when the new_fixture method errors because an existing fixture already existed.
        If that fixture is already counted and the score is different than what is in the db, an error should be raised.
        At the moment all scores should be recounted. Will have to create a roll_back method on the model to backtrack
        the points given and recalculate the scores."""

        existing_fixture = Fixture.objects.get(fd_id=fixture['fd_id'])
        with existing_fixture as ef:
            if not ef.counted:
                ef.score = fixture['score']
                ef.give_points()
            elif ef.counted and not ef.score:
                raise IntegrityError("points were given incorrectly, in order to assure accuracy points need to be"
                                     "reset.")
