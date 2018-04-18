# Generated by Django 2.0.4 on 2018-04-18 17:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('matches', '0005_matchevent_team'),
    ]

    operations = [
        migrations.AlterField(
            model_name='matchevent',
            name='team',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='team', to='teams.Team'),
        ),
    ]
