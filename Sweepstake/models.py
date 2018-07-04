from django.db import models
from .errors import StatusError
from django.contrib.postgres.fields import JSONField


# Create your models here.
class Team(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=3)
    pot = models.IntegerField()
    points = models.IntegerField(default=0)
    previous_points = JSONField(default={})

    class Meta:
        ordering = ['-points']

    def __str__(self):
        return self.name


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
    previous_points = JSONField(default={1: 0,
                                         2: 0,
                                         3: 0,
                                         4: 0,
                                         5: 0,
                                         6: 0,
                                         7: 0,
                                         8: 0})
    location = models.CharField(max_length=50)
    pot = models.CharField(max_length=50)

    class Meta:
        ordering = ['-points']

    def __str__(self):
        return self.name

    def set_points(self):
        for team in self.teams.all():
            for matchdays, pts in team.previous_points.items():
                self.previous_points[matchdays] += pts
            self.points += team.points


class Fixture(models.Model):
    home_team = models.ForeignKey(Team, related_name='home_team', on_delete=models.CASCADE)
    away_team = models.ForeignKey(Team, related_name='away_team', on_delete=models.CASCADE)
    status = models.CharField(max_length=50)
    time = models.DateTimeField()
    goals_home_team = models.IntegerField(default=0)
    goals_away_team = models.IntegerField(default=0)
    counted = models.BooleanField(default=False)
    matchday = models.IntegerField(default=0)
    penalties = models.BooleanField(default=False)
    penalty_home_team = models.IntegerField(default=0)
    penalty_away_team = models.IntegerField(default=0)
    points_winner = models.IntegerField(default=2)
    points_loser = models.IntegerField(default=0)

    def __str__(self):
        name = '{} - {}, {}'.format(self.home_team.code, self.away_team.code, self.time.strftime('%d - %m'))
        return name

    def set_points(self):
        """Set the points to be won with this game."""

        if self.matchday < 4:
            return
        elif self.matchday == 4:
            self.points_loser = 1  # Because loser survived the group stage
            self.points_winner = 6
        elif self.matchday == 5:
            self.points_winner = 7
        elif self.matchday == 6:
            self.points_winner = 9
        elif self.matchday == 7:
            self.points_winner = 2
        elif self.matchday == 8:
            self.points_winner = 9

    def give_points(self):
        """Gives the points to the appropriate team"""

        if self.status != 'FINISHED' or self.counted:
            raise StatusError

        def decide_winner(self):
            if self.penalties:
                goals = 'penalty_'
            else:
                goals = 'goals_'

            if self.__getattribute__(goals + 'home_team') > self.__getattribute__(goals + 'away_team'):
                self.home_team.points += self.points_winner
                self.home_team.previous_points[self.matchday] = self.points_winner
                self.away_team.points += self.points_loser
                self.away_team.previous_points[self.matchday] = self.points_loser
                return True
            elif self.__getattribute__(goals + 'home_team') < self.__getattribute__(goals + 'away_team'):
                self.away_team.points += self.points_winner
                self.away_team.previous_points[self.matchday] = self.points_winner
                self.home_team.points += self.points_loser
                self.home_team.previous_points[self.matchday] = self.points_loser
                return True
            else:
                return False

        self.counted = decide_winner(self)

        if not self.counted:
            self.home_team.points += 1
            self.home_team.previous_points[self.matchday] = 1
            self.away_team.points += 1
            self.away_team.previous_points[self.matchday] = 1
            self.counted = True

        if not self.counted:
            raise ValueError

        self.home_team.save()
        self.away_team.save()
