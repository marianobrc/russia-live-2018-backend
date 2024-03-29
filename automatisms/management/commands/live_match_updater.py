import json
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


def get_match_status(api_match_scores, api_match_status):
    if api_match_status == "LIVE" or api_match_status == "BREAK":
        return Match.PLAYING_FT
    elif api_match_status == "ET":
        return Match.EXTRA_TIME
    elif api_match_status == "PEN_LIVE":
        return Match.PENALTIES
    elif api_match_status == "FT":
        # Check if scores are equal, then the match haven't finished
        if api_match_scores['localteam_score'] != api_match_scores['visitorteam_score']:
            return Match.FINISHED
        else:
            return Match.PLAYING_FT
    elif api_match_status == "AET":
        # Check if scores are equal, then the match haven't finished
        if api_match_scores['localteam_score'] != api_match_scores['visitorteam_score']:
            return Match.FINISHED
        else:
            return Match.EXTRA_TIME # Don't send the finish event until after penalties
    elif api_match_status == "FT_PEN":
        return Match.FINISHED # When penalties finished, then the match finished
    elif api_match_status == "HT":
        return Match.HALFTIME
    elif api_match_status == "NS":
        return Match.NOT_STARTED
    else:
        return Match.PLAYING_FT  # ToDo unify playing status


def update_match_status_from_json(match, match_json):
    print("Updating score of match %s .." % match)
    # Team 1 is always local and Team 2 is always visitor
    match_minute_json = match_json['time']['minute']
    if match_minute_json is not None and match_minute_json != "":
        match_minute = int(match_minute_json)
        if match_json['time']['extra_minute'] is not None:
            match_minute += int(match_json['time']['extra_minute'])
        match.minutes = match_minute  # In extra time a plus sign appears
    match.status = get_match_status(api_match_scores=match_json['scores'], api_match_status=match_json['time']['status'])
    if match.status == Match.PENALTIES and not match.is_penalty_definition:
        match.is_penalty_definition = True
    if match.is_penalty_definition:
        match.team1_penalties_score =  match_json['scores']['localteam_pen_score']
        match.team2_penalties_score = match_json['scores']['visitorteam_pen_score']
    elif match.status == Match.PLAYING_FT or Match.EXTRA_TIME: # During the game
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
                team_stats.possession = stat['possessiontime'] if stat['possessiontime'] is not None else 0
                if stat['passes'] is not None:
                    team_stats.passes = stat['passes']['total'] if stat['passes']['total'] is not None else 0
                    team_stats.passes_accuracy = stat['passes']['percentage'] if stat['passes']['percentage'] is not None else 0
                if stat['shots'] is not None:
                    team_stats.shots_total = stat['shots']['total'] if stat['shots']['total'] is not None else 0
                    team_stats.shots_ongoal = stat['shots']['ongoal'] if stat['shots']['ongoal'] is not None else 0
                    if int(stat['shots']['total']) > 0:
                        shots_accuracy = round((float(stat['shots']['ongoal']) / float(stat['shots']['total'])) * 100.0)
                    else:
                        shots_accuracy = 0
                    team_stats.shots_accuracy = shots_accuracy
                if stat['attacks'] is not None:
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
    if api_event_type == "goal" or api_event_type == "penalty" or api_event_type == "own-goal" or api_event_type == "own_goal":
        return "goal"
    elif api_event_type == "pen_shootout_goal":
        return "penalty_goal"
    elif api_event_type == "missed_penalty" or api_event_type == "pen_shootout_miss":
        return "penalty_missed"
    elif api_event_type == "substitution":
        return "player_change"
    elif api_event_type == "yellowcard":
        return "yellow_card"
    elif api_event_type == "redcard":
        return "red_card"
    elif api_event_type == "yellowred":
        return "yellow_red_card"
    else:
        return "match_generic"

