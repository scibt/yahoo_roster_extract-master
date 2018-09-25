import auth
import csv
import datetime
import sys

csv.register_dialect('ALM', delimiter=',', quoting=csv.QUOTE_ALL)
y = auth.yahoo_session()


def make_league_code(gameid, leagueid):
    return str(gameid) + '.l.' + str(leagueid)

def make_team_code(gameid, leagueid, teamid):
    return str(gameid) + '.l.' + str(leagueid) + '.t.' + str(teamid)

def make_player_code(gameid, playerid):
    return str(gameid) + '.p.' + str(playerid)

def league_data(league_code):
    return "https://fantasysports.yahooapis.com/fantasy/v2/league/" + league_code

def team_data(team_code):
    return "https://fantasysports.yahooapis.com/fantasy/v2/team/" + team_code

def roster_data(team_code, date_wanted):
    return "https://fantasysports.yahooapis.com/fantasy/v2/team/" + team_code + "/roster;date=" + date_wanted.isoformat()

def player_data(league_code, player_code):
    return "https://fantasysports.yahooapis.com/fantasy/v2/league/" + league_code + "/players;player_keys=" + player_code + "/stats"

def stat_desc(x):
    return {
        '1': 'Goals',
        '2': 'Assists',
        '4': 'PlusMinus',
        '5': 'PIM',
        '8': 'PPP',
        '14': 'SOG',
        '19': 'Wins',
        '22': 'GA',
        '23': 'GAA',
        '24': 'SV',
        '25': 'SA',
        '26': 'SavePct',
        '27': 'SHO'
    }[x]

leagues = []
teams = []
rosters = []
Goalies = []
Skaters = []
gameid = sys.argv[1]
leagueid= sys.argv[2
                   ] 

#get league data
league_code = make_league_code(gameid, leagueid)
l = auth.api_query(y, league_data(league_code))
#grab relevant part of dict
this_league = l['fantasy_content']['league']
leagues.append(this_league)
last_day = datetime.datetime.strptime(this_league['end_date'], "%Y-%m-%d")
#go one beyond last day to make sure you get all the roster moves.
last_day = last_day + datetime.timedelta(days=1)

#iterate over teams
num_teams = int(this_league['num_teams'])
for j in range(1, num_teams + 1):
    #get basic team data
    team_code = make_team_code(gameid, leagueid, j)
    t = auth.api_query(y, team_data(team_code))
    #just relevant response
    this_team = t['fantasy_content']['team']
    #include season in dict
    this_team['season'] = this_league['season']
    this_team['logo'] = this_team['team_logos']['team_logo']['url']

    #handle co-managers
    this_manager = this_team['managers']['manager']
    if type(this_manager) == list:
        this_manager = this_manager[0]

    this_team['manager_id'] = this_manager['manager_id']

    this_team['manager_nickname'] = this_manager['nickname']
    if 'guid' in this_manager: manager_guid = this_manager['guid']
    if 'guid' not in this_manager: manager_guid = None
    this_team['manager_guid'] = manager_guid
    if 'email' in this_manager: manager_email = this_manager['email']
    if 'email' not in this_manager: manager_email = None
    this_team['manager_email'] = manager_email
    if "is_owned_by_current_login" not in this_team: this_team["is_owned_by_current_login"] = None
    #drop some keys
    this_team.pop("managers", None)
    this_team.pop("team_logos", None)
    this_team.pop("roster_adds", None)

    print("Team " + str(j) +  " of " + str(num_teams) + " - Name: " + str(this_team['name']))
    teams.append(this_team)

    #get team roster
    r = auth.api_query(y, roster_data(team_code, last_day))
    this_roster = r['fantasy_content']['team']['roster']['players']['player']
    for k in this_roster:
        k['owner_email'] = manager_email
        k['owner_guid'] = manager_guid
        k['team_code'] = team_code
        k['date_captured'] = last_day
        k['season'] = this_league['season']
        k['full_name'] = k['name']['full']
        k['first_name'] = k['name']['ascii_first']
        k['last_name'] = k['name']['ascii_last']
        k['eligible_positions'] = k['eligible_positions']['position']
        k['selected_position'] = k['selected_position']['position']
        k.pop("image_url", None)
        k.pop("is_undroppable", None)
        k.pop("has_player_notes", None)
        k.pop("starting_status", None)
        k.pop("status", None)
        k.pop("has_recent_player_notes", None)
        k.pop("on_disabled_list", None)
        k.pop("is_editable", None)
        k.pop("headshot", None)
        k.pop("name", None)
        k.pop("editorial_player_key", None)
        k.pop("editorial_team_key", None)

        player_code = make_player_code(gameid, k['player_id'])
        ps = auth.api_query(y, player_data(league_code,player_code))
        this_playerstats = ps['fantasy_content']['league']['players']['player']['player_stats']['stats']['stat']

        for pst in this_playerstats:
            colhead = stat_desc(pst['stat_id']) 
            k[colhead] = pst['value']

        k.pop("player_id", None)
        if k['position_type'] == 'G':
            k.pop("position_type", None)
            Goalies.append(k)
        else:
            k.pop("position_type", None)
            Skaters.append(k)

#write data
auth.data_to_csv(
    target_dir="data",
    data_to_write=leagues,
    desired_name='leagues'+this_league['season']
)

auth.data_to_csv(
    target_dir="data",
    data_to_write=teams,
    desired_name='teams'+this_league['season']
)

auth.data_to_csv(
    target_dir="data",
    data_to_write=Goalies,
    desired_name='Goalies'+this_league['season']
)


auth.data_to_csv(
    target_dir="data",
    data_to_write=Skaters,
    desired_name='Skaters'+this_league['season']
)