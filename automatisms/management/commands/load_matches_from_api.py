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
    # Get team players from api and create players in DB
    team_ext_id = team.external_id
    print("Fetching team with ext id %s" % team_ext_id)
    request_url = API_ENDPOINT_URL + "team/{}?Authorization={}".format(team_ext_id, API_KEY)
    print(request_url)
    response = requests.get(request_url, verify=False)
    if response.status_code != 200:
        print("Error status: %s" % response.status_code)
        exit(1)
    print("Creating players ..")
    squad_json = response.json()['squad']
    for p in squad_json:
        player_ext_id = p['id']
        print("Fetching player with ext id %s" % player_ext_id)
        request_url = API_ENDPOINT_URL + "player/{}?Authorization={}".format(player_ext_id, API_KEY)
        print(request_url)
        response = requests.get(request_url, verify=False)
        if response.status_code != 200:
            print("Error status: %s" % response.status_code)
            continue
        p_json = response.json()
        # Save player in DB
        player = Player.objects.create(
            external_id=player_ext_id,
            team=team,
            common_name=p_json['common_name'],
            first_name=p_json['firstname'],
            last_name=p_json['lastname'],
            nationality=None, # ToDo map to countries
            position=p_json['position'],
            birthdate=get_date_from_spanish_date(p_json['birthdate']),
        )
        print("New player added: '%s'" % player)


def create_match_from_json(match_json, create_teams=False, update=False):
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
                    country=Country.objects.get(code_iso3='arg'), # ToDo change it once we have real data
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
                    country=Country.objects.get(code_iso3='col'),  # ToDo change it once we have real data
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
        match.stage = CompetitionStage.objects.get(name="Groups")
        match.stage_detail = "Group A"
        match.date = get_date_from_dotted_date(match_json['formatted_date'])
        match.stadium = match_json['venue']
        match.team1 = team1
        match.team1_score = match_json['localteam_score']
        match.team2 = team2
        match.team2_score = match_json['visitorteam_score']
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
        parser.add_argument('--create_teams', dest='create_teams', required=False, action='store_true')
        parser.add_argument('--update', dest='update', required=False, action='store_true')


    def handle(self, *args, **options):
        try:
            #comp_id = options['comp_id']
            match_id = options['match_id']
            create_teams = options['create_teams']
            update = options['update']
        except Exception as e:
            print("Error parsing parameters %s" % e)

        if match_id != 'all':
            print("Fetching match with id %s" % match_id)
            request_url = API_ENDPOINT_URL + "matches/{}?Authorization={}".format(match_id, API_KEY)
            print(request_url)
            response = requests.get(request_url, verify=False)
            if response.status_code != 200:
                print("Error status: %s" % response.status_code)
                exit(1)
            match_json = response.json()
            create_match_from_json(match_json=match_json, create_teams=create_teams, update=update)

        else:
            print("Fetching all matches in teh competition. UNINPLEMENTED")
            exit(0)




