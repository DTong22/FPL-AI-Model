import pandas as pd
import numpy as np
import requests
import datetime as dt

def map_position(position_id):
    """Map element_type to position name."""
    position_map = {
        1: 'GK',
        2: 'DEF',
        3: 'MID',
        4: 'FWD',
        'GK' : 1,
        'DEF': 2,
        'MID': 3,
        'FWD': 4,
    }
    return position_map.get(position_id, 'Unknown')


def map_team(team_name):
    team_map = {
        "Arsenal": "ARS",
        "Aston Villa": "AVL",
        "Bournemouth": "BOU",
        "Brentford": "BRE",
        "Brighton": "BHA",
        "Chelsea": "CHE",
        "Crystal Palace": "CRY",
        "Everton": "EVE",
        "Fulham": "FUL",
        "Ipswich": "IPS",
        "Leicester": "LEI",
        "Liverpool": "LIV",
        "Man City": "MCI",
        "Man Utd": "MUN",
        "Newcastle": "NEW",
        "Nott'm Forest": "NFO",
        "Southampton": "SOU",
        "Spurs": "TOT",
        "West Ham": "WHU",
        "Wolves": "WOL"
    }
    return team_map.get(team_name, 'Unknown')
    df1['position'] = df1['position'].apply(map_position)


def get_fpl_data():
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    response = requests.get(url)
    return response.json()

def get_team_data(fpl_data):
    teams_df = pd.DataFrame(fpl_data['teams'])
    return teams_df[['name', 'id']]

def preprocess_elements(fpl_data):
    df = pd.DataFrame(fpl_data['elements'])
    df1 = df[['element_type', 'first_name', 'now_cost', 'second_name', 'team', 
        'transfers_in_event', 'transfers_out_event', 'id',
        'chance_of_playing_next_round', 'news', 'web_name', 'code']].copy()
    df1['chance_of_playing_next_round'] = df1['chance_of_playing_next_round'].fillna(value=100)
    df1.rename(columns={'element_type':'position', 'now_cost':'value', 'transfers_in_event':'transfers_in',
                            'transfers_out_event':'transfers_out'}, inplace=True)
    df1['name'] = df1['first_name'] + ' ' + df1['second_name']
    df1.drop(columns=['first_name', 'second_name'], inplace=True)
    df1['position'] = df1['position'].apply(map_position)
    return df1

def get_player_history(player_df):
    player_history = []
    player_fixtures = []
    for player_id in player_df['id']:
        url = f"https://fantasy.premierleague.com/api/element-summary/{player_id}/"
        response = requests.get(url)
        if response.status_code == 200:
            history_data = response.json()['history']
            fixtures_data = response.json()['fixtures']
            for fixture in fixtures_data:
                fixture['id'] = player_id
            player_history.extend(history_data)
            player_fixtures.extend(fixtures_data)

    return pd.DataFrame(player_history), pd.DataFrame(player_fixtures)

def preprocess_history(history_df, player_df, teams_df):
    last_round = history_df[history_df['round'] == history_df['round'].max()]
    last_round = last_round.copy()
    slim_player_df = player_df[['position', 'id', 'web_name', 'name', 'team', 'code']]
    df2 = last_round.merge(slim_player_df, left_on='element', right_on='id', how='left')
    df2.drop(columns=['id'], inplace=True)
    df2 = df2.merge(teams_df, left_on='team', right_on='id', how='left')
    df2.drop(columns=['id', 'team'], inplace=True)
    df2.rename(columns={'name_y':'team', 'name_x':'name'}, inplace=True)
    df2['season'] = '2024-25'
    df2['GW'] = df2['round']
    
    df3 = df2.merge(teams_df, left_on='opponent_team', right_on='id')
    df3.rename(columns={'name_x':'name', 'name_y':'opp_team_name'}, inplace=True)
    df3.drop(columns='id', inplace=True)
    df3.sort_values('GW', inplace=True)
    return df3

def preprocess_fixtures(fixtures_df, player_df, teams_df):
    fixtures_df.sort_values('event', inplace=True)
    fixtures_next6 = fixtures_df[fixtures_df['event'] < fixtures_df['event'].min() + 6]    
    fixtures_next6 = fixtures_next6.copy()
    fixtures_next6.rename(columns={'event': 'round', 'is_home': 'was_home'}, inplace=True)
    fixtures_next6['opponent_team'] = np.where(fixtures_next6['was_home'], fixtures_next6['team_a'], fixtures_next6['team_h'])
    fixtures_slim = fixtures_next6[['id','round', 'kickoff_time', 'was_home', 'opponent_team']].copy()
    merged_teams = player_df.merge(fixtures_slim, on='id', how='left')
    merged_team_name = merged_teams.merge(teams_df, left_on='team', right_on='id', how='left')
    merged_team_names = merged_team_name.merge(teams_df, left_on='opponent_team', right_on='id', how='left')
    merged_team_names.drop(columns=['team', 'id', 'id_y'], inplace=True)
    merged_team_names.rename(columns={'name':'opp_team_name', 'name_y':'team', 'name_x':'name', 'id_x':'element'}, inplace=True)
    merged_team_names['season'] = '2024-25'
    return merged_team_names