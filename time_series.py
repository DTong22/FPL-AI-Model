import pandas as pd
import numpy as np
import datetime as dt

def concat_fixtures(history, fixtures):
    return pd.concat([history, fixtures]).reset_index(drop=True)

def create_features(master):
    df = master.copy()
    df['position_code'] = df['position'].apply(map_position)
    
    df["value"] = df["value"]/10
    df.drop(columns=['xP', 'expected_assists', 'expected_goal_involvements', 
                     'expected_goals','expected_goals_conceded', 
                     'starts', 'own_goals'], inplace=True)
    
    # Code features (may need to binary)
    df['team_codes'] = df['team'].astype('category').cat.codes
    df['opp_codes']  = df['opp_team_name'].astype('category').cat.codes
    
    df['conceded_opp'] = np.where(df['was_home'], df['team_h_score'], df['team_a_score'])
    df['scored_opp'] = np.where(df['was_home'], df['team_a_score'], df['team_h_score'])
    df['scored_team'] = np.where(df['was_home'], df['team_h_score'], df['team_a_score'])
    df['conceded_team'] = np.where(df['was_home'], df['team_a_score'], df['team_h_score'])
    
    # Rank features
    df['transfers_in_rank'] = df.groupby(['season', 'round'])['transfers_in'].rank(ascending=True)
    df['transfers_out_rank'] = df.groupby(['season', 'round'])['transfers_out'].rank(ascending=True)
    df['selected_rank'] = df.groupby(['season', 'round'])['selected'].rank(ascending=True)
    
    # Split the 'time' column into 'date' and 'time' columns
    df[['date', 'time']] = df['kickoff_time'].str.split('T', expand=True)
    df['time'] = df['time'].str[:-1]
    df['time'] = pd.to_datetime(df['time'], format='%H:%M:%S')
    df['time'] = df['time'].dt.hour + df['time'].dt.minute / 60
    return df.sort_values(['date'])

def moving_average(df, columns_to_average, window_size=6):
    for col in columns_to_average:
        df[col + '_avg'] = df.groupby('code')[col].transform(lambda x: x.rolling(window=window_size).mean().shift(1))
    return df

def ewma(df, columns_to_average, group_by, span=6):
    for col in columns_to_average:
        df[col + '_ewma'] = df.groupby(group_by)[col].transform(lambda x: x.ewm(span=span, adjust=True).mean().shift(1))
    return df

def player_moving_average(df):
    columns_to_average = [
            'total_points',
            'goals_scored','assists',
            'saves','clean_sheets','goals_conceded', 
            'bonus', 'bps', 
            'ict_index', 'influence', 'creativity', 'threat',
            'minutes',
            'yellow_cards', 'red_cards',
            'penalties_missed','penalties_saved', 
            'selected','transfers_balance', 'transfers_in', 'transfers_out']

    df = ewma(df, columns_to_average, 'code')
    return df

def team_moving_average(df):
    teams = df[["date","team", "scored_team", "conceded_team", "opp_team_name", "scored_opp", "conceded_opp"]].copy()
    no_dupes = teams.drop_duplicates(ignore_index=True)
    no_dupes = no_dupes.copy()
    team_columns = ['scored_team', 'conceded_team']
    
    no_dupes1 = ewma(no_dupes, team_columns, 'team', span=10)
    
    opp_columns = ['scored_opp', 'conceded_opp']
    
    no_dupes2 = ewma(no_dupes1, opp_columns, 'opp_team_name', span=10)
    
    slim_no_dupes = no_dupes2[['date', 'opp_team_name', 'scored_team_ewma', 'conceded_team_ewma', 'scored_opp_ewma', 'conceded_opp_ewma']]
    merged_df = df.merge(slim_no_dupes, on=['date', 'opp_team_name'])
    return merged_df

def fill_fixtures(df, fixtures):
    df = df[df['season']== '2024-25']
    
    df = df.copy()
    # Forward fill selected to fixtures
    df[['selected', 'selected_rank']] = df.groupby('code')[['selected', 'selected_rank']].fillna(method='ffill')
    
    # Select fixtures only
    df = df[(df['round'] > fixtures['round'].min()-1) & (df['round'] < fixtures['round'].min()+6)] #next 6 weeks
    
    # Fill team data with nan
    cols_to_fill = ['scored_team_ewma','conceded_team_ewma', 'scored_opp_ewma', 'conceded_opp_ewma']
    condition = df['round'] > fixtures['round'].min()
    df.loc[condition, cols_to_fill] = np.nan
    
    # Forward fill team data
    df = df.sort_values('date')
    team_columns= ['scored_team_ewma','conceded_team_ewma']
    df[team_columns] = df.groupby('team')[team_columns].fillna(method='ffill')
    
    # Forward fill opposition data
    df = df.sort_values('date')
    opp_columns = ['scored_opp_ewma','conceded_opp_ewma']
    df[opp_columns] = df.groupby('opponent_team')[opp_columns].fillna(method='ffill')
    
    return df.sort_values(['date', 'team', 'name'])
