import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import os
from fetch_fpl_data import  get_fpl_data, get_team_data, preprocess_elements, get_player_history, preprocess_history, preprocess_fixtures
from time_series import concat_fixtures, create_features, player_moving_average, team_moving_average, fill_fixtures
from ml_pipeline import encode_cols, X_scaled, select_features, make_predictions, join_predictions, update_predicted_points, make_pivot_table

# Get variables from .env
#DB_USER = os.getenv("DB_USER")
#DB_PASSWORD = os.getenv("DB_PASSWORD")
#DB_HOST = os.getenv("DB_HOST")
#DB_NAME = os.getenv("DB_NAME")

# SQLAlchemy engine setup
#engine = create_engine(f'mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}')

def fetch_data():
    fpl_data = get_fpl_data() # calls api, output is json (daily) store to sql
    teams_df = get_team_data(fpl_data) # outputs df of team using json input
    player_df = preprocess_elements(fpl_data) # outputs df of players using json input
    history_df, fixtures_df = get_player_history(player_df)  # calls api to get player history and fixtures
    processed_history = preprocess_history(history_df, player_df, teams_df) # processes history df in pandas
    processed_fixtures = preprocess_fixtures(fixtures_df, player_df, teams_df) # processes history df in pandas

    return processed_history, processed_fixtures

def store_data(processed_history, processed_fixtures):
    cleaned = pd.read_csv('player_data.csv')
    history = pd.concat([cleaned, processed_history])
    history.to_csv('player_data.csv', index=False)
    processed_fixtures.to_csv('next_6_gw.csv', index=False)
    #processed_history.to_sql('player_data', engine, if_exists='append', index=False)
    #processed_fixtures.to_sql('player_fixtures', engine, if_exists='replace', index=False)


def call_time_series():
    #history = pd.read_sql_table('player_data', engine)
    #fixtures = pd.read_sql_table('player_fixtures', engine)

    history = pd.read_csv('player_data.csv')
    fixtures = pd.read_csv('next_6_gw.csv')

    master = concat_fixtures(history, fixtures)
    df = create_features(master)
    df = player_moving_average(df)
    merged_df = team_moving_average(df)
    df = fill_fixtures(merged_df, fixtures)
    return df

def call_ml_pipeline(df):
    df = encode_cols(df)
    X_scaled = select_features(df)
    predictions = make_predictions(X_scaled)
    df1 = join_predictions(df, predictions)
    df1['predicted_points'] = df1.apply(update_predicted_points, axis=1)
    df_pivot = make_pivot_table(df1, fixtures)
    return df_pivot

def main():
    processed_history, processed_fixtures = fetch_data()
    store_data(processed_history, processed_fixtures)
    df = call_time_series()
    df_pivot = call_ml_pipeline()
    df_pivot.to_csv("pivot_points.csv", index=False)

if __name__ == "__main__":
    main()
    
