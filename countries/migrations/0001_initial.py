# Generated by Django 2.0.4 on 2018-04-12 15:15

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code_iso3', models.CharField(db_index=True, max_length=3, unique=True)),
                ('name', models.CharField(max_length=50)),
            ],
        ),
    ]
