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

API_ENDPOINT_URL = "http://api.football-api.com/2.0/"
API_KEY = "565ec012251f932ea4000001b409351be5874923474525d0fedd7793"
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


def create_team_players_from_api(team):
    global total_requests
    # Get team players from api and create players in DB
    team_ext_id = team.external_id
    print("Fetching team with ext id %s" % team_ext_id)
    request_url = API_ENDPOINT_URL + "team/{}?Authorization={}".format(team_ext_id, API_KEY)
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
        return
    print("Creating players ..")
    squad_json = response.json()['squad']
    for p in squad_json:
        player_ext_id = p['id']
        print("Fetching player with ext id %s" % player_ext_id)
        request_url = API_ENDPOINT_URL + "player/{}?Authorization={}".format(player_ext_id, API_KEY)
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
                continue
            # Make player with avalilable data
            try:  # Shorten names
                common_name_split = p['name'].replace("&apos;", "'").split()
                first_name = common_name_split[0]
                first_name_initial = first_name[0]
                surname = common_name_split[1]
                if len(surname) > 8:
                    surname = surname[:8] + "."  # Limit surname to 8 chars
                shortened_name = "{}. {}".format(first_name_initial, surname)
            except Exception:
                shortened_name = p['name']
                first_name = p['name']
                surname = ""
            player = Player.objects.create(
                external_id=player_ext_id,
                team=team,
                common_name=shortened_name,
                first_name=first_name,
                last_name=surname,
                nationality=None,  # ToDo map to countries
                position=p['position'],
            )
        else:
            p_json = response.json()
            # Save player in DB
            try:  # Shorten names
                common_name_split = p_json['common_name'].replace("&apos;", "'").split()
                first_name_initial = common_name_split[0][0]
                surname = common_name_split[1]
                if len(surname) > 8:
                    surname = surname[:8] + "."  # Limit surname to 8 chars
                shortened_name = "{}. {}".format(first_name_initial, surname)
            except Exception:
                shortened_name = p_json['common_name']
                first_name = p_json['common_name']
                surname = ""
            player = Player.objects.create(
                external_id=player_ext_id,
                team=team,
                common_name=shortened_name,
                first_name=p_json['firstname'],
                last_name=p_json['lastname'],
                nationality=None, # ToDo map to countries
                position=p_json['position'],
                birthdate=get_date_from_spanish_date(p_json['birthdate']),
            )
        print("New player added: '%s'" % player)


def create_match_from_json(match_json, create_teams=False, update=False, set_live=False):
    global total_requests
    try:
        match_ext__id = match_json['id']
        match = Match.objects.get(external_id=match_ext__id)
    except Match.DoesNotExist:
        # Get or create teams
        try:
            team1_ext_id = match_json['localteam_id']
            print("Looking for team1 ext ID %s.." % team1_ext_id)
            team1 = Team.objects.get(external_id=team1_ext_id)
        except Team.DoesNotExist:
            if create_teams:
                print("Creating Team 1 ext ID %s .." % team1_ext_id)
                team1 = Team.objects.create(
                    external_id=team1_ext_id,
                    name=match_json['localteam_name'],
                    country=Country.objects.get(code_iso3='rus'), # ToDo change it once we have real data
                )
                create_team_players_from_api(team=team1)

            else:
                print("Team ext ID %s not found. Aborted. Run with create_teams = True to create.\n " % team1_ext_id)
                exit(0)
        else:
            print("Team 1 found: %s" % team1)

        try:
            team2_ext_id = match_json['visitorteam_id']
            print("Looking for team1 ext ID %s.." % team2_ext_id)
            team2 = Team.objects.get(external_id=team2_ext_id)
        except Team.DoesNotExist:
            if create_teams:
                print("Creating Team 2 ext ID %s .." % team2_ext_id)
                team2 = Team.objects.create(
                    external_id=team2_ext_id,
                    name=match_json['visitorteam_name'],
                    country=Country.objects.get(code_iso3='deu'),  # ToDo change it once we have real data
                )
                create_team_players_from_api(team2)
            else:
                print("Team ext ID %s not found. Aborted. Run with create_teams = True to create.\n " % team1_ext_id)
                exit(0)
        else:
            print("Team 2 found: %s" % team2)

        print("Creating new match from json..")
        # Continue creating match
        match = Match()
        match.external_id = match_ext__id
        match.stage = CompetitionStage.objects.get(name="groups")
        match.stage_detail = "Group A"
        match.date = get_datetime_from_dotted_date_and_time(formated_date=match_json['formatted_date'], time=match_json['time'])
        match.stadium = match_json['venue']
        match.team1 = team1
        match.team1_score = 0
        match.team2 = team2
        match.team2_score = 0
        match.is_live = set_live
        match.save()
    else:
        if update:
            print("Updating match %s .." % match)
        else:
            print("Match %s .." % match)
        return match


class Command(BaseCommand):
    """
    Load matches from football-api for a competition id or match id
    """

    help = 'Load matches from api to database, creating teams and players as needed'

    def add_arguments(self, parser):
        #parser.add_argument('--comp', dest='comp_id', help='specify bar name')
        parser.add_argument('--match', dest='match_id', help='specify latitude')
        parser.add_argument('--create-teams', dest='create_teams', required=False, action='store_true')
        parser.add_argument('--update', dest='update', required=False, action='store_true')
        parser.add_argument('--set-live', dest='set_live', required=False, action='store_true')

    def handle(self, *args, **options):
        global total_requests
        try:
            #comp_id = options['comp_id']
            match_id = options['match_id']
            create_teams = options['create_teams']
            update = options['update']
            set_live = options['set_live']
        except Exception as e:
            print("Error parsing parameters %s" % e)
            exit(1)
        else:
            if match_id != 'all':
                print("Fetching match with id %s" % match_id)
                request_url = API_ENDPOINT_URL + "matches/{}?Authorization={}".format(match_id, API_KEY)
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
                match_json = response.json()
                create_match_from_json(match_json=match_json, create_teams=create_teams, update=update, set_live=set_live)

            else:
                print("Fetching all matches in teh competition. UNINPLEMENTED")
                exit(0)
        finally:
            print("Total requests: %s" % total_requests)




