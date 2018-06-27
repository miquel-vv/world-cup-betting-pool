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
        self.__get_results()
        self.__update_points()
        self.participant_points()

    def __get_results(self):

        """Updates the game scores in the DB"""

        headers = {'X-Auth-Token': '36b47a042ef748fe913405438dd5bbf4'}
        data = requests.get('http://api.football-data.org/v1/competitions/467/fixtures', headers=headers)
        data = data.json()
        fixtures = data['fixtures']

        for fixture in fixtures:
            if fixture['status'] != 'FINISHED':
                if fixture['status'] == 'IN_PLAY':
                    print('running in 1 min.')
                    raise Exception  # This causes the cron to fail and re-run every minute until game ends.
                continue

            home_team = Team.objects.filter(name=fixture['homeTeamName'])[0]
            away_team = Team.objects.filter(name=fixture['awayTeamName'])[0]

            try:
                db_fixture = Fixture.objects.filter(score_status='not counted', home_team=home_team,
                                                    away_team=away_team)[0]
            except IndexError:
                continue

            db_fixture.goals_home_team = int(fixture['result']['goalsHomeTeam'])
            db_fixture.goals_away_team = int(fixture['result']['goalsAwayTeam'])
            db_fixture.status = fixture['status']
            db_fixture.save()

    def __update_points(self):

        """updates the team points in the database"""
        fixtures = Fixture.objects.filter(score_status="not counted", status="FINISHED")

        for fixture in fixtures:
            wins = None
            draw = None

            if fixture.goals_home_team > fixture.goals_away_team:
                wins = fixture.home_team
            elif fixture.goals_home_team < fixture.goals_away_team:
                wins = fixture.away_team
            elif fixture.goals_home_team == fixture.goals_away_team:
                draw = (fixture.home_team, fixture.away_team)

            points = 0
            try:
                wins.points += 2
                points = 2
                wins.save()
                print('{} got 2 points'.format(wins.name))
            except AttributeError:
                for team in draw:
                    print('{} got one point'.format(team.name))
                    team.points += 1
                    points += 1
                    team.save()
            finally:
                if points == 2:
                    fixture.score_status = 'counted'
                    fixture.save()
                    print('Succesfully calculated points for {} - {}'.format(fixture.home_team.name,
                                                                             fixture.away_team.name))
                else:
                    raise ValueError('{points} were given in the fixture {home_team} - '
                                     '{away_team}'.format(points=points, home_team=fixture.home_team,
                                                          away_team=fixture.away_team))

    def participant_points(self):

        participants = Participant.objects.all()
        for participant in participants:
            print('updating score {}'.format(participant.name))
            sum = 0
            for team in participant.teams.all():
                sum += team.points

            print('{} got {} points'.format(participant.name, sum))
            participant.points = sum
            participant.save()