# Sanity checks
def verify_event_data_consistency(event_json):

    try: # Get event ID that shouldn't be missing ever
        event_id = event_json['id']
    except Exception as e:
        print("[verify_event_data_consistency]> ERROR getting event ID: \nEvent: %s \nError: %s" % (event_json, e))
        return False

    # Validate event ID is valid
    if event_id is None:
        print("[verify_event_data_consistency]> ERROR -> Event ID is None!")
        return False

    try: # Get event type
        event_type = event_json['type']
    except Exception as e:
        print("[verify_event_data_consistency]> ERROR getting event type: \nEvent: %s \nError: %s" % (event_json, e))
        return False

    # Validate event type
    if event_type is None:
        print("[verify_event_data_consistency]> ERROR -> Event type is None!")
        return False

    # Get team id
    try: # Get event type
        team_id = event_json['team_id']
    except Exception as e:
        print("[verify_event_data_consistency]> ERROR getting team_id: \nEvent: %s \nError: %s" % (event_json, e))
        return False

    # Validate team id
    if team_id is None:
        print("[verify_event_data_consistency]> ERROR -> Team ID is None!")
        return False

    # All validations passed
    return True






def update_match_events_from_json(match, events_json, is_simulation=False, sim_time=0):
    print("Updating events of match %s .." % match)
    device_tokens = [t.token for t in PushToken.objects.filter(notifications_on=True, active=True)]
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
    # elif match.status == Match.HALFTIME and MatchEvent.objects.filter(match=match, event_type='half_time').count() == 0:
    #     new_event = MatchEvent()
    #     new_event.external_id = '-1'
    #     new_event.match = match
    #     new_event.team = match.team2
    #     new_event.event_type = 'half_time'
    #     new_event.minute = 45 # ToDo: check how to handle minutes in half time
    #     new_event.extra_minute = 0
    #     new_event.description = "Half Time"
    #     new_event.description2 = ""
    #     new_event.save()
    #     title = "Half Time"
    #     message = "{} {} - {} {}".format(match.team1.country.code_iso3, match.team1_score,
    #                                      match.team2_score, match.team2.country.code_iso3)
        #send_push_message_broadcast(token_list=device_tokens, title=title, message=message)
        #return # Don't update more events during half-time
    elif match.status == Match.EXTRA_TIME and MatchEvent.objects.filter(
            match=match,
            event_type='extra_time'
    ).count() == 0:
        new_event = MatchEvent()
        new_event.external_id = '-1'
        new_event.match = match
        new_event.team = match.team2
        new_event.event_type = 'extra_time'
        new_event.minute = 98
        new_event.extra_minute = 0
        new_event.description = "Extra time started"
        new_event.description2 = ""
        new_event.save()
        title = "Extra Time"
        message = "{} - {}".format(match.team1.country.code_iso3.upper(), match.team2.country.code_iso3.upper())
        send_push_message_broadcast(token_list=device_tokens, title=title, message=message)
        new_event.is_notified = True
        new_event.save()
        print("Match %s ..Extra time definition." % match)
        return
    elif match.status == Match.PENALTIES and MatchEvent.objects.filter(
            match=match,
            event_type='penalties_definition'
    ).count() == 0:
        new_event = MatchEvent()
        new_event.external_id = '-1'
        new_event.match = match
        new_event.team = match.team2
        new_event.event_type = 'penalties_definition'
        new_event.minute = 120
        new_event.extra_minute = 0
        new_event.description = ""
        new_event.description2 = ""
        new_event.save()
        title = "Penalties Definition"
        message = "{} - {}".format(match.team1.country.code_iso3.upper(), match.team2.country.code_iso3.upper())
        send_push_message_broadcast(token_list=device_tokens, title=title, message=message)
        new_event.is_notified = True
        new_event.save()
        print("Match %s ..Penalties Started." % match)
        return
    elif match.status == Match.FINISHED and MatchEvent.objects.filter(match=match, event_type='match_finished').count() == 0:
        new_event = MatchEvent()
        new_event.external_id = '-1'
        new_event.match = match
        new_event.team = match.team2
        new_event.event_type = 'match_finished'
        new_event.minute = 200  # ToDo: check how to handle minutes in half time
        new_event.extra_minute = 0
        new_event.description = "Finished"  # ToDo check when to use it
        new_event.description2 = ""
        new_event.save()
        title = "Match finished"
        if match.is_penalty_definition:
            message = "{} {}({}) - ({}){} {}".format(
                match.team1.country.code_iso3.upper(), match.team1_score, match.team1_penalties_score,
                match.team2_penalties_score, match.team2_score, match.team2.country.code_iso3.upper()
            )
        else:
            message = "{} {} - {} {}".format(match.team1.country.code_iso3.upper(), match.team1_score,
                                             match.team2_score, match.team2.country.code_iso3.upper())
        send_push_message_broadcast(token_list=device_tokens, title=title, message=message)
        new_event.is_notified = True
        new_event.save()
        print("Match %s ..FINISHED." % match)
        return

    # Process NEW events obtained from the API
    new_events_json = [ev for ev in events_json if str(ev['id']) not in current_match_event_ids]
    new_events_json = sorted(new_events_json, key=lambda event: event['minute'])
    for event_json in new_events_json:
        try:
            # IMPORTANT: Checks data sanity, cause the api use to return wrong or uncompleted data
            if not verify_event_data_consistency(event_json):
                print("ERROR: EVENT DATA INCONSISTENCY (Skipped):  %s" % event_json)
                continue

            # LOG NEW EVENT FOR DEBUGG
            print("NEW EVENT REVEIVED:\n %s" % event_json)

            # First get event type
            event_type = get_event_type(api_event_type=event_json['type'])

            # Validate team
            if event_json['team_id'] == match.team2.external_id:
                team = match.team2
            elif event_json['team_id'] == match.team1.external_id:
                team = match.team1
            else:
                print("ERROR: EVENT TEAM DOESN'T MATCH, (Skipped):\n  %s" % event_json)
                continue


            new_event = MatchEvent()
            new_event.external_id = event_json['id']
            new_event.match = match
            new_event.team = team
            new_event.event_type = event_type

            # Notify goals ASAP, then continue processign event details
            if (event_type == 'goal') and (match.status != Match.FINISHED or is_simulation):
                team_scores = event_json['result']
                team1_score = team_scores[0]
                team2_score = team_scores[2]
                title = "Goal! {}".format(new_event.team.country.code_iso3.upper())
                message = "{} {} - {} {}".format(match.team1.country.code_iso3.upper(), team1_score,
                                                 team2_score, match.team2.country.code_iso3.upper())
                print(">>>>>>>>>> SENDING GOAL NOTIFICATION FOR NEW EVENT: %s %s" % (title, message))
                send_push_message_broadcast(token_list=device_tokens, title=title, message=message)
                new_event.is_notified = True

            event_minute = event_json['minute']
            new_event.minute = int(event_minute) if event_minute is not None else 0
            if event_type == 'penalty_goal' or event_type == 'penalty_missed':
                new_event.minute += 120
            if event_json['extra_minute'] is not None:
                new_event.minute += int(event_json['extra_minute'])
            new_event.extra_minute = 0 # deprecated
            try:
                player = Player.objects.get(external_id=event_json['player_id'])
            except Exception:
                if event_json['player_name'] is not None and event_json['player_name'] != "": # Is a new player
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
                    player_id = event_json['player_id']
                    if player_id is None:
                        player_id = "no_player_id"
                    new_player = Player.objects.create(
                        external_id=player_id,
                        team=team,
                        common_name=shortened_name,
                        first_name=first_name,
                        last_name=surname,
                        nationality=None,  # ToDo map to countries
                        position="",
                    )
                    player = new_player
                else: # No player info yet, will be updated later
                    player = None
            new_event.player = player
            new_event.description = "" # ToDo check when to use it
            if new_event.event_type == 'player_change':
                try:
                    player_out_fullname = event_json["related_player_name"]
                    player_out_name = player_out_fullname
                    if len(player_out_name) > 12:
                        player_splited_fullname = player_out_fullname.split()
                        player_out_name = player_splited_fullname[0][0] + ". " + ' '.join(player_splited_fullname[1:])
                        if len(player_out_name) > 12:
                            player_out_name = player_out_name[: 11] + ".."
                except Exception as e:
                    player_out_name = player_splited_fullname[: 11] + ".."
                finally:
                    new_event.description2 = player_out_name
            elif event_type == 'penalty_goal':
                new_event.description2 = "Penalty Goal."
            elif event_type == 'penalty_missed':
                new_event.description2 = "Penalty Missed."
            else:
                new_event.description2 = ""
            new_event.save()
            print("New event saved:  %s" % new_event)
            if is_simulation:
                sleep(int(sim_time))
        except Exception as e:
            print("ERROR creating event (skipped): %s " % e)
            continue

    # Now update old events
    old_events_json = [ev for ev in events_json if str(ev['id']) in current_match_event_ids]
    old_events_json = sorted(old_events_json, key=lambda event: event['minute'])
    for event_json in old_events_json:
        try:
            print("UPDATE EVENT REVEIVED:\n %s" % event_json)
            try:
                old_event = MatchEvent.objects.get(external_id=event_json['id'])
            except Exception as e:
                print("Error updating event %s (skipped): \n%s" % (event_json, e))
                continue
            else:
                # Consistency checks
                if not verify_event_data_consistency(event_json):
                    print("UPDATE ERROR: EVENT DATA INCONSISTENCY (Skipped):  %s" % event_json)
                    continue

                # Update event type if has changed
                new_event_type = get_event_type(api_event_type=event_json['type'])
                if event_json['type'] is not None and new_event_type != old_event.event_type:
                    print("Old event type updated [%s] -> %s" % (old_event, new_event_type))
                    old_event.event_type =  new_event_type
                    old_event.save()
                    # Notify goals -> WORKAROUND FOR API ISSUE WITH PENALTIES
                    if (new_event_type == 'goal') and (match.status != Match.FINISHED or is_simulation):
                        if not old_event.is_notified: # Avoid duplicate notifications
                            team_scores = event_json['result']
                            team1_score = team_scores[0]
                            team2_score = team_scores[2]
                            title = "Goal! {}".format(old_event.team.country.code_iso3.upper())
                            message = "{} {} - {} {}".format(match.team1.country.code_iso3.upper(), team1_score,
                                                             team2_score, match.team2.country.code_iso3.upper())
                            print(">>>>>>>>>> SENDING GOAL NOTIFICATION FOR OLD EVENT: %s %s" % (title, message))
                            send_push_message_broadcast(token_list=device_tokens, title=title, message=message)
                            old_event.is_notified = True
                            old_event.save()
                        else:
                            print(">>>>>>>>>> WARNING: Double notifiation attempted and SKIPPED for event %s" % old_event)

                # Update event time if has changed
                event_minute = event_json['minute']
                new_time = int(event_minute)
                if event_json['extra_minute'] is not None:
                    new_time += int(event_json['extra_minute'])
                if new_event_type == 'penalty_goal' or new_event_type == 'penalty_missed':
                    new_time += 120
                if event_minute is not None and new_time != int(old_event.minute):
                    print("Old event time updated [%s] -> %s" % (old_event, event_minute))
                    old_event.minute = int(event_minute)
                    old_event.extra_minute = 0  # deprecated
                    old_event.save()

                # Update team if has changed
                if old_event.team is not None and event_json['team_id'] is not None and str(old_event.team.external_id) != str(event_json['team_id']):
                    print("Old event team updated [%s] -> %s" % (old_event, event_json['team_id']))
                    if event_json['team_id'] == match.team2.external_id:
                        new_team = match.team2
                        old_event.team = new_team
                        old_event.save()
                    elif event_json['team_id'] == match.team1.external_id:
                        new_team = match.team1
                        old_event.team = new_team
                        old_event.save()
                    else:
                        print("ERROR: EVENT TEAM DOESN'T MATCH, (Skipped):\n  %s" % event_json)
                        pass


                # The player is updated if the id exists and if is diferent from current
                if (old_event.player is None and event_json['player_id'] is not None) or\
                        (old_event.player is not None and event_json['player_id'] is not None and str(old_event.player.external_id) != str(event_json['player_id']) ):
                    try:
                        player = Player.objects.get(external_id=event_json['player_id'])
                    except Exception:
                        if event_json['player_name'] is not None:  # Is a new player
                            print("Creating missing player: %s" % event_json['player_name'] )
                            # Make player with avalilable data
                            first_name = event_json['firstname']
                            if first_name is None or first_name == "":
                                first_name = event_json['common_name'].split()[0]
                            surname = event_json['lastname']
                            if surname is None or surname == "":
                                surname = event_json['common_name'].split()[1]
                            common_name = event_json['common_name']
                            if len(common_name) > 14:  # Shorten names
                                very_first_name = first_name.split(' ')[0][0]  # First letter of first name
                                common_name = very_first_name + ". " + surname  # J. Masscheranno
                                if len(common_name) > 14:  # Use only surname
                                    common_name = surname  # Masscheranno
                                if len(common_name) > 14:  # Abreviate
                                    common_name = common_name[:12] + ".."  # Masscheran..
                            # Create the new player
                            player_id = event_json['player_id']
                            if player_id is None:
                                player_id = "unknown_player"
                            new_player = Player.objects.create(
                                external_id=player_id,
                                team=team,
                                common_name=common_name,
                                first_name=first_name,
                                last_name=surname,
                                nationality=team.country,  # All players must be from the team's country in this worldcup
                                position=event_json['position_id'],
                            )
                            old_event.player = new_player
                            print("Old event NEW player updated -> %s" % old_event)
                    else: # No exception, then player was found
                        old_event.player = player
                        print("Old event player updated [%s] -> %s" % (old_event, old_event.player))

                # Update description
                old_event.description = ""  # ToDo check when to use it
                if old_event.event_type == 'player_change':
                    try:
                        player_out_fullname = event_json["related_player_name"]
                        player_out_name = player_out_fullname
                        if len(player_out_name) > 12:
                            player_splited_fullname = player_out_fullname.split()
                            player_out_name = player_splited_fullname[0][0] + ". " + ' '.join(
                                player_splited_fullname[1:])
                            if len(player_out_name) > 12:
                                player_out_name = player_out_name[: 11] + ".."
                    except Exception as e:
                        player_out_name = player_splited_fullname[: 11] + ".."
                    finally:
                        old_event.description2 = player_out_name
                elif old_event.event_type == 'penalty_goal':
                    old_event.description2 = "Penalty Goal."
                elif old_event.event_type == 'penalty_missed':
                    old_event.description2 = "Penalty Missed."
                else:
                    old_event.description2 = ""

                # Finally save event
                old_event.save()

        except Exception as e:
            print("ERROR Updating event (skipped): %s " % e)
            continue

    print("Updating events of match %s ..DONE" % match)


