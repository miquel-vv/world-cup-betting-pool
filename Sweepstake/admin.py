from django.contrib import admin
from .models import Team, Participant, Fixture, Player
# Register your models here.

admin.site.register(Team)
admin.site.register(Participant)
admin.site.register(Fixture)
admin.site.register(Player)