from time import sleep
import requests
from django.core.management.base import BaseCommand
from matches.models import Match, MatchEvent, MatchStats
from teams.models import Player
from expo_notifications.models import PushToken
from expo_notifications.core import send_push_message_broadcast


def set_default_team_stats(match, team):
    try:  # Create or update stats
        team_stats = MatchStats.objects.get(match=match, team=team)
    except MatchStats.DoesNotExist:
        team_stats = MatchStats(match=match, team=team)
    finally:
        team_stats.possession = 0
        team_stats.passes = 0
        team_stats.passes_accuracy = 0
        team_stats.shots_total = 0
        team_stats.shots_ongoal = 0
        team_stats.shots_accuracy = 0
        team_stats.dangerous_attacks = 0
        team_stats.courner_kicks = 0
        team_stats.free_kicks = 0
        team_stats.yellow_cards = 0
        team_stats.red_cards = 0
        team_stats.substitutions = 0
        team_stats.fouls = 0
        team_stats.save()


class Command(BaseCommand):
    """
    Create default empty stats
    """

    help = 'Update live matches from api to database'

    def handle(self, *args, **options):

        matches = Match.objects.filter(is_history=False, status=Match.NOT_STARTED)
        for match in matches:
            print("Settings stats of match %s .." % match)
            try: # Team 1 is always local and Team 2 is always visitor
                team1 = match.team1
                team2 = match.team2
                print("Settings stats for team 1 %s .." % team1)
                set_default_team_stats(match, team1)
                print("Settings stats for team 2 %s .." % team2)
                set_default_team_stats(match, team2)
            except Exception as e:
                print("ERROR UPDATING MATCH STATS: %s" % e)
