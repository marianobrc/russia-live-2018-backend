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


def create_match_from_json(match_json, competition_id, stage_name, set_live=False):
    global total_requests
    try:  # First try to get or create teh country
        print("Looking for competition with ID %s .." % competition_id)
        competition = Competition.objects.get(external_id=competition_id)
    except Exception as e:
        print("Error Looking for competition with ID %s .." % competition_id)
        exit(1)
    try:
        match_ext_id = match_json['id']
        print("Processing match with ID %s" % match_ext_id)
        match = Match.objects.get(external_id=match_ext_id)
    except Match.DoesNotExist:
        # Get or create teams
        try:
            team1_ext_id = match_json['localteam_id']
            print("Looking for team1 ext ID %s.." % team1_ext_id)
            team1 = Team.objects.get(competition=competition, external_id=team1_ext_id)
        except Team.DoesNotExist:
            print("Team with id %s not found" % team1_ext_id)
            return None
        else:
            print("Team 1 found: %s" % team1)

        try:
            team2_ext_id = match_json['visitorteam_id']
            print("Looking for team1 ext ID %s.." % team2_ext_id)
            team2 = Team.objects.get(competition=competition, external_id=team2_ext_id)
        except Team.DoesNotExist:
            print("Team with id %s not found" % team2_ext_id)
            return None
        else:
            print("Team 2 found: %s" % team2)

        # Continue creating match
        print("Creating new match from json..")
        match = Match()
        match.external_id = match_ext_id
        match.stage = CompetitionStage.objects.get(competition=competition, name=stage_name)
        try:
            stage_detail = match_json['stage']['data']['name']
        except Exception as e:
            print("Error getting match stage (Abort): %s " % e)
            exit(1)
        match.stage_detail = stage_detail
        from datetime import datetime
        datetime_str = match_json['time']['starting_at']['date_time']
        datetime_object = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        match.date = datetime_object
        match.stadium = match_json['venue']['data']['name']
        match.team1 = team1
        match.team1_score = match_json['scores']['localteam_score']
        match.team2 = team2
        match.team2_score = match_json['scores']['visitorteam_score']
        match.is_live = set_live
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

            print("Fetching all matches for knockout phase..")
            request_url = API_ENDPOINT_URL + "seasons/892?api_token={}&include=fixtures:filter(stage_id|1729),fixtures.localTeam,fixtures.visitorTeam,fixtures.stage, fixtures.venue".format(API_KEY)
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
            matches_json_list = response.json()['data']['fixtures']['data']

            # Create matches
            for match_json in matches_json_list:
                create_match_from_json(match_json=match_json, competition_id=competition_id, stage_name="eliminatories")

        finally:
            print("Total requests: %s" % total_requests)




