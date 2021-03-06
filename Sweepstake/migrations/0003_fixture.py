# Generated by Django 2.0.6 on 2018-06-19 09:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Sweepstake', '0002_auto_20180614_2349'),
    ]

    operations = [
        migrations.CreateModel(
            name='Fixture',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(max_length=50)),
                ('time', models.DateTimeField()),
                ('goals_home_team', models.IntegerField(default=0)),
                ('goals_away_team', models.IntegerField(default=0)),
                ('score_status', models.CharField(default='not counted', max_length=50)),
                ('away_team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='away_team', to='Sweepstake.Team')),
                ('home_team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='home_team', to='Sweepstake.Team')),
            ],
        ),
    ]
