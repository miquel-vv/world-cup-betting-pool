from django.db import models
from .errors import StatusError
from django.contrib.postgres.fields import JSONField
from collections import defaultdict


class Team(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=3)
    pot = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    previous_points = JSONField(default={})

    class Meta:
        ordering = ['-points']

    def __str__(self):
        return self.name

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.points = 0
        for previous in self.previous_points.values():
            self.points += previous
        self.save()


class Player(models.Model):
    name = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    goals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Participant(models.Model):
    name = models.CharField(max_length=200)
    teams = models.ManyToManyField(Team)
    topscorer = models.ForeignKey(Player, related_name='topscorer', on_delete=models.CASCADE)
    assist_king = models.ForeignKey(Player, related_name='assist_king', on_delete=models.CASCADE)
    points = models.IntegerField(default=0)
    previous_points = JSONField(default={})
    location = models.CharField(max_length=50)
    pot = models.CharField(max_length=50)

    class Meta:
        ordering = ['-points']

    def __str__(self):
        return self.name

    def set_points(self):
        self.previous_points = defaultdict(int)
        for team in self.teams.all():
            for matchday, pts in team.previous_points.items():
                self.previous_points[matchday] += pts

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.points = 0
        for previous in self.previous_points.values():
            self.points += previous
        self.save()


class FixtureManager(models.Manager):
    """Manager object to check when the last fixture was counted."""

    competition = 2000 # The competion id in Football-data.org for the World Cup
    competition_name = 'fifa world cup'

    def last_counted(self, string=True):

        last_counted = super().get_queryset().filter(counted=True).last()

        if not last_counted:
            return '2018-06-13'  # This means that no fixture was found and therefor first date of the comp is returned.

        if string:
            return last_counted.time.strftime('%Y-%m-%d')
        else:
            return last_counted


class Fixture(models.Model):
    fd_id = models.IntegerField(verbose_name='Football-data id', unique=True)
    home_team = models.ForeignKey(Team, related_name='home_team', on_delete=models.CASCADE)
    away_team = models.ForeignKey(Team, related_name='away_team', on_delete=models.CASCADE)
    stage = models.CharField(max_length=50)
    matchday = models.IntegerField(null=True)
    status = models.CharField(max_length=50)
    time = models.DateTimeField()
    score = JSONField(default={})   # Replicates the score dict from football-data.org. Makes updating easier.
    points = JSONField(default={'winner': 2,
                                'loser': 0})
    counted = models.BooleanField(default=False)

    objects = FixtureManager()

    class Meta:
        ordering = ['time']

    def __str__(self):
        name = '{} - {}, {}'.format(self.home_team.code, self.away_team.code, self.time.strftime('%d - %m'))
        return name

    def set_points(self):
        """Set the points to be won with this game."""

        points = {
            'GROUP_STAGE': (2, 0),
            'ROUND_OF_16': (7, 1),  # 2 for winning, 1 for passing group stage (for loser too), 4 for surviving last 16
            'QUARTER_FINALS': (7, 0),  # 2 for winning, 5 for passing Round of 16
            'SEMI_FINALS': (9, 0),  # 2 for winning, 7 for being at least second
            'FINAL': (9, 0)     # 2 for winning 7 for being WC
        }
        try:
            self.points['winner'], self.points['loser'] = points[self.stage]
        except KeyError:
            print('{} was groupstage'.format(self.matchday))
            return

    def give_points(self):
        """Gives the points to the appropriate team"""
        print('{} - {} won by {}'.format(self.home_team, self.away_team, self.score['winner']))

        if self.score['winner'] == 'DRAW':
            print('{} - {} taken as draw'.format(self.home_team, self.away_team))
            self.points['winner'] = 1
            self.points['loser'] = 1
            winner = self.home_team    # Named winner just for ease
        else:
            winner = self.__getattribute__(self.score['winner'].lower())

        if winner == self.home_team:
            loser = self.away_team
        else:
            loser = self.home_team

        with winner as win:
            win.previous_points[self.get_previous_name()] = self.points['winner']

        with loser as lost:
            lost.previous_points[self.get_previous_name()] = self.points['loser']

        self.counted = True

    def get_previous_name(self):
        if self.matchday:                   # To identify in the previous_points dicts of both Team and Participant
            previous_name = self.matchday
        else:
            previous_name = self.stage
        return previous_name

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save()
