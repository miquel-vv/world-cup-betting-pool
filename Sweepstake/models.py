from django.db import models


# Create your models here.
class Team(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=3)
    pot = models.IntegerField()
    points = models.IntegerField(default=0)
    previous_position = models.IntegerField(default=0)

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
    previous_position = models.IntegerField()
    points = models.IntegerField(default=0)
    location = models.CharField(max_length=50)
    pot = models.CharField(max_length=50)

    class Meta:
        ordering = ['-points']

    def __str__(self):
        return self.name


class Fixture(models.Model):
    home_team = models.ForeignKey(Team, related_name='home_team', on_delete=models.CASCADE)
    away_team = models.ForeignKey(Team, related_name='away_team', on_delete=models.CASCADE)
    status = models.CharField(max_length=50)
    time = models.DateTimeField()
    goals_home_team = models.IntegerField(default=0)
    goals_away_team = models.IntegerField(default=0)
    score_status = models.CharField(max_length=50, default='not counted')  # Can be 'counted' or 'not counted'
    matchday = models.IntegerField(default=0)

    def __str__(self):
        name = '{} - {}, {}'.format(self.home_team.code, self.away_team.code, self.time.strftime('%d - %m'))
        return name
