import requests
import pandas as pd
import json

# --- CONFIGURATION ---
LEAGUE_ID = "1339044910581452800"
TOTAL_WEEKS = 14 # Regular season length
TOTAL_TEAMS = 10 

def get_sleeper_data():
    users_req = requests.get(f"https://api.sleeper.app/v1/league/{LEAGUE_ID}/users").json()
    users_dict = {u['user_id']: u.get('display_name', 'Unknown') for u in users_req}
    
    rosters_req = requests.get(f"https://api.sleeper.app/v1/league/{LEAGUE_ID}/rosters").json()
    roster_to_team = {}
    team_records = {}
    
    for r in rosters_req:
        roster_id = r['roster_id']
        owner_id = r['owner_id']
        team_name = users_dict.get(owner_id, f"Team {roster_id}")
        roster_to_team[roster_id] = team_name
        
        wins = r['settings']['wins']
        losses = r['settings']['losses']
        ties = r['settings']['ties']
        
        team_records[team_name] = {
            'RealWins': wins + (ties * 0.5),
            'Win %': round(wins / (wins + losses + ties), 2) if (wins+losses+ties) > 0 else 0
        }
    return roster_to_team, team_records

def calculate_advanced_metrics(roster_to_team):
    team_stats = {name: {'AllPlayWins': 0, 'AllPlayGames': 0, 'ExpectedWins': 0, 'MedWins': 0} 
                  for name in roster_to_team.values()}
    
    for week in range(1, TOTAL_WEEKS + 1):
        matchups = requests.get(f"https://api.sleeper.app/v1/league/{LEAGUE_ID}/matchups/{week}").json()
        if not matchups:
            continue
            
        weekly_scores = [{'team': roster_to_team[m['roster_id']], 'points': m['points']} for m in matchups]
        df_week = pd.DataFrame(weekly_scores).sort_values(by='points', ascending=False).reset_index(drop=True)
        median_score = df_week['points'].median()
        
        for index, row in df_week.iterrows():
            team = row['team']
            teams_beaten = (TOTAL_TEAMS - 1) - index
            
            team_stats[team]['AllPlayWins'] += teams_beaten
            team_stats[team]['AllPlayGames'] += (TOTAL_TEAMS - 1)
            team_stats[team]['ExpectedWins'] += teams_beaten / (TOTAL_TEAMS - 1)
            
            if row['points'] > median_score:
                team_stats[team]['MedWins'] += 1
    return team_stats

def generate_bush_rankings():
    print("Fetching live Sleeper Data...")
    roster_to_team, team_records = get_sleeper_data()
    team_stats = calculate_advanced_metrics(roster_to_team)
    
    data = []
    for team in roster_to_team.values():
        rec = team_records[team]
        stat = team_stats[team]
        exp_wins = stat['ExpectedWins']
        real_wins = rec['RealWins']
        
        data.append({
            'Team': team,
            'Win %': rec['Win %'],
            'RecordvsAll Win%': round(stat['AllPlayWins'] / stat['AllPlayGames'], 2) if stat['AllPlayGames'] > 0 else 0,
            'Med Win%': round(stat['MedWins'] / TOTAL_WEEKS, 2),
            'RealWins': real_wins,
            'Expected Wins': round(exp_wins, 2),
            'Wins Above Expected': round(real_wins - exp_wins, 2),
        })
        
    df = pd.DataFrame(data)
    df['WRank'] = df['Expected Wins'].rank(ascending=False)
    
    # UPDATE THESE WEEKLY IF YOU WANT EXTERNAL ROSTER RANKS
    df['FC'] = [1, 3, 2, 4, 6, 8, 10, 5, 9, 7] 
    df['FFW'] = [2, 1, 5, 3, 4, 6, 8, 7, 9, 10]
    df['Sleeper'] = [1, 5, 8, 7, 3, 2, 4, 9, 6, 10]
    
    df['AVG'] = df[['FC', 'FFW', 'Sleeper']].mean(axis=1).round(2)
    df['BUSH'] = ((df['AVG'] + df['WRank']) / 2).round(2)
    df['BUSH RANK'] = df['BUSH'].rank(ascending=True).astype(int)
    
    df = df.sort_values(by='BUSH RANK')
    cols = ['BUSH RANK', 'Team', 'BUSH', 'AVG', 'WRank', 'RealWins', 'Expected Wins', 'RecordvsAll Win%', 'FC', 'FFW', 'Sleeper']
    return df[cols]

# Run script and export to JSON for the website
bush_df = generate_bush_rankings()
bush_df.to_json("data.json", orient="records")
print("Data successfully saved to data.json!")