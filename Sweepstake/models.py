from django.db import models
from django.contrib.postgres.fields import JSONField
from django.db.models import Q
from collections import defaultdict
import logging

logging.basicConfig(filename='log/log.txt',
                    format='%(asctime)s:%(name)s:%(levelname)s:%(message)s',
                    level=logging.DEBUG)

logger = logging.getLogger(__name__)


def get_suffix(position):
    '''Helper function to get the suffix of a number's suffix'''
    suffices = ['th', 'st', 'nd', 'rd'] + 6*['th']
    return suffices[int(str(position)[-1])]


class CardCreatorMixin():
    '''A class which provides the get_summary() functionality needed to create
    cards and row elements.'''

    def get_image(self):
        '''Implement in child as they each have their specific image.'''
        raise NotImplementedError
    
    def get_summary(self, position=0, verbose=True):
        ''' This function returns a dictionary that is passed as context to create 
            a countries card or table row in the view tab. The function should be used
            by the manager, as it requires the position to create the output.
            args:
                position: Tuple (position, suffix) passed by the manager
                verbose: Boolean. If true, '"Place" and "Points" get added to the
                        position and points number.
            output:
                A dictionary formatted as: {
                    name:
                    image:
                    position:
                    points:
                }
        '''
        position = position if position else self.position

        if verbose:
            place = '{0}<sup>{1}</sup> Place'.format(position, get_suffix(position)) 
            points = '{} Points'.format(self.points)
        else:
            place = '{0}<sup>{1}</sup>'.format(position, get_suffix(position)) 
            points = '{}'.format(self.points)

        summary = {
            'class': self.__class__.__name__,
            'name': self.name,
            'image': self.get_image(),
            'position': place,
            'points': points
        }

        return summary

class GeneralManager(models.Manager):
    '''The general manager adds functionality required for both teams and participants
    which are called members in this class.'''

    def get_pot_leaderbord(self, pot_name):
        '''Creates a list of dicts (from the member.get_summary()) function, to create a 
        leaderbord specifically for the pot.
        args:
            pot_name: Name of the pot for which to create a leaderbord.
        output:
            list of dicts (from the member.get_summary()).
        '''

        pot_list = []
        for i, member in enumerate(super(GeneralManager, self).get_queryset().filter(pot=pot_name)):
            pot_list.append(member.get_summary(i+1, False))
        
        return pot_list
    
    def get_member(self, name):
        '''Gets a member and adds the position of that member. getting the member normally
        doesn't add the position of the member.'''

        for i, member in enumerate(super(GeneralManager, self).get_queryset()):
            if member.name == name:
                member.position = i+1
                return member
        
        raise KeyError("Member " + name + " not found.")
    
    def get_score_after_stage(self, stage):
        '''Returns all members as queryset() after a certain stage. Together with the points
        and position after that stage.
        args: 
            the stage group_stage, last_16, quarter_final, semi-final or final
        output: 
            list sorted by position, with each list item being the tuple (Member, points).
        '''

        stage_keys = ['1','2','3','ROUND_OF_16','QUARTER_FINALS', 'SEMI_FINALS', '3RD_PLACE', 'FINAL']
        stage_limit = {    
            'group_stage': 2,
            'last_16': 3,
            'quarter_final': 4,
            'semi_final': 5,
            'final': 7
        }

        members = []
        for member in self.get_queryset():
            points = 0
            for i in range(0,stage_limit[stage]+1):
                try:
                    points += member.previous_points[stage_keys[i]]
                except KeyError:
                    if stage_keys[i] == '3RD_PLACE':
                        continue
                    break

            members.append((member, points))
    
        members.sort(reverse=True, key=lambda x: x[1])
        return members
    
    def get_position(self, member):
        for i, m in enumerate(self.all()):
            if m==member:
                return i+1

class Team(models.Model, CardCreatorMixin):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=3)
    pot = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    previous_points = JSONField(default={})
    objects = GeneralManager()

    class Meta:
        ordering = ['-points']
    
    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._position = None 
        return instance

    def __str__(self):
        return self.name

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.points = 0
        for previous in self.previous_points.values():
            self.points += previous
        self.save()

    def get_image(self):
        name = self.name.lower().replace(' ', '-')
        return 'v2/icons/countries/{}.svg'.format(name)
    
    @property
    def position(self):
        if not self._position:
            self._position = Team.objects.get_position(self)
        return self._position
    
    @position.setter
    def position(self, val):
        self._position = val
    


