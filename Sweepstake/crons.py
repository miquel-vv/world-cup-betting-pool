from django_cron import CronJobBase, Schedule
import requests
from .models import Team, Player, Fixture, Participant
from datetime import datetime, timezone


class CalculateScores(CronJobBase):
    RUN_EVERY_MINS = 120  # every 2 hours
    RETRY_AFTER_FAILURE_MINS = 1
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS, retry_after_failure_mins=RETRY_AFTER_FAILURE_MINS)
    code = 'Sweepstake.CalculateScores'    # a unique code

    def do(self):
        #self.__get_results()
        #self.__update_points()
        self.participant_points()

