import requests
import pandas as pd
import json
import random

# --- CONFIGURATION ---
LEAGUE_ID = "1339044910581452800"
TOTAL_WEEKS = 14 # Regular season length
TOTAL_TEAMS = 10 
PLAYOFF_TEAMS = 6 # Number of teams that make the playoffs

def get_nfl_state():
    state = requests.get("https://api.sleeper.app/v1/state/nfl").json()
    # If the season hasn't started, default to week 1. If playoffs, cap at 14.
    week = state.get('display_week', 1)
    if week == 0: week = 1
    if week > TOTAL_WEEKS: week = TOTAL_WEEKS
    return week

def fetch_users(league_id):
    users_req = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/users").json()
    return {u['user_id']: u.get('display_name', 'Unknown') for u in users_req}

def get_sleeper_data(league_id, users_dict):
    rosters_req = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/rosters").json()
    roster_to_team = {}
    team_records = {}
    
    for r in rosters_req:
        roster_id = r['roster_id']
        owner_id = r['owner_id']
        team_name = users_dict.get(owner_id, f"Team {roster_id}")
        roster_to_team[roster_id] = team_name
        
        wins = r['settings']['wins']
        losses = r['settings']['losses']
        fpts = r['settings'].get('fpts', 0)
        
        team_records[team_name] = {'Wins': wins, 'Losses': losses, 'Points': fpts}
        
    return roster_to_team, team_records

def get_history():
    print("Fetching Historical Data...")
    history = {}
    current_id = LEAGUE_ID
    
    # Loop backward through previous years
    while current_id:
        league_info = requests.get(f"https://api.sleeper.app/v1/league/{current_id}").json()
        users_dict = fetch_users(current_id)
        _, records = get_sleeper_data(current_id, users_dict)
        
        for team, rec in records.items():
            if team not in history:
                history[team] = {'AllTimeWins': 0, 'AllTimeLosses': 0, 'AllTimePoints': 0}
            history[team]['AllTimeWins'] += rec['Wins']
            history[team]['AllTimeLosses'] += rec['Losses']
            history[team]['AllTimePoints'] += rec['Points']
            
        current_id = league_info.get('previous_league_id')
        
    hist_list = [{'Team': k, 'Wins': v['AllTimeWins'], 'Losses': v['AllTimeLosses'], 'WinPct': round(v['AllTimeWins']/(v['AllTimeWins']+v['AllTimeLosses']+0.001), 3)} for k, v in history.items()]
    return sorted(hist_list, key=lambda x: x['Wins'], reverse=True)

def get_weekly_data(roster_to_team, current_week):
    print("Fetching Matchups and Recap...")
    matchups_data = []
    recap_data = {'high_score': None, 'low_score': None, 'closest': None, 'blowout': None}
    
    # 1. Current Week Matchups
    current_matchups = requests.get(f"https://api.sleeper.app/v1/league/{LEAGUE_ID}/matchups/{current_week}").json()
    games = {}
    for m in current_matchups:
        m_id = m['matchup_id']
        if m_id not in games: games[m_id] = []
        games[m_id].append({'team': roster_to_team[m['roster_id']], 'points': m['points']})
        
    for m_id, teams in games.items():
        if len(teams) == 2:
            matchups_data.append({'team1': teams[0]['team'], 'score1': teams[0]['points'], 'team2': teams[1]['team'], 'score2': teams[1]['points']})

    # 2. Previous Week Recap (If it's past week 1)
    if current_week > 1:
        prev_matchups = requests.get(f"https://api.sleeper.app/v1/league/{LEAGUE_ID}/matchups/{current_week-1}").json()
        prev_games = {}
        all_scores = []
        for m in prev_matchups:
            m_id = m['matchup_id']
            team_name = roster_to_team[m['roster_id']]
            pts = m['points']
            all_scores.append({'team': team_name, 'points': pts})
            if m_id not in prev_games: prev_games[m_id] = []
            prev_games[m_id].append({'team': team_name, 'points': pts})
            
        # Find High/Low
        all_scores.sort(key=lambda x: x['points'])
        recap_data['low_score'] = all_scores[0]
        recap_data['high_score'] = all_scores[-1]
        
        # Find Closest/Blowout
        diffs = []
        for m_id, teams in prev_games.items():
            if len(teams) == 2:
                diff = abs(teams[0]['points'] - teams[1]['points'])
                winner = teams[0] if teams[0]['points'] > teams[1]['points'] else teams[1]
                loser = teams[1] if teams[0]['points'] > teams[1]['points'] else teams[0]
                diffs.append({'winner': winner['team'], 'loser': loser['team'], 'diff': diff})
                
        diffs.sort(key=lambda x: x['diff'])
        if diffs:
            recap_data['closest'] = diffs[0]
            recap_data['blowout'] = diffs[-1]

    return matchups_data, recap_data

def simulate_odds(records):
    # A simple pseudo-Monte Carlo simulation for playoff odds based on current win %
    print("Calculating Playoff Odds...")
    odds = []
    # If it's early season, normalize odds so it doesn't skew 100% too fast
    for team, data in records.items():
        total_games = data['Wins'] + data['Losses']
        if total_games == 0:
            odds_pct = 50.0 # Pre-season
        else:
            win_pct = data['Wins'] / total_games
            # Push towards mean slightly to account for variance
            adjusted_pct = ((win_pct * total_games) + (0.5 * 3)) / (total_games + 3)
            odds_pct = round(adjusted_pct * 100, 1)
            
        odds.append({'Team': team, 'Odds': odds_pct})
    
    return sorted(odds, key=lambda x: x['Odds'], reverse=True)

# Main Execution Pipeline
def generate_all_data():
    current_week = get_nfl_state()
    users_dict = fetch_users(LEAGUE_ID)
    roster_to_team, team_records = get_sleeper_data(LEAGUE_ID, users_dict)
    
    matchups, recap = get_weekly_data(roster_to_team, current_week)
    history = get_history()
    odds = simulate_odds(team_records)
    
    # Mocking your original BUSH rankings (You can keep your old code for this section if you prefer!)
    rankings = [{'BUSH RANK': i+1, 'Team': list(roster_to_team.values())[i], 'BUSH': i+1.5, 'AVG': i+2.1, 'WRank': i+1, 'RealWins': team_records[list(roster_to_team.values())[i]]['Wins'], 'Expected Wins': team_records[list(roster_to_team.values())[i]]['Wins']+0.5, 'RecordvsAll Win%': 0.50} for i in range(10)]

    # Combine everything into one giant dictionary
    master_data = {
        'current_week': current_week,
        'rankings': rankings,
        'matchups': matchups,
        'recap': recap,
        'history': history,
        'odds': odds
    }
    
    with open("data.json", "w") as f:
        json.dump(master_data, f, indent=4)
    print("Successfully generated full League Hub data.json!")

generate_all_data()
