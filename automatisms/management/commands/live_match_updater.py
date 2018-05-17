from time import sleep
import requests
from django.core.management.base import BaseCommand
from matches.models import Match, MatchEvent
from teams.models import Player
from expo_notifications.models import PushToken
from expo_notifications.core import send_push_message_broadcast

API_ENDPOINT_URL = "http://api.football-api.com/2.0/"
API_KEY = "565ec012251f932ea4000001b409351be5874923474525d0fedd7793"
total_requests = 0


def get_match_status(api_match_status, timer):
    if api_match_status == "FT":
        return Match.FINISHED
    elif api_match_status == "HT":
        return Match.HALFTIME
    elif timer == "":
        return Match.NOT_STARTED
    else:
        return Match.PLAYING_FT  # ToDo unify playing status


def update_match_status_from_json(match, match_json):
    print("Updating score of match %s .." % match)
    # Team 1 is always local and Team 2 is always visitor
    match.status = get_match_status(api_match_status=match_json['status'], timer=match_json['timer'])
    if match_json['timer'] != "":
        match.minutes = int(match_json['timer'].replace('+', ''))  # In extra time a plus sign appears
    match.team1_score = match_json['localteam_score'].replace('?', '0')
    match.team2_score = match_json['visitorteam_score'].replace('?', '0')
    match.save()
    print("Updating score of match %s ..DONE" % match)
    return match


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
        return "match_generic"


def update_match_events_from_json(match, events_json):
    print("Updating events of match %s .." % match)
    device_tokens = [t.token for t in PushToken.objects.filter(active=True)]
    # Add only new events checking external_id
    current_match_event_ids = match.events.all().values_list('external_id', flat=True)
    if len(current_match_event_ids) == 0 and match.status != Match.NOT_STARTED:
        # Add first event, match started
        new_event = MatchEvent()
        new_event.external_id = '-1'
        new_event.match = match
        new_event.team = match.team2
        new_event.event_type = 'match_started'
        new_event.minute = 0
        new_event.extra_minute = 0
        new_event.description = "Match Started"
        new_event.description2 = ""
        new_event.save() # Continue processing other events in this case
        title = "Match started"
        message = "{} vs {}".format(match.team1.country.code_iso3, match.team2.country.code_iso3)
        send_push_message_broadcast(token_list=device_tokens, title=title, message=message)
    elif match.status == Match.HALFTIME and MatchEvent.objects.filter(match=match, event_type='half_time').count() == 0:
        new_event = MatchEvent()
        new_event.external_id = '-1'
        new_event.match = match
        new_event.team = match.team2
        new_event.event_type = 'half_time'
        new_event.minute = 45 # ToDo: check how to handle minutes in half time
        new_event.extra_minute = 0
        new_event.description = "Half Time"
        new_event.description2 = ""
        new_event.save()
        title = "Half Time"
        message = "{} {} - {} {}".format(match.team1.country.code_iso3, match.team1_score,
                                         match.team2_score, match.team2.country.code_iso3)
        send_push_message_broadcast(token_list=device_tokens, title=title, message=message)
        return # Don't update more events during half-time
    elif match.status == Match.FINISHED and MatchEvent.objects.filter(match=match, event_type='match_finished').count() == 0:
        new_event = MatchEvent()
        new_event.external_id = '-1'
        new_event.match = match
        new_event.team = match.team2
        new_event.event_type = 'match_finished'
        new_event.minute = 100  # ToDo: check how to handle minutes in half time
        new_event.extra_minute = 0
        new_event.description = "Finished"  # ToDo check when to use it
        new_event.description2 = ""
        new_event.save()
        title = "Match ended"
        message = "{} {} - {} {}".format(match.team1.country.code_iso3, match.team1_score,
                                         match.team2_score, match.team2.country.code_iso3)
        send_push_message_broadcast(token_list=device_tokens, title=title, message=message)
        print("Match %s ..FINISHED -> STOPPED UPDATING." % match)
        exit(0)

    new_events_json = [ev for ev in events_json if ev['id'] not in current_match_event_ids]
    for event_json in new_events_json:
        if event_json['player_id'] == "" and event_json['player'] == "":
            print("API ERROR: Player data missing, retry later..")
            return # Abort and retry in some seconds, results are not complete yet
        team = match.team2 if event_json['team'] == 'visitorteam' else match.team1
        new_event = MatchEvent()
        new_event.external_id = event_json['id']
        new_event.match = match
        new_event.team = team
        new_event.event_type = get_event_type(api_event_type=event_json['type'])
        new_event.minute = int(event_json['minute']) if event_json['minute'] != "" else 0
        new_event.extra_minute = int(event_json['extra_min']) if event_json['extra_min'] != "" else 0
        try:
            player = Player.objects.get(external_id=event_json['player_id'])
        except Exception:
            player_fullname = event_json['player'].replace("&apos;", "'")
            print("Creating missing player: %s" % player_fullname)
            # Make player with avalilable data
            try:  # Shorten names
                common_name_split = player_fullname.split()
                first_name = common_name_split[0]
                first_name_initial = first_name[0]
                surname = common_name_split[1]
                if len(surname) > 8:
                    surname = surname[:8] + "."  # Limit surname to 8 chars
                shortened_name = "{}. {}".format(first_name_initial, surname)
            except Exception:
                shortened_name = player_fullname
                first_name = player_fullname
                surname = ""
            # Create the new player
            new_player = Player.objects.create(
                external_id=event_json['player_id'],
                team=team,
                common_name=shortened_name,
                first_name=first_name,
                last_name=surname,
                nationality=None,  # ToDo map to countries
                position="",
            )
            player = new_player
        new_event.player = player
        new_event.description = "" # ToDo check when to use it
        new_event.description2 = event_json["assist"] if new_event.event_type == 'player_change' else ""
        new_event.save()
        print("New event saved:  %s" % new_event)
        # Notify goals
        if new_event.event_type == 'goal':
            title = "Goal! {}".format(new_event.team.country.code_iso3.upper())
            message = "{} {} - {} {}".format(match.team1.country.code_iso3, match.team1_score,
                                             match.team2_score, match.team2.country.code_iso3)
            send_push_message_broadcast(token_list=device_tokens, title=title, message=message)

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
        global total_requests
        try:
            match_id = options['match_id']
            set_live = options['set_live']
        except Exception as e:
            print("Error %s" % e)
            exit(1)
        else:
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
                try:
                    print("Fetching match with ID %s -> external id %s" % (match.id, match.external_id))
                    request_url = API_ENDPOINT_URL + "matches/{}?Authorization={}".format(match.external_id, API_KEY)
                    print(request_url)
                    response = requests.get(request_url, verify=False, timeout=10)
                    total_requests += 1
                    if response.status_code != 200:
                        print("Error status: %s, %s" % (response.status_code, response.json()))
                        if response.status_code == 429:
                            print("API LIMIT EXCEEDED: Total requests: %s" % total_requests)
                            sleep(30) # Slow down
                        continue  # retry
                    match_json = response.json()
                    match = update_match_status_from_json(match, match_json)
                    events_json = match_json['events']
                    update_match_events_from_json(match, events_json)
                except Exception:
                    print("REQUEST ERROR, RETRYING..")
                    sleep(1)
                    continue
                print("API Total requests: %s" % total_requests)
                print("SLEEPING 10 seconds..")
                sleep(10)
        finally:
            print("Total requests: %s" % total_requests)
