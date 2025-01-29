import pandas as pd
from pulp import LpProblem, LpVariable, lpSum, LpMaximize, LpStatus

def dream_team(df_pivot, n_next_rounds, fixtures):
    df = df_pivot[df_pivot['status']==100]   #100% players only
    selected = LpVariable.dicts("selected", df.index, cat="Binary")

    # Step 3: Define the objective function
    model = LpProblem("FPL_Team_Optimization", LpMaximize)
    captain_factor = 2  # Factor to double the captain's points

    if n_next_rounds == 1:
        col = f"predicted_points_{fixtures['round'].min()}"
    elif n_next_rounds == 3:
        col = "total_3_GWs"
    elif n_next_rounds == 6:
        col = "total_points"
    else:
        print("must be 1, 3 or 6")

    # Define the objective function with captaincy rule
    objective = lpSum(df[col][i] * selected[i] for i in df.index)
    captain_points = df[col].max()  # Get the maximum points among all players
    model += objective + captain_factor * captain_points * lpSum(selected[i] for i in df.index)  # Add captain's points

    # Step 4: Set the budget constraint
    budget_limit = 200#float(input('enter team value:'))-16  # Set your budget limit here
    model += lpSum(df["value"][i] * selected[i] for i in df.index) <= budget_limit

    # Step 5: Set the position requirements constraint
    position_constraints = {"GK": 1, "DEF": 3,"MID": 5, "FWD": 2 }  # Set your position requirements here
    for position, requirement in position_constraints.items():
        model += lpSum(selected[i] for i in df.index if df["position"][i] == position) == requirement

        # Constraint: Maximum 2 players per team per position
        teams = df["team"].unique().tolist()
        for team in teams:
            model += lpSum(selected[i] for i in df.index if df["team"][i] == team and df["position"][i] == position) <= 2

    # Step 6: Set the constraint on the maximum number of players from a single team
    max_players_per_team = 3  # Set the maximum number of players from a single team here
    teams = df["team"].unique().tolist()
    for team in teams:
        model += lpSum(selected[i] for i in df.index if df["team"][i] == team) <= max_players_per_team

    # Step 7: Solve the linear programming problem
    model.solve()

    # Step 8: Print the selected players, their positions, and expected points
    print("Status:", LpStatus[model.status])
    selected_players = [i for i in df.index if selected[i].value() == 1]
    selected_data = df.loc[selected_players, ["name", "position", "value", "team", col]]

    # Calculate total points and find the player with the most points
    sums = selected_data[col].sum()
    captain_points = selected_data.loc[selected_data[col].idxmax(), col]

    captain = selected_data.loc[selected_data[col].idxmax(), 'name']

    # Double the captain's points
    selected_data.loc[selected_data['name'] == captain, col] *= 2

    # Order the dataframe by position
    order_mapping = {"GK": 1, "DEF": 2, "MID": 3, "FWD": 4}
    selected_data["position_order"] = selected_data["position"].map(order_mapping)
    selected_data.sort_values("position_order", inplace=True)

    # Print the selected players
    print(f"Total points next {n_next_rounds}:", sums+captain_points)

    # Print the captain and their points (doubled)
    print("Captain:", captain)
    print("Money in bank", budget_limit-selected_data['value'].sum())

    selected_data['captain'] = selected_data['name'] == captain
    selected_data['ppm'] = selected_data[col]/selected_data['value']
    return selected_data
