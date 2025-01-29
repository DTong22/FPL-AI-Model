import pandas as pd
import numpy as np
import joblib
from keras.models import load_model

def encode_cols(df):
    # Specify the columns to be encoded
    columns_to_encode = ['position']
    
    # Use get_dummies to encode the specified columns
    df_encoded = pd.get_dummies(df[columns_to_encode], columns=columns_to_encode)

    # Concatenate the original DataFrame with the encoded DataFrame
    df_combined = pd.concat([df, df_encoded], axis=1)
    
    df_combined['was_home'] = df_combined['was_home'].astype(int)

    return df_combined

def select_features(df):
    features = [
        'bps_ewma',                
        'total_points_ewma',
        'threat_ewma',
        'creativity_ewma',           
        'yellow_cards_ewma',
        'saves_ewma',                    
        'goals_scored_ewma',
        'assists_ewma',
        'clean_sheets_ewma',        
        'transfers_in_rank',
        'transfers_out_rank',
        'bonus_ewma',                 
        'value',
        'scored_opp_ewma',   
        'conceded_opp_ewma',  
        'scored_team_ewma',   
        'conceded_team_ewma',
        'was_home',
        'position_GK',
        'position_DEF', 
        'position_MID',
        'position_FWD',
    ]
    X = df[features]
    scaler = joblib.load('scaler.joblib')
    X_scaled = scaler.transform(X)
    return X

def make_predictions(X):
    model = load_model('model.h5')
    predictions = model.predict(X)
    return predictions

def join_predictions(df, predictions):
    df['predicted_points'] = predictions
    df.rename(columns={'chance_of_playing_next_round': 'status'}, inplace=True)
    
    df1 = df[['season', 'round','date', 'web_name', 'name', 'element', 'predicted_points', 'position', 'team', 'opp_team_name','was_home','value', 'status', 'news']].sort_values(by= ['date', 'predicted_points'], ascending=[True, False]).round({'predicted_points': 1})
    df1['opp_team_name'] = df1['opp_team_name'].apply(map_team) + ' ' + np.where(df1['was_home'], '(H)', '(A)')
    df1['team'] = df1['team'].apply(map_team)
    df1['news'] = df1['news'].fillna('None')
    df1['round'] = df1['round'].astype(int)
    
    return df1

def update_predicted_points(row):
    if row['status'] == 0:  # Check if status is 0
        if 'Expected back' in row['news']:
            expected_back_date_str = row['news'].split('Expected back ')[1]
            expected_back_date = datetime.strptime(expected_back_date_str, '%d %b')
            fixture_date = datetime.strptime(row['date'], '%Y-%m-%d')

            # Adjust the expected back year if it is in the next year
            if fixture_date.month > 6 and expected_back_date.month < 7:
                expected_back_date = expected_back_date.replace(year=fixture_date.year + 1)
            else:
                expected_back_date = expected_back_date.replace(year=fixture_date.year)

            # Check if fixture date is before expected back date
            if fixture_date < expected_back_date:
                return 0
        else:
            return 0
    return row['predicted_points']

def make_pivot_table(df, fixtures):
    
    # Pivot the DataFrame with multiple value columns
    df_pivot = df.pivot_table(index=['web_name', 'position', 'value', 'team', 'element', 'status', 'news'], columns='round', values=['predicted_points', 'opp_team_name'], aggfunc={  'predicted_points': 'sum', 'opp_team_name': lambda x: ', '.join(x)}, fill_value=0)

    # Flatten the MultiIndex columns
    df_pivot.columns = [f'{col[0]}_{col[1]}' if col[0] in ['predicted_points', 'opp_team_name'] else col[0] for col in df_pivot.columns]

    # Add a column with the sum of all points for each player
    df_pivot['total_points'] = df.groupby(['web_name', 'position', 'value', 'team', 'element', 'status', 'news'])['predicted_points'].sum().astype(float).round(1)

    df_pivot = df_pivot.reset_index()
    df_pivot['total_3_GWs'] = (df_pivot.iloc[:, 13]+df_pivot.iloc[:, 14]+df_pivot.iloc[:, 15]).round(1)
    df_pivot.rename(columns={'web_name':'name'}, inplace=True)

    pd.set_option('display.max_rows', None)
    next_round = fixtures['round'].min()
    df_pivot = df_pivot.sort_values(f'predicted_points_{next_round}', ascending=False)

    df_pivot = df_pivot.round(1)
    df_pivot['total_3_GWs'] = df_pivot['total_3_GWs'].astype(float).round(1)
    return df_pivot
