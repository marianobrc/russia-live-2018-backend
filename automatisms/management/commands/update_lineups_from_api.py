import json
from time import sleep
import requests
from django.core.management.base import BaseCommand
from matches.models import Match, MatchEvent, MatchStats
from teams.models import Player
from expo_notifications.models import PushToken
from expo_notifications.core import send_push_message_broadcast

API_ENDPOINT_URL = "https://soccer.sportmonks.com/api/v2.0/"
API_KEY = "gr33lj1tRZanPATeL1U82l8jVxDxYgenfU9fw2cUI446LEFodUovnCn1skAD"
total_requests = 0


def update_match_lineups_from_json(match, lineups_json):
    print("Updating lineups of match %s .." % match)
    # Team 1 is always local and Team 2 is always visitor
    team1_id = int(match.team1.external_id)
    team2_id = int(match.team2.external_id)
    team1_players = [('%4s' % p['number']) + ('. %s' % p['player_name']) for p in lineups_json if p['number'] is not None and p['team_id'] == team1_id]
    team2_players = [('%4s' % p['number']) + ('. %s' % p['player_name']) for p in lineups_json if p['number'] is not None and p['team_id'] == team2_id]
    if len(team1_players) > 0:
        match.team1_lineup = team1_players
    if len(team2_players) > 0:
        match.team2_lineup = team2_players
    match.save()
    print("Updating lineups of match %s ..DONE" % match)
    return match


class Command(BaseCommand):
    """
    Update live matches from api to database
    """

    help = 'Update live matches from api to database'

    def add_arguments(self, parser):
        parser.add_argument('--match', dest='match_id', help='match to track')
        parser.add_argument('--old-match', dest='is_old_match', required=False, action='store_true')



    def handle(self, *args, **options):
        global total_requests
        try:
            match_id = options['match_id']
            is_old_match = options['is_old_match']
        except Exception as e:
            print("Error %s" % e)
            exit(1)
        else:
            # Get current live matches from API
            print("Fetching single match with ID %s" % (match_id))

            if is_old_match:
                request_url = API_ENDPOINT_URL + "fixtures/{}?api_token={}&include=localTeam,visitorTeam,venue,lineup".format(
                    match_id, API_KEY)
            else:
                request_url = API_ENDPOINT_URL + "livescores/?api_token={}&include=localTeam,visitorTeam,venue,lineup".format(API_KEY)
            print(request_url)
            try:
                response = requests.get(request_url, verify=False, timeout=10)
                total_requests += 1
            except Exception:
                print("REQUEST ERROR, RETRYING..")
                sleep(1)
                response = requests.get(request_url, verify=False, timeout=10)
                total_requests += 1
            if response.status_code != 200:
                print("Error status: %s, %s" % (response.status_code, response.json()))
                if response.status_code == 429:
                    print("API LIMIT EXCEEDED: Total requests: %s" % total_requests)
                    sleep(30)  # Slow down
                exit(1)

            # Check if is single amtch or all
            if is_old_match:
                live_matches_json = [ response.json()['data'] ]
            else:
                live_matches_json = response.json()['data']

            live_matches_ids = [ j['id'] for j in live_matches_json ]
            # If is a specific match nad isn't live then abort
            if match_id != 'all' and int(match_id) not in live_matches_ids:
                print("Match with ID %s not found (Aborted)" % match_id)
                exit(1)
            # Iterate all live matches
            for match_json in live_matches_json:

                try:
                    ext_match_id = match_json['id']
                    if match_id != 'all' and int(ext_match_id) != int(match_id):
                        print("Match with ID %s skipped.." % ext_match_id)
                        continue
                    match = Match.objects.get(external_id=ext_match_id)
                except Match.DoesNotExist:
                    print("Match with ID %s not found (Skipped)" % ext_match_id)
                    continue
                except Exception as e:
                    print("Error updating Match with ID %s (Skipped): \n %s" % (ext_match_id, e))
                    continue

                try: # Update all match info, events and stats
                    lineups_json = match_json['lineup']['data']
                    update_match_lineups_from_json(match, lineups_json)
                except Exception as e:
                    print("ERROR UPDATING MATCH: %s" % e)
                    sleep(1)
                    continue

        finally:
            print("Total requests: %s" % total_requests)
