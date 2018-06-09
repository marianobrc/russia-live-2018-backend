from django.db import models
from teams.models import Team


class Competition(models.Model):
    external_id = models.CharField(max_length=20)  # Id in external data provider
    name = models.CharField(max_length=255)
    region = models.CharField(max_length=255, blank=True) # Optional

    def __str__(self):
        return self.name


class CompetitionStage(models.Model):
    external_id = models.CharField(max_length=20)  # Id in external data provider
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=500, blank=True)
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE)

    def __str__(self):
        return "{} - {}".format(self.name, self.description)


class Standing(models.Model):
    external_id = models.CharField(max_length=20)  # Id in external data provider
    stage = models.ForeignKey(CompetitionStage, on_delete=models.CASCADE)
    sub_group = models.CharField(max_length=50, blank=True) # Group A, Quarters, Final
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    position = models.PositiveIntegerField()
    played = models.PositiveIntegerField(default=0)
    won = models.PositiveIntegerField(default=0)
    drawn = models.PositiveIntegerField(default=0)
    lost = models.PositiveIntegerField(default=0)
    goal_difference = models.IntegerField(default=0)
    points = models.PositiveIntegerField(default=0)
    is_playing = models.BooleanField(default=False)  # There is a match on course that can affect this standing

    class Meta:
        unique_together = (
            ("team", "stage", "sub_group", ),  # One team can be only once in each stage, ie once in groups stage, one in quarters
            ("sub_group", "position",)  # Cant be two teams in the same position in Group A
        )

    def __str__(self):
        return "{}: {} {}".format(self.stage, self.position, self.team.name)