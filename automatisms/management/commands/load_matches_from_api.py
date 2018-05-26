# -*- coding: UTF-8 -*-
import os
from time import sleep
from datetime import datetime
import requests
from django.core.management.base import BaseCommand
from matches.models import Match
from competitions.models import CompetitionStage
from teams.models import Team, Player
from countries.models import Country

API_ENDPOINT_URL = "https://soccer.sportmonks.com/api/v2.0/"
API_KEY = "gr33lj1tRZanPATeL1U82l8jVxDxYgenfU9fw2cUI446LEFodUovnCn1skAD"
total_requests = 0


def get_datetime_from_dotted_date_and_time(formated_date, time):
    try:
        date_list = formated_date.split('.')
        day = int(date_list[0])
        month = int(date_list[1])
        year = int(date_list[2])
        time_list = time.split(':')
        hour = int(time_list[0])
        minute = int(time_list[1])
        return datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=0)
    except Exception:
        return None


def get_date_from_dotted_date(formated_date):
    try:
        date_list = formated_date.split('.')
        day = int(date_list[0])
        month = int(date_list[1])
        year = int(date_list[2])
        return datetime(year=year, month=month, day=day).date()
    except Exception:
        return None


def get_date_from_spanish_date(formated_date):
    try:
        date_list = formated_date.split('/')
        day = int(date_list[0])
        month = int(date_list[1])
        year = int(date_list[2])
        return datetime(year=year, month=month, day=day).date()
    except Exception:
        return None


def create_match_from_json(match_json, stage_name, set_live=False):
    global total_requests
    try:
        match_ext_id = match_json['id']
        print("Processing match with ID %s" % match_ext_id)
        match = Match.objects.get(external_id=match_ext_id)
    except Match.DoesNotExist:
        # Get or create teams
        try:
            team1_ext_id = match_json['localteam_id']
            print("Looking for team1 ext ID %s.." % team1_ext_id)
            team1 = Team.objects.get(external_id=team1_ext_id)
        except Team.DoesNotExist:
            print("Team with id %s not found" % team1_ext_id)
            exit(1)
        else:
            print("Team 1 found: %s" % team1)

        try:
            team2_ext_id = match_json['visitorteam_id']
            print("Looking for team1 ext ID %s.." % team2_ext_id)
            team2 = Team.objects.get(external_id=team2_ext_id)
        except Team.DoesNotExist:
            print("Team with id %s not found" % team2_ext_id)
            exit(1)
        else:
            print("Team 2 found: %s" % team2)

        print("Creating new match from json..")
        # Continue creating match
        match = Match()
        match.external_id = match_ext_id
        match.stage = CompetitionStage.objects.get(name=stage_name)
        match.stage_detail = match_json['stage']['data']['name'].lower()
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
        parser.add_argument('--stage', dest='stage_name', required=True, help='Stage name in DB')
        parser.add_argument('--match', dest='match_id', required=False, help='match id in api')
        parser.add_argument('--from', dest='start_date', required=False, help='Start date')
        parser.add_argument('--to', dest='end_date', required=False, help='End date')
        parser.add_argument('--set-live', dest='set_live', required=False, action='store_true')

    def handle(self, *args, **options):
        global total_requests
        try:
            match_id = options['match_id']
            stage_name = options['stage_name']
            start_date = options['start_date']
            end_date = options['end_date']
            set_live = options['set_live']
        except Exception as e:
            print("Error parsing parameters %s" % e)
            exit(1)
        else:
            if match_id == 'all':
                print("Fetching all matches between %s and %s" % (start_date, end_date))
                request_url = API_ENDPOINT_URL + "fixtures/between/{}/{}?api_token={}&include=localTeam,visitorTeam,venue,lineup,events,stats,group,stage".format(start_date, end_date, API_KEY)
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
            else:
                print("Fetching single match with ID %s" % (match_id))
                request_url = API_ENDPOINT_URL + "fixtures/{}?api_token={}&include=localTeam,visitorTeam,venue,lineup,events,stats,group,stage".format(match_id, API_KEY)
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
                # Save list of matches with one single match
                single_match_json = response.json()['data']
                matches_json_list = [single_match_json]

            # Create matches
            for match_json in matches_json_list:
                create_match_from_json(match_json=match_json, stage_name=stage_name, set_live=set_live)

        finally:
            print("Total requests: %s" % total_requests)




