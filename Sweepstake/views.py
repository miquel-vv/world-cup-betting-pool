from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseRedirect
from django.views import View
from .models import Player, Participant, Team, Fixture
from .forms import ParticipantForm
from .management.commands.update_scores import Command as update_command

import json


def index(request):
    return render(request, 'Sweepstake/index.html')


def create_user(request):
    if request.method == 'POST':
        form = ParticipantForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            if not password == form.cleaned_data['confirm_password']:
                raise ValidationError

            #All names of participants and users are stored in title case. 
            #This is necessary for links in the templates.
            first_name = form.cleaned_data['first_name'].title()
            last_name = form.cleaned_data['last_name'].title()
            username = " ".join([first_name, last_name])
            try:
                User.objects.create_user(
                    username=username,
                    first_name=first_name, 
                    password=password,
                    last_name=last_name
                )
            except IntegrityError:
                render(request, 'Sweepstake/create_user.html', {'form': ParticipantForm})

            teams = [
                Team.objects.get(name=form.cleaned_data['team_pot_'+chr(i+97)]) for i in range(0,4)
            ]
            topscorer = Player.objects.get(name=form.cleaned_data['topscorer'])
            assist_king = Player.objects.get(name=form.cleaned_data['assist_king'])

            new_partic = Participant(
                name = username,
                topscorer = topscorer,
                assist_king = assist_king
            )
            new_partic.save()

            with new_partic:
                new_partic.pot = form.cleaned_data["pot"].title()
                new_partic.teams.add(*teams)
                new_partic.set_points()

            user = authenticate(username=username, password=password)
            if user is not None:
                return HttpResponseRedirect('/participants')
            
        
    return render(request, 'Sweepstake/create_user.html', {'form': ParticipantForm})


class DashboardView(View):
    '''A mixin class to create dashboard views.'''
    item = None

    def get(self, request, **kwargs):
        name = kwargs["name"].replace('_', ' ')
        self.member = self.item.objects.get_member(name)

        return render(request, 'v2/base.html', context=self.get_context())
    
    def get_context(self):
        context = {
            'overview_type': self.item.__name__,
            'card': self.create_card(),
            'rows': self.create_rows(),
            'bottom_right': self.create_bottom_right()
        }
        return context

    def create_card(self):
        return render_to_string('v2/card.html', context=self.member.get_summary())

    def create_rows(self):
        pot = self.member.pot
        rows = []
        for t in self.item.objects.get_pot_leaderbord(pot):
            rows.append(render_to_string('v2/table_item.html', context=t))
        return rows

    def create_bottom_right(self):
        raise NotImplementedError


class TeamDashboard(DashboardView):

    item = Team
    
    def get_context(self):
        context = super(TeamDashboard, self).get_context()
        context['leaderbord'] = 'Pot ' + chr(self.member.pot)
        return context

    def create_game(self, fixture):
        if not fixture:
            return ''

        summary = fixture.get_summary()
        points = summary['points']['winner'] if summary['winner'] == self.member else summary['points']['loser']
        points = '+ {} Points'.format(points)
        context = {
            'home_team': summary['home_team'],
            'away_team': summary['away_team'],
            'points': points
        }
        return render_to_string('v2/game_card.html', context=context)
    
    def create_bottom_right(self):
        fixtures = Fixture.objects.get_fixtures_of(self.member)
        context = {
            'group_stage': []
        }

        for fixture in fixtures.filter(stage="GROUP_STAGE"):
            context['group_stage'].append(self.create_game(fixture))

        stages = ['last_16', 'quarter_final', 'semi_final']
        stages_api = ['ROUND_OF_16', 'QUARTER_FINALS', 'SEMI_FINALS']

        for stage, stage_api in zip(stages, stages_api):
            try:
                context[stage] = self.create_game(fixtures.filter(stage=stage_api)[0])
            except IndexError:
                context[stage] = 'Disqualified'
        
        try:
            context['final'] = self.create_game(fixtures.filter(stage='FINAL')[0])
        except IndexError:
            try:
                context['final'] = self.create_game(fixtures.filter(stage='3RD_PLACE')[0])
            except IndexError:
                context['final'] = 'Disqualified'

        return render_to_string('v2/games_schema.html', context=context)


class ParticipantDashboard(DashboardView):
    
    item = Participant

    def get_context(self):
        context = super(ParticipantDashboard, self).get_context()
        context['leaderbord'] = self.member.pot
        return context
    
    def create_bottom_right(self):
        context = {
            'countries_chosen': [
                render_to_string('v2/card.html', context=country.get_summary()) for country in self.member.teams.all()
                ]
        }
        return render_to_string('v2/countries_chosen.html', context=context)
    

def leaderbords(request):
    return render(request, 'v2/base_leaderbords.html', context=context)


def teams(request):
    return render(request, 'Sweepstake/teams.html')


class LeaderbordView(View):
    item_class = None

    def get(self, request, **kwargs):
        context = self.get_context()
        if request.user.is_authenticated:
            context['user'] = request.user

        return render(request, 'v2/base_leaderbord.html', context=context)
    
    def get_context(self):
        context = self.create_podium()
        context['leaderbord'] = self.create_leaderbord()
        return context
    
    def create_podium(self):
        top_3 = {}

        for i, item in enumerate(self.item_class.objects.all()[:3]):
            top_3[str(i+1)+'_place'] = render_to_string('v2/card.html', context=item.get_summary())
        
        return top_3
        
    def create_leaderbord(self):
        context = {
            'leaderbord': 'Leaderbord',
            'rows': self.create_rows()
        }
        return render_to_string('v2/leaderbord.html', context=context)

    def create_rows(self):
        rows = []
        for item in self.item_class.objects.all():
            rows.append(render_to_string('v2/table_item.html', context=item.get_summary()))
        return rows


class TeamLeaderbord(LeaderbordView):
    item_class = Team


class ParticipantLeaderbord(LeaderbordView):
    item_class = Participant


def update(request):
    updater = update_command()
    updater.handle()
    return HttpResponseRedirect('/participants')


class Itemview(View):
    '''Class view from v1, not used in v2. But kept for potential functionality.'''
    item = Participant

    def get(self, request, **kwargs):
        name = kwargs['name'].replace('_', ' ')
        try:
            parts = self.item.objects.filter(name=name)
        except KeyError:
            parts = self.item.objects.all()

        response = {self.__class__.__name__: []}
        for part in parts:
            part_dict = part.__dict__
            del part_dict['_state']
            response[self.__class__.__name__].append(part_dict)
        response = json.dumps(response)
        return HttpResponse(response, content_type='application/json')


class Participants(Itemview):
    '''Class view from v1, not used in v2. But kept for potential functionality.'''
    item = Participant


class Teams(Participants):
    '''Class view from v1, not used in v2. But kept for potential functionality.'''
    item = Team


class ItemPosition(View):

    item_class = None

    def get(self, request, **kwargs):
        stages = ['group_stage', 'last_16', 'quarter_final', 'semi_final', 'final']
        positions_list=[]

        name = kwargs['name'].replace('_', ' ')

        item = self.item_class.objects.get(name=name)

        for stage in stages:
            for i, other in enumerate(self.item_class.objects.get_score_after_stage(stage)):
                if item == other[0]:
                    positions_list.append({
                        'round': stage.replace('_', ' ').title(),
                        'points': other[1],
                        'position': i+1
                    })
                    break
        
        response = json.dumps({
            name: positions_list
        })

        return HttpResponse(response, content_type='application/json')


class TeamPosition(ItemPosition):
    item_class = Team

class ParticipantPosition(ItemPosition):
    item_class = Participant