def update_match_lineups_from_json(match, lineups_json):
    print("Updating lineups of match %s .." % match)
    # Team 1 is always local and Team 2 is always visitor
    team1_id = int(match.team1.external_id)
    team2_id = int(match.team2.external_id)
    team1_players = [('%4s' % p['number']) + ('. %s' % p['player_name']) for p in lineups_json if p['team_id'] == team1_id]
    team2_players = [('%4s' % p['number']) + ('. %s' % p['player_name']) for p in lineups_json if p['team_id'] == team2_id]
    if len(team1_players) > 0:
        match.team1_lineup = team1_players
    if len(team2_players) > 0:
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
        parser.add_argument('--simulate', dest='is_simulation', required=False, action='store_true', default=False)
        parser.add_argument('--from-file', dest='json_file', required=False, )
        parser.add_argument('--sim-time', dest='simulation_delay', required=False, )


    def handle(self, *args, **options):
        global total_requests
        try:
            match_id = options['match_id']
            set_live = options['set_live']
            is_old_match = options['is_old_match']
            is_simulation = options['is_simulation']
            json_file = options['json_file']
            simulation_delay = options['simulation_delay']
        except Exception as e:
            print("Error %s" % e)
            exit(1)
        else:
            # Get match data and keep updating
            while True:
                # Get current live matches from API
                print("Fetching single match with ID %s" % (match_id))
                if is_simulation:
                    f = open(json_file, 'r')
                    live_matches_json = json.load(f)['data']
                else: # real match
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
                        if match_id != 'all' and int(ext_match_id) != int(match_id):
                            print("Match with ID %s skipped.." % ext_match_id)
                            continue
                        match = Match.objects.get(external_id=ext_match_id)
                    except Match.DoesNotExist:
                        print("Match with ID %s not found (Skipped)" % ext_match_id)
                        continue
                    except Exception as e:
                        print("Error updating Match with ID %s (Skipped): \n %s" % (ext_match_id, e))
                        continue

                    if set_live:
                        match.is_live = True
                        match.save()

                    try: # Update all match info, events and stats
                        match = update_match_status_from_json(match, match_json)
                        events_json = match_json['events']['data']
                        update_match_events_from_json(match, events_json, is_simulation, simulation_delay)
                        stats_json = match_json['stats']['data']
                        update_match_statistics_from_json(match, stats_json)
                        #lineups_json = match_json['lineup']['data']
                        #update_match_lineups_from_json(match, lineups_json)
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
