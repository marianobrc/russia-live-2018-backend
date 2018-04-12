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
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    position = models.PositiveIntegerField()
    played = models.PositiveIntegerField()
    won = models.PositiveIntegerField()
    drawn = models.PositiveIntegerField()
    lost = models.PositiveIntegerField()
    goal_difference = models.PositiveIntegerField()
    points = models.PositiveIntegerField()

    class Meta:
        unique_together = (
            ("stage", "team",),  # One team can be only once in groups stage
            ("stage", "position",)  # Cant be two teams in position one of groups stage
        )

    def __str__(self):
        return "{}: {} {}".format(self.stage, self.position, self.team.name)