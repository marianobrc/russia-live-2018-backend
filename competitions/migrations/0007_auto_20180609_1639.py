# Generated by Django 2.0.4 on 2018-06-09 16:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0006_auto_20180502_2244'),
    ]

    operations = [
        migrations.AlterField(
            model_name='standing',
            name='goal_difference',
            field=models.IntegerField(default=0),
        ),
    ]
