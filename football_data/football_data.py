from football_data_api import CompetitionData


class CompetitionInterface(CompetitionData):

    def __init__(self, competition_name):
        super().__init__(competition_name=competition_name)

    def get_competition_info(self):
        return self.get_info('competition')

    def get_matches(self, **kwargs):
        matches = super().get_info('matches', **kwargs)['matches']

        for match in matches:
            yield {
                'fd_id': match['id'],
                'home_team': match['homeTeam']['name'],
                'away_team': match['awayTeam']['name'],
                'stage': match['stage'],
                'matchday': match['matchday'],
                'status': match['status'],
                'time': match['utcDate'],
                'score': match['score']
            }

    def get_teams(self, **kwargs):
        teams = super().get_info('teams', **kwargs)

        for team in teams:
            yield {
                'fd_id': team['id'],
                'name': team['name'],
                'code': team['tla'],
            }
