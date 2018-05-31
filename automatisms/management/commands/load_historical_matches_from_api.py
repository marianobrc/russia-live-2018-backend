# -*- coding: UTF-8 -*-
import os
from time import sleep
from datetime import datetime
import requests
from django.core.management.base import BaseCommand
from matches.models import Match
from competitions.models import CompetitionStage, Competition
from teams.models import Team, Player
from countries.models import Country

API_ENDPOINT_URL = "https://soccer.sportmonks.com/api/v2.0/"
API_KEY = "gr33lj1tRZanPATeL1U82l8jVxDxYgenfU9fw2cUI446LEFodUovnCn1skAD"
total_requests = 0


def create_match_from_json(team1, team2, match_json ):
    global total_requests

    try:
        match_ext_id = match_json['id']
        print("Processing match with ID %s" % match_ext_id)
        match = Match.objects.get(external_id=match_ext_id)
    except Match.DoesNotExist:
        # Continue creating match
        print("Creating new match from json..")
        localteam_id = match_json['localteam_id']
        visitorteam_id = match_json['visitorteam_id']
        if int(team1.external_id) == localteam_id and int(team2.external_id) == visitorteam_id:
            local_team = team1
            visitor_team = team2
        else:
            local_team = team2
            visitor_team = team1

        match = Match()
        match.external_id = match_ext_id
        match.stage = None
        match.stage_detail = match_json['stage']['data']['name'].lower()
        from datetime import datetime
        datetime_str = match_json['time']['starting_at']['date_time']
        datetime_object = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        match.date = datetime_object
        match.stadium = match_json['venue']['data']['name']
        match.team1 = local_team
        match.team1_score = match_json['scores']['localteam_score']
        match.team2 = visitor_team
        match.team2_score = match_json['scores']['visitorteam_score']
        match.is_live = False
        match.is_history = True # Historical match <<<
        match.save()
        print("Match saved: %s" % match)
    else:
        print("Match %s already exist (skiped).." % match)
    return match


class Command(BaseCommand):
    """
    Load matches from football-api for a competition id or match id
    """

    help = 'Load matches from api to database, creating teams and players as needed'

    def add_arguments(self, parser):
        parser.add_argument('--competition', dest='competition_id', required=True, help='Competition EXT ID')


    def handle(self, *args, **options):
        global total_requests
        try:
            competition_id = options['competition_id']

        except Exception as e:
            print("Error parsing parameters %s" % e)
            exit(1)
        else:

            try:  # First try to get the current competition
                print("Looking for competition with ID %s .." % competition_id)
                current_competition = Competition.objects.get(external_id=competition_id)
            except Exception as e:
                print("Error Looking for competition with ID %s .." % competition_id)
                exit(1)

            # Then get competition matches in DB
            current_matches = Match.objects.filter(stage__competition=current_competition, is_history=False)
            for match in current_matches:
                team1 = match.team1
                team2 = match.team2
                team1_ext_id = team1.external_id
                team2_ext_id = team2.external_id
                print("Fetching historical matches between %s and %s" % (team1, team2))
                request_url = API_ENDPOINT_URL + "head2head/{}/{}?api_token={}&include=localTeam,visitorTeam,stage,venue".format(
                    team1_ext_id, team2_ext_id, API_KEY
                )
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
                        sleep(30) # Slow down
                    exit(1)
                # Save list of matches
                matches_json_list = response.json()['data']
                # Create matches
                for match_json in matches_json_list:
                    create_match_from_json(
                        team1=team1,
                        team2=team2,
                        match_json=match_json
                    )

        finally:
            print("Total requests: %s" % total_requests)




