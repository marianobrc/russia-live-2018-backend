# Generated by Django 2.0.4 on 2018-05-31 23:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('matches', '0015_match_is_history'),
    ]

    operations = [
        migrations.AlterField(
            model_name='match',
            name='stage',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='competitions.CompetitionStage'),
        ),
    ]
