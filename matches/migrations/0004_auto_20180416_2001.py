# Generated by Django 2.0.4 on 2018-04-16 20:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('matches', '0003_match_stage_detail'),
    ]

    operations = [
        migrations.AlterField(
            model_name='matchevent',
            name='match',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='matches.Match'),
        ),
    ]