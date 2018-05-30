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


def get_match_status(api_match_status, timer):
    if api_match_status == "LIVE":
        return Match.PLAYING_FT
    elif api_match_status == "FT":
        return Match.FINISHED
    elif api_match_status == "HT":
        return Match.HALFTIME
    elif api_match_status == "NS":
        return Match.NOT_STARTED
    else:
        return Match.PLAYING_FT  # ToDo unify playing status


def update_match_status_from_json(match, match_json):
    print("Updating score of match %s .." % match)
    # Team 1 is always local and Team 2 is always visitor
    match_minute = match_json['time']['minute']
    match.status = get_match_status(api_match_status=match_json['time']['status'], timer=match_minute)
    if match_minute is not None and match_minute != "":
        match.minutes = match_minute  # In extra time a plus sign appears
    match.team1_score = match_json['scores']['localteam_score']
    match.team2_score = match_json['scores']['visitorteam_score']
    match.save()
    print("Updating score of match %s ..DONE" % match)
    return match

def update_match_statistics_from_json(match, stats_json):
    print("Updating stats of match %s .." % match)
    # Team 1 is always local and Team 2 is always visitor
    try:
        team1 = match.team1
        team2 = match.team2
        for stat in stats_json:
            if stat['team_id'] == int(team1.external_id):
                team = team1
            else: # Team2 is the only remaining option
                team = team2
            print("Updating stats for team %s .." % team)
            try: # Create or update stats
                team_stats = MatchStats.objects.get(match=match, team=team)
            except MatchStats.DoesNotExist:
                team_stats = MatchStats(match=match, team=team)
            finally:
                team_stats.possession = stat['possessiontime'] if stat['possessiontime'] is not None else 50
                team_stats.passes = stat['passes']['total'] if stat['passes']['total'] is not None else 0
                team_stats.passes_accuracy = stat['passes']['percentage'] if stat['passes']['percentage'] is not None else 100
                team_stats.shots_total = stat['shots']['total'] if stat['shots']['total'] is not None else 0
                team_stats.shots_ongoal = stat['shots']['ongoal'] if stat['shots']['ongoal'] is not None else 0
                if int(stat['shots']['total']) > 0:
                    shots_accuracy = round((float(stat['shots']['ongoal']) / float(stat['shots']['total'])) * 100.0)
                else:
                    shots_accuracy = 100
                team_stats.shots_accuracy = shots_accuracy
                team_stats.dangerous_attacks = stat['attacks']['dangerous_attacks'] if stat['attacks']['dangerous_attacks'] is not None else 0
                team_stats.courner_kicks = stat['corners'] if stat['corners'] is not None else 0
                team_stats.free_kicks = stat['free_kick'] if stat['free_kick'] is not None else 0
                team_stats.yellow_cards = stat['yellowcards'] if stat['yellowcards'] is not None else 0
                team_stats.red_cards = stat['redcards'] if stat['redcards'] is not None else 0
                team_stats.substitutions = stat['substitutions'] if stat['substitutions'] is not None else 0
                team_stats.fouls = stat['fouls'] if stat['fouls'] is not None else 0
                team_stats.save()
    except Exception as e:
        print("ERROR UPDATING MATCH STATS: %s" % e)
    else:
        print("Updating stats of match %s ..DONE" % match)
    finally:
        return match