class Player(models.Model):
    name = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    goals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Participant(models.Model, CardCreatorMixin):
    name = models.CharField(max_length=200)
    teams = models.ManyToManyField(Team)
    topscorer = models.ForeignKey(Player, related_name='topscorer', on_delete=models.CASCADE)
    assist_king = models.ForeignKey(Player, related_name='assist_king', on_delete=models.CASCADE)
    points = models.IntegerField(default=0)
    previous_points = JSONField(default={})
    location = models.CharField(max_length=50)
    pot = models.CharField(max_length=50) #To create subgroups within participants.

    objects = GeneralManager()

    class Meta:
        ordering = ['-points']

    def __str__(self):
        return self.name

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._position = None 
        return instance

    def set_points(self):
        self.previous_points = defaultdict(int)
        for team in self.teams.all():
            team_points = 0
            for matchday, pts in team.previous_points.items():
                team_points += pts
                self.previous_points[matchday] += pts
            assert team_points == team.points

    def get_image(self):
        return 'v2/icons/user-shape-card.svg'

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.points = 0
        for previous in self.previous_points.values():
            self.points += previous
        self.save()
    
    @property
    def position(self):
        if not self._position:
            self._position = Participant.objects.get_position(self)
        return self._position
    
    @position.setter
    def position(self, val):
        self._position = val


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

    def get_fixtures_of(self, team):
        '''Gets all the fixtures of a team, home and away.'''
        return self.filter(Q(home_team=team) | Q(away_team=team))


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
            logger.info('Match {} vs {} in the {}, matchday {} got points set to {}'
                        .format(self.home_team, self.away_team, self.stage, self.matchday, self.points))
        except KeyError:
            logger.exception('{} raised keyerror'.format(self.stage))
            self.points['winner'], self.points['loser'] = (2, 0)

    def give_points(self):
        """Gives the points to the appropriate team"""
        logger.info('{} - {} won by {}'.format(self.home_team, self.away_team, self.score['winner']))

        if self.score['winner'] == 'DRAW':
            logger.info('{} - {} was draw'.format(self.home_team, self.away_team))
            self.points['winner'] = 1   # Draw only happens in group stage so only one point each.
            self.points['loser'] = 1
            winner = self.home_team     # Named winner just for ease
        else:
            winner = self.__getattribute__(self.score['winner'].lower())

        if winner == self.home_team:
            loser = self.away_team
        else:
            loser = self.home_team

        logger.info('{home_team}{home_team_points} - {away_team_points}{away_team} was won by {winner}'
                    .format(home_team=self.home_team,
                            home_team_points=self.score['fullTime']['homeTeam'],
                            away_team=self.away_team,
                            away_team_points=self.score['fullTime']['awayTeam'],
                            winner=winner))

        with winner as win:
            win.previous_points[self.get_previous_name()] = self.points['winner']

        with loser as lost:
            lost.previous_points[self.get_previous_name()] = self.points['loser']

        self.counted = True

    def get_previous_name(self):
        """Matchday = null if fixture in knock out phase. So need to identify the right name to use."""
        if self.matchday:
            previous_name = self.matchday
        else:
            previous_name = self.stage
        return previous_name

    def get_summary(self):
        '''Creates a summary that is used by a view to create a game card.
        args:/
        output: dict {
            home_team: {name:, goals:, image:},
            away_team: {name:, goals:, image:},
            points: points,
            winner: winner
            }
        '''

        home_team = {
            'name': self.home_team.name,
            'goals': self.score['fullTime']['homeTeam'],
            'image': self.home_team.get_image()
        }
        away_team = {
            'name': self.away_team.name,
            'goals': self.score['fullTime']['awayTeam'],
            'image': self.away_team.get_image()
        }

        winner = self.home_team if home_team['goals'] >= away_team['goals'] else self.away_team

        summary = {
            'home_team': home_team,
            'away_team': away_team,
            'points': self.points,
            'winner': winner
        }
        return summary

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save()
