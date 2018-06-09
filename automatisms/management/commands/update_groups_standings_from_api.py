# -*- coding: UTF-8 -*-
from time import sleep
import requests
from django.core.management.base import BaseCommand
from competitions.models import  Standing

API_ENDPOINT_URL = "https://soccer.sportmonks.com/api/v2.0/"
API_KEY = "gr33lj1tRZanPATeL1U82l8jVxDxYgenfU9fw2cUI446LEFodUovnCn1skAD"
total_requests = 0


def update_group_standings_from_json(group_json):
    group_name = group_json['name']
    print("Updating standings for %s.." % group_name)
    standings_json = group_json['standings']['data']
    # Update each standing
    for team_standing_json in standings_json:
        try:
            team_name = team_standing_json['team_name']
            print("Updating groups standings for %s.." % team_name)
            points_detail = team_standing_json['overall']
            db_standing = Standing.objects.get(external_id=team_standing_json['team_id'])
            db_standing.position = team_standing_json['position']
            db_standing.played = points_detail['games_played']
            db_standing.won = points_detail['won']
            db_standing.drawn = points_detail['draw']
            db_standing.lost = points_detail['lost']
            db_standing.goal_difference = points_detail['goals_scored'] - points_detail['goals_against']
            db_standing.points = team_standing_json['points']
            db_standing.save()
        except Exception as e:
            print("Error updating groups standings for %s (Skipped): \n %s" % (team_name, e))
            continue




class Command(BaseCommand):
    """
    Load matches from football-api for a competition id or match id
    """

    help = 'Update standings for all groups'

    def handle(self, *args, **options):
        global total_requests
        try:
            print("Fetching all standings for groups stage..")
            request_url = API_ENDPOINT_URL + "standings/season/892?api_token={}&include=team,league,season,round,stage".format(API_KEY)
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
            standings_json_list = response.json()['data']

            # Update standings
            for group_json in standings_json_list:
                update_group_standings_from_json(group_json=group_json)

        except Exception as e:
            print("Error updating groups standings: \n %s" % e)
            exit(1)
        finally:
            print("Total requests: %s" % total_requests)




