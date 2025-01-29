import pandas as pd

def get_manager_data(team_id, fixtures):
    GW = fixtures['round'].min()-1
    url = f"https://fantasy.premierleague.com/api/entry/{team_id}/event/{GW}/picks/"
    response = requests.get(url)
    return response.json()

def get_manager_team(manager_data, df_pivot):
    ids = []
    for i in range(0,15):
        ids.append(manager_data['picks'][i]['element'])

    manager_team = df_pivot[df_pivot['element'].isin(ids)].copy()
    manager_team.sort_values(by="element", key=lambda column: column.map(lambda e: ids.index(e)), inplace=True)
    return manager_team

def suggest_transfers(manager_team, df_pivot, cash_in_bank):

    available_players = df_pivot[~df_pivot['element'].isin(manager_team['element'])]
    
    transfer_suggestions = []

    #next_gw = int(available_players.columns[19][-2:])
    next_gw = min([int(col[-2:]) for col in available_players.columns if 'predicted_points_' in col])


    for _, row in manager_team.iterrows():
        # Conditions to find players in the same position, cheaper, and with higher predicted points and 'total_3_GWs'
        alternatives = available_players[
            (available_players['position'] == row['position']) & 
            (available_players['value'] <= row['value']+cash_in_bank) & 
            (available_players[f'predicted_points_{next_gw}'] > row[f'predicted_points_{next_gw}']) &
            (available_players['total_3_GWs'] > row['total_3_GWs'])

        ]
        
        # If there are any alternatives, get the best one (e.g., highest predicted points or total_3_GWs)
        if not alternatives.empty:
            best_alternative = alternatives.loc[alternatives['total_3_GWs'].idxmax()]

            # Store the suggested transfer
            transfer_suggestions.append({
                'Current Player': row['name'],
                'Replacement Player': best_alternative['name'],
                'Points Improvement Next 3 GWs' : round(best_alternative['total_3_GWs'] - row['total_3_GWs'], 1),
                'Current Player Value': row['value'],
                'Replacement Player Value': best_alternative['value'],
                'Current Player Team': row['team'],
                'Replacement Player Team': best_alternative['team'],
                f'Points Improvement GW{next_gw}': round(best_alternative[f'predicted_points_{next_gw}'] - row[f'predicted_points_{next_gw}'],1),
                f'Points Improvement GW{next_gw+1}': round(best_alternative[f'predicted_points_{next_gw+1}'] - row[f'predicted_points_{next_gw+1}'],1),
                f'Points Improvement GW{next_gw+2}': round(best_alternative[f'predicted_points_{next_gw+2}'] - row[f'predicted_points_{next_gw+2}'],1),
                f'Current Points GW{next_gw}': round(row[f'predicted_points_{next_gw}'],1),
                f'Current Points GW{next_gw+1}': round(row[f'predicted_points_{next_gw+1}'],1),
                f'Current Points GW{next_gw+2}': round(row[f'predicted_points_{next_gw+2}'],1),
                f'Replacement Points GW{next_gw}': round(best_alternative[f'predicted_points_{next_gw}'],1),
                f'Replacement Points GW{next_gw+1}': round(best_alternative[f'predicted_points_{next_gw+1}'],1),
                f'Replacement Points GW{next_gw+2}': round(best_alternative[f'predicted_points_{next_gw+2}'],1),
                'Current Next 3 GWs' : round(row['total_3_GWs'], 1),
                'Replacement Next 3 GWs' : round(best_alternative['total_3_GWs'], 1),
                'next_gw': next_gw,
                f'Opponent GW{next_gw}': row[f'opp_team_name_{next_gw}'] + ' ' + row[f'h/a_{next_gw}'],
                f'Opponent GW{next_gw+1}': row[f'opp_team_name_{next_gw+1}'] + ' ' + row[f'h/a_{next_gw+1}'],
                f'Opponent GW{next_gw+2}': row[f'opp_team_name_{next_gw+2}'] + ' ' + row[f'h/a_{next_gw+2}'],
                f'Replacement Opponent GW{next_gw}': best_alternative[f'opp_team_name_{next_gw}'] + ' ' + best_alternative[f'h/a_{next_gw}'],
                f'Replacement Opponent GW{next_gw+1}': best_alternative[f'opp_team_name_{next_gw+1}'] + ' ' + best_alternative[f'h/a_{next_gw+1}'],
                f'Replacement Opponent GW{next_gw+2}': best_alternative[f'opp_team_name_{next_gw+2}'] + ' ' + best_alternative[f'h/a_{next_gw+2}'],

            })
        else:
            # No better alternatives, suggest keeping the current player
            transfer_suggestions.append({
                'Current Player': row['name'],
                'Replacement Player': 'None',
                'Points Improvement Next 3 GWs': 0,
                'Current Player Value': row['value'],
                'Replacement Player Value': 'N/A',
                'Current Player Team': row['team'],
                'Replacement Player Team': 'N/A',
                f'Points Improvement GW{next_gw}': 0,
                f'Points Improvement GW{next_gw+1}': 0,
                f'Points Improvement GW{next_gw+2}': 0,
                f'Current Points GW{next_gw}': round(row[f'predicted_points_{next_gw}'],1),
                f'Current Points GW{next_gw+1}': round(row[f'predicted_points_{next_gw+1}'],1),
                f'Current Points GW{next_gw+2}': round(row[f'predicted_points_{next_gw+2}'],1),
                f'Replacement Points GW{next_gw}': 0,
                f'Replacement Points GW{next_gw+1}': 0,
                f'Replacement Points GW{next_gw+2}': 0,
                'Current Next 3 GWs' : round(row['total_3_GWs'],1),
                'Replacement Next 3 GWs' : 0,
                'next_gw': next_gw,
                f'Opponent GW{next_gw}': row[f'opp_team_name_{next_gw}'],
                f'Opponent GW{next_gw+1}': row[f'opp_team_name_{next_gw+1}'],
                f'Opponent GW{next_gw+2}': row[f'opp_team_name_{next_gw+2}'],
                f'Replacement Opponent GW{next_gw}': '',
                f'Replacement Opponent GW{next_gw+1}': '',
                f'Replacement Opponent GW{next_gw+2}': '',
            })


    suggestions_df = pd.DataFrame(transfer_suggestions)
    
    return suggestions_df.sort_values('Points Improvement Next 3 GWs', ascending=False)

def predicted_team_points(manager_team, df_pivot):
    return manager_team[manager_team.columns[19]].sum()

def predicted_points_and_suggestions(df_pivot, fixtures):
    manager_team = input_team(df_pivot)

    predicted_points = predicted_team_points(manager_team, df_pivot)

    suggestions = suggest_transfers(manager_team, df_pivot)

    return predicted_points, manager_team, suggestions