def get_event_type(api_event_type):
    if api_event_type == "goal":
        return "goal"
    elif api_event_type == "substitution":
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
        message = "{} vs {}".format(match.team1.country.code_iso3.upper(), match.team2.country.code_iso3.upper())
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
        print("Match %s ..FINISHED." % match)
        return

    # Process events obtained from the API
    new_events_json = [ev for ev in events_json if str(ev['id']) not in current_match_event_ids]
    for event_json in new_events_json:
        if event_json['player_id'] == "" and event_json['player_name'] == "":
            print("API ERROR: Player data missing, retry later..")
            return # Abort and retry in some seconds, results are not complete yet
        # First get event type
        event_type = get_event_type(api_event_type=event_json['type'])
        # Notify goals ASAP, then continue processign event details
        if event_type == 'goal':
            title = "Goal! {}".format(new_event.team.country.code_iso3.upper())
            message = "{} {} - {} {}".format(match.team1.country.code_iso3.upper(), match.team1_score,
                                             match.team2_score, match.team2.country.code_iso3.upper())
            send_push_message_broadcast(token_list=device_tokens, title=title, message=message)

        team = match.team2 if event_json['team_id'] == match.team2.external_id else match.team1
        new_event = MatchEvent()
        new_event.external_id = event_json['id']
        new_event.match = match
        new_event.team = team
        new_event.event_type = event_type
        event_minute = event_json['minute']
        new_event.minute = int(event_minute) if event_minute is not None else 0
        event_extra_minute = event_json['extra_minute']
        new_event.extra_minute = int(event_extra_minute) if event_extra_minute is not None else 0
        try:
            player = Player.objects.get(external_id=event_json['player_id'])
        except Exception:
            player_fullname = event_json['player_name']
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
        new_event.description2 = event_json["related_player_name"] if new_event.event_type == 'player_change' else ""
        new_event.save()
        print("New event saved:  %s" % new_event)

    print("Updating events of match %s ..DONE" % match)


def update_match_lineups_from_json(match, lineups_json):
    print("Updating lineups of match %s .." % match)
    # Team 1 is always local and Team 2 is always visitor
    team1_id = int(match.team1.external_id)
    team2_id = int(match.team2.external_id)
    team1_players = [('%3s' % p['number']) + ('. %s' % p['player_name']) for p in lineups_json if p['team_id'] == team1_id]
    team2_players = [('%3s' % p['number']) + ('. %s' % p['player_name']) for p in lineups_json if p['team_id'] == team2_id]
    match.team1_lineup = team1_players
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
        parser.add_argument('--set-live', dest='set_live', required=False, action='store_true')
        parser.add_argument('--old-match', dest='is_old_match', required=False, action='store_true')


    def handle(self, *args, **options):
        global total_requests
        try:
            match_id = options['match_id']
            set_live = options['set_live']
            is_old_match = options['is_old_match']
        except Exception as e:
            print("Error %s" % e)
            exit(1)
        else:
            # Get match data and keep updating
            while True:
                # Get current live matches from API
                print("Fetching single match with ID %s" % (match_id))
                if is_old_match:
                    request_url = API_ENDPOINT_URL + "fixtures/{}?api_token={}&include=localTeam,visitorTeam,venue,lineup,events,stats,group,stage".format(
                        match_id, API_KEY)
                else:
                    request_url = API_ENDPOINT_URL + "livescores/?api_token={}&include=localTeam,visitorTeam,venue,lineup,events,stats,group,stage".format(API_KEY)
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
                        match = Match.objects.get(external_id=ext_match_id)
                    except Match.DoesNotExist:
                        print("Match with ID %s not found (Skipped)" % match_id)
                        continue

                    if set_live:
                        match.is_live = True
                        match.save()

                    try: # Update all match info, events and stats
                        match = update_match_status_from_json(match, match_json)
                        events_json = match_json['events']['data']
                        update_match_events_from_json(match, events_json)
                        stats_json = match_json['stats']['data']
                        update_match_statistics_from_json(match, stats_json)
                        lineups_json = match_json['lineup']['data']
                        update_match_lineups_from_json(match, lineups_json)
                    except Exception as e:
                        print("ERROR UPDATING MATCH: %s" % e)
                        sleep(1)
                        continue
                # Start again in a few seconds
                print("API Total requests: %s" % total_requests)
                print("SLEEPING 5 seconds..")
                sleep(5)
        finally:
            print("Total requests: %s" % total_requests)
