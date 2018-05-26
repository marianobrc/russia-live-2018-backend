from django.db import models
from countries.models import Country


# Create your models here.


class Team(models.Model):
    external_id = models.CharField(max_length=20)  # Id in external data provider
    name = models.CharField(max_length=50)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    competition = models.ForeignKey('competitions.Competition', on_delete=models.CASCADE, null=True)


    def __str__(self):
        return self.name


class Player(models.Model):
    external_id = models.CharField(max_length=20)  # Id in external data provider
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    common_name = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50, blank=True)
    nationality = models.ForeignKey(Country, on_delete=models.CASCADE, null=True)
    position = models.CharField(max_length=50, blank=True)
    birthdate = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.common_name
