from django.db import models
from competitions.models import CompetitionStage
from teams.models import Team, Player


class Match(models.Model):
    external_id = models.CharField(max_length=20)  # Id in external data provider
    stage = models.ForeignKey(CompetitionStage, on_delete=models.CASCADE)
    stage_detail = models.CharField(max_length=255, blank=True)
    date = models.DateTimeField()
    stadium = models.CharField(max_length=255, blank=True)
    # Status can be used to filter between live matches, upcoming matches and old matches
    NOT_STARTED = 'NS'  # Not started yet
    PLAYING_FT = 'FT'  # First Time
    HALFTIME = 'HT'  # Half Time
    PLAYING_ST = 'ST'  # Second Time
    FINISHED = 'FN'  # Finished
    MATCH_STATUSES = (
        (NOT_STARTED, 'Not started yet'),
        (PLAYING_FT,   'Playing First Time'),
        (HALFTIME,  'Half Time'),
        (PLAYING_ST, 'Playing Second Time'),
        (FINISHED,  'Finished'),
    )
    status = models.CharField(max_length=20, choices=MATCH_STATUSES, default=NOT_STARTED)
    is_live = models.BooleanField(default=False)
    minutes = models.PositiveIntegerField(default=0)
    team1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="team1")
    team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="team2")
    team1_score = models.PositiveIntegerField(null=True)
    team2_score = models.PositiveIntegerField(null=True)

    def __str__(self):
        return "ID {}, {} {} : {} {} - {}".format(
            self.id, self.team1.name, self.team1_score,  self.team2_score, self.team2.name, self.status
        )


class MatchEvent(models.Model):
    external_id = models.CharField(max_length=20)  # Id in external data provider
    match = models.ForeignKey(Match, related_name='events', on_delete=models.CASCADE)
    team = models.ForeignKey(Team, related_name='team', on_delete=models.CASCADE, null=True)
    event_type = models.CharField(max_length=30)
    minute = models.PositiveIntegerField()
    extra_minute = models.PositiveIntegerField()
    player = models.ForeignKey(Player, on_delete=models.CASCADE, null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    description2 = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return "{} {} {}".format(self.minute, self.event_type, self.player)


class MatchStats(models.Model):
    match = models.ForeignKey(Match, related_name='match_stats', on_delete=models.CASCADE)
    team = models.ForeignKey(Team, related_name='team_stats', on_delete=models.CASCADE)
    possession = models.PositiveIntegerField(default=0)

    def __str__(self):
        return "{} -> {}: {}%".format(self.match, self.team, self.possession)
