# Generated by Django 2.0.4 on 2018-04-18 19:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('matches', '0007_match_minutes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='matchevent',
            name='player',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='teams.Player'),
        ),
    ]
