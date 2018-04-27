# Generated by Django 2.0.4 on 2018-04-26 14:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='competitionstage',
            name='sub_id',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='standing',
            name='drawn',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='standing',
            name='goal_difference',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='standing',
            name='lost',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='standing',
            name='played',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='standing',
            name='points',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='standing',
            name='won',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
