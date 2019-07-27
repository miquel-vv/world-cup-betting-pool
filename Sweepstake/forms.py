from django import forms
from .models import Participant, Team, Player

class ParticipantForm(forms.Form):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    pot = forms.CharField(max_length=100)
    team_pot_a = forms.ModelChoiceField(queryset=Team.objects.filter(pot=1).order_by('name'))
    team_pot_b = forms.ModelChoiceField(queryset=Team.objects.filter(pot=2).order_by('name'))
    team_pot_c = forms.ModelChoiceField(queryset=Team.objects.filter(pot=3).order_by('name'))
    team_pot_d = forms.ModelChoiceField(queryset=Team.objects.filter(pot=4).order_by('name'))
    topscorer = forms.ModelChoiceField(queryset=Player.objects.all().order_by('name'))
    assist_king = forms.ModelChoiceField(queryset=Player.objects.all().order_by('name'))