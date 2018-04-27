# Generated by Django 2.0.4 on 2018-04-12 15:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('countries', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('external_id', models.CharField(max_length=20)),
                ('common_name', models.CharField(max_length=50)),
                ('first_name', models.CharField(max_length=50)),
                ('last_name', models.CharField(max_length=50)),
                ('position', models.CharField(blank=True, max_length=50)),
                ('birthdate', models.DateField(blank=True)),
                ('nationality', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='countries.Country')),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('external_id', models.CharField(max_length=20)),
                ('name', models.CharField(max_length=50)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='countries.Country')),
            ],
        ),
        migrations.AddField(
            model_name='player',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='teams.Team'),
        ),
    ]