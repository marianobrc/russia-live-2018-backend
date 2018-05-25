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


def create_team_players_from_json(team, squad_json):
    print("Creating players ..")
    for p_json in squad_json:
        # Make player with avalilable data
        try:
            p = p_json['player']['data']
            player_ext_id = p['player_id']
            if Player.objects.filter(external_id=player_ext_id).exists():
                print("Player id %s exist! (skipped)" % player_ext_id)
                continue
            first_name = p['firstname']
            surname = p['lastname']
            common_name = p['common_name']
            if len(common_name) > 11: # Shorten names
                common_name = common_name[:11] + "."  # Limit surname to 11 chars
            player = Player.objects.create(
                external_id=player_ext_id,
                team=team,
                common_name=common_name,
                first_name=first_name,
                last_name=surname,
                nationality=team.country, # All players must be from the team's country in this worldcup
                position=p['position_id'],
            )
        except Exception as e:
            print("Error creating player: %s" % e)
            return None
        else:
            print("New player added: '%s'" % player)



class Command(BaseCommand):
    """
    Load matches from api to database, creating teams and players as needed
    """

    help = 'Load matches from api to database, creating teams and players as needed'

    def handle(self, *args, **options):
        global total_requests
        try:
            print("Fetching teams ..")
            request_url = API_ENDPOINT_URL + 'teams/season/892?api_token={}&include=country,squad.player'.format(
                API_KEY)
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
            teams_json = response.json()
            for team_json in teams_json['data']:
                try: # First try to get or create teh country
                    country_code = team_json['country']['data']['extra']['iso'].lower()
                    country_name = team_json['country']['data']['name']
                    team_country = Country.objects.get(code_iso3=country_code)
                except Country.DoesNotExist:
                    team_country = Country()
                    team_country.name = country_name
                    team_country.code_iso3 = country_code
                    team_country.save()
                except Exception as e:
                    print("Error getting / creating country (team skipped): %s .." % e)
                    continue

                try: # Then create the team
                    team_ext_id = team_json['id']
                    print("Looking for team1 ext ID %s.." % team_ext_id)
                    team = Team.objects.get(external_id=team_ext_id)
                except Team.DoesNotExist:
                        print("Creating Team with ext ID %s .." % team_ext_id)
                        team = Team.objects.create(
                            external_id=team_ext_id,
                            name=team_json['name'],
                            country=team_country,
                        )
                except Exception as e:
                    print("Error creating team (team skipped): %s .." % e)
                    continue
                finally:
                    print("Adding players to team %s .." % team)
                    create_team_players_from_json(team=team, squad_json=team_json['squad']['data'])

        except Exception as e:
            print("Error: %s .." % e)
        finally:
            print("Total requests: %s" % total_requests)




