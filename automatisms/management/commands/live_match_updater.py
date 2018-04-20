from time import sleep
import requests
from django.core.management.base import BaseCommand
from matches.models import Match, MatchEvent
from teams.models import Player

API_ENDPOINT_URL = "http://api.football-api.com/2.0/"
API_KEY = "565ec012251f932ea4000001b409351be5874923474525d0fedd7793"


def get_match_status(api_match_status):
    if api_match_status == "FT":
        return Match.FINISHED
    elif api_match_status == "HT":
        return Match.HALFTIME
    else:
        return Match.PLAYING_FT  # ToDo unify playing status


def update_match_status_from_json(match, match_json):
    print("Updating score of match %s .." % match)
    # Team 1 is always local and Team 2 is always visitor
    match.status = get_match_status(api_match_status=match_json['status'])
    if match_json['timer'] != "":
        match.minutes = int(match_json['timer'])
    match.team1_score = match_json['localteam_score']
    match.team2_score = match_json['visitorteam_score']
    match.save()
    print("Updating score of match %s ..DONE" % match)


def get_event_type(api_event_type):
    if api_event_type == "goal":
        return "goal"
    elif api_event_type == "subst":
        return "player_change"
    elif api_event_type == "yellowcard":
        return "yellow_card"
    elif api_event_type == "redcard":
        return "red_card"
    else:
        return api_event_type


def update_match_events_from_json(match, events_json):
    print("Updating events of match %s .." % match)
    # Add only new events checking external_id
    current_match_event_ids = match.events.all().values_list('external_id', flat=True)
    new_events_json = [ev for ev in events_json if ev['id'] not in current_match_event_ids]
    for event_json in new_events_json:
        new_event = MatchEvent()
        new_event.external_id = event_json['id']
        new_event.match = match
        new_event.team = match.team2 if event_json['team'] == 'visitorteam' else match.team1
        new_event.event_type = get_event_type(api_event_type=event_json['type'])
        new_event.minute = int(event_json['minute']) if event_json['minute'] != "" else 0
        new_event.extra_minute = int(event_json['extra_min']) if event_json['extra_min'] != "" else 0
        try:
            player = Player.objects.get(external_id=event_json['player_id'])
        except Exception:
            player = None
        new_event.player = player
        new_event.description = "" # ToDo check when to use it
        new_event.description2 = event_json["assist"] if new_event.event_type == 'player_change' else ""
        new_event.save()
        print("New event saved:  %s" % new_event)
    print("Updating events of match %s ..DONE" % match)


class Command(BaseCommand):
    """
    Keep track of livematch and update database
    """

    help = 'Load matches from api to database, creating teams and players as needed'

    def add_arguments(self, parser):
        parser.add_argument('--match', dest='match_id', help='match to track')
        parser.add_argument('--set-live', dest='set_live', required=False, action='store_true')


    def handle(self, *args, **options):
        try:
            match_id = options['match_id']
            set_live = options['set_live']
        except Exception as e:
            print("Error %s" % e)
            exit(1)
        try:
            match = Match.objects.get(id=match_id)
        except Match.DoesNotExist:
            print("Match with ID %s not found " % match_id)
            exit(1)

        if set_live:
            match.is_live = True
            match.save()

        # Get match data and keep track
        while True:
            print("Fetching match with ID %s -> external id %s" % (match.id, match.external_id))
            request_url = API_ENDPOINT_URL + "matches/{}?Authorization={}".format(match.external_id, API_KEY)
            print(request_url)
            response = requests.get(request_url, verify=False)
            if response.status_code != 200:
                print("Error status: %s" % response.status_code)
                exit(1)
            match_json = response.json()
            update_match_status_from_json(match, match_json)
            events_json = match_json['events']
            update_match_events_from_json(match, events_json)
            print("SLEEPING 2 seconds..")
            sleep(2)
