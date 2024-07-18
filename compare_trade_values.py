import pandas as pd
from fuzzywuzzy import process, fuzz
import matplotlib.pyplot as plt
import numpy as np
import re
from datetime import datetime
import math
import os

from jb.get_jb_dynasty import get_jb_trade_values
from ktc.get_ktc import get_ktc_trade_values


def get_latest_file(directory):
    # Get a list of files in the directory
    files = os.listdir(directory)
    
    # Filter out directories, only keep files
    files = [f for f in files if os.path.isfile(os.path.join(directory, f))]
    
    # Sort files alphabetically
    files.sort()
    
    # Get the latest file (last in the sorted list)
    latest_file = files[-1] if files else None
    
    return latest_file

date_str = datetime.now().strftime('%Y%m%d')

offline=False
show_visual=False

league_name = "Nerd Herd Dynasty"
# league_name = "Fantasy Degens"
# league_name = "Dirty Dozen"
recommend_adds_within_x_value_points = 1

print(f"Running process for {league_name}")

if offline:
    print("Running in offline mode using most recently downloaded rankings.")
    jb_df = pd.read_csv("/Users/steven/Library/CloudStorage/OneDrive-Personal/Documents/2024/fantasy_coding/dynasty-value/jb/outfiles/"+get_latest_file("/Users/steven/Library/CloudStorage/OneDrive-Personal/Documents/2024/fantasy_coding/dynasty-value/jb/outfiles/"))
    ktc_df = pd.read_csv("/Users/steven/Library/CloudStorage/OneDrive-Personal/Documents/2024/fantasy_coding/dynasty-value/ktc/outfiles/all_players/"+get_latest_file("/Users/steven/Library/CloudStorage/OneDrive-Personal/Documents/2024/fantasy_coding/dynasty-value/ktc/outfiles/all_players/"))
else:
    jb_df = get_jb_trade_values()
    ktc_df = get_ktc_trade_values()


def normalize_name(player_name):
    # Remove common suffixes and extra spaces
    normalized_name = re.sub(r'\b(?:Jr|Sr|III|IV|V)\b', '', player_name).strip()
    return normalized_name

def get_best_match(player_name, list_of_names, threshold=90):
    best_match = None
    best_score = -1
    
    # Normalize player_name
    normalized_player_name = normalize_name(player_name)
    
    for name in list_of_names:
        # Normalize name from list_of_names
        normalized_name = normalize_name(name)
        
        # Calculate match score for both normalized and original names
        score_normalized = fuzz.token_sort_ratio(normalized_player_name, normalized_name)
        score_original = fuzz.token_sort_ratio(player_name, name)
        
        # Use the maximum score from both normalized and original names
        overall_score = max(score_normalized, score_original)
        
        # Update best match if current score is higher
        if overall_score > best_score and overall_score >= threshold:
            best_match = name
            best_score = overall_score
    
    return best_match if best_score >= threshold else None

# Apply the matching function
jb_df['BestMatch'] = jb_df['Player'].apply(lambda x: get_best_match(x, ktc_df['Player'].tolist()))

# Merge dataframes
merged_df = pd.merge(jb_df, ktc_df, left_on='BestMatch', right_on='Player')

# Drop the 'BestMatch' column if not needed
merged_df.drop(columns=['BestMatch'], inplace=True)
merged_df = merged_df.rename(columns={"Player_x":"Player", "Player_y": "Matched_Player_Name"})

merged_df = merged_df[["Player", "Matched_Player_Name", "Position", "Team", "Age", "JB Trade Value", "KTC Trade Value", "JB_normalized", "KTC_normalized"]]

# Function to calculate absolute or percentage difference
def calculate_difference(merged_df, absolute=True):
    if absolute:
        merged_df['Value_Difference'] = merged_df['JB_normalized'] - merged_df['KTC_normalized']
    else:
        merged_df['Value_Difference'] = ((merged_df['JB_normalized'] - merged_df['KTC_normalized']) / merged_df['KTC_normalized']) * 100
    return merged_df

# Calculate percentage difference by default
absolute = True
merged_df = calculate_difference(merged_df, absolute=absolute)

# Sort dataframe by absolute percentage difference
df_sorted = merged_df.reindex(merged_df['Value_Difference'].sort_values().index)

# Select top 25 players with largest value gaps
top_25 = df_sorted.tail(25)

# Select bottom 25 players with largest value drop-offs
bottom_25 = df_sorted.head(25)

# Prepare data for plotting
players = np.concatenate((bottom_25['Player'].values[::-1], top_25['Player'].values))
value_changes = np.concatenate((bottom_25['Value_Difference'].values[::-1], top_25['Value_Difference'].values))
positions = np.arange(len(players))

if show_visual==True:

    # Create color list based on positive or negative change
    colors = ['green' if vc >= 0 else 'red' for vc in value_changes]


    # Function to format player names for x-axis labels
    def format_player_name(player_name):
        parts = player_name.split()
        if len(parts) > 1:
            formatted_name = f'{parts[0][0]}. {" ".join(parts[1:])}'
        else:
            formatted_name = player_name
        return formatted_name


    # Plotting function with improved data labels and flipped axes
    def plot_value_changes(players, value_changes, colors):
        plt.figure(figsize=(6, 12))
        bars = plt.bar(positions, value_changes, color=colors)
        plt.xticks(positions, [format_player_name(name) for name in players], rotation=45, ha='right')
        plt.ylabel('Value Difference' + (' (Percentage)' if not absolute else ''))
        plt.title('Top 25 Players with Largest JB to KTC Value Gaps')
        plt.gca().invert_xaxis()  # Invert x-axis to have the largest changes on the right
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        # Adjust the bottom margin
        plt.subplots_adjust(bottom=0.3)

        # Adding data labels inside the bars with improved positioning
        print()
        print("Comparing player values between JB and KTC")
        for i, (vc, player) in enumerate(zip(value_changes, players)):
            if math.isnan(vc):
                print(f"NaN value for {player}")
                vc = 0
            if math.isinf(vc):
                print(f"infinite value for {player}")
                vc = 0
            label = f'{"+" if vc >= 0 else "-"}{abs(int(vc)):.0f}'
            plt.text(i, vc, label, ha='center', va='bottom' if vc >= 0 else 'top',
                    color='black', fontsize=9, fontweight='bold')

    # Toggle between absolute and percentage difference (assuming a user interaction)
    absolute_difference = True  # Set to True for absolute difference, False for percentage difference

    # Recalculate and plot based on toggle
    merged_df = calculate_difference(merged_df, absolute_difference)
    df_sorted = merged_df.sort_values(by='Value_Difference', ascending=False)
    top_25 = df_sorted.head(25)
    bottom_25 = df_sorted.tail(25)
    players = np.concatenate((bottom_25['Player'].values[::-1], top_25['Player'].values))
    value_changes = np.concatenate((bottom_25['Value_Difference'].values[::-1], top_25['Value_Difference'].values))
    colors = ['green' if vc >= 0 else 'red' for vc in value_changes]
    plot_value_changes(players, value_changes, colors)


    # show the rankings chart
    plt.tight_layout()
    plt.show()

# create weighted average trade value column
merged_df["weighted_avg_trade_value"] = round((merged_df["JB_normalized"]+merged_df["JB_normalized"]+merged_df["KTC_normalized"])/3,0)


from espn_api.football import League

if league_name=="Nerd Herd Dynasty":
    # Check ESPN waivers for best adds
    try:
        league = League(league_id=89078444, year=2024)
    except ConnectionError:
        print("HTTP error when attempting to connect to ESPN. Try again.")

    print()
    print("Getting free agents from Nerd Herd Dynasty League")
    free_agents = league.free_agents(size=2500)

    free_agent_names = []

    for player in free_agents:
        name = player.name
        free_agent_names.append(name)


    # fuzzy match players
    # Apply the matching function
    free_agents_df = merged_df

    free_agents_df['BestMatch'] = free_agents_df['Player'].apply(lambda x: get_best_match(x, free_agent_names))

    # filter to just free agents
    free_agents_df = free_agents_df[free_agents_df["BestMatch"].str.len()>0]

    list_of_free_agents = free_agents_df["Player"].to_list()

    def apply_fa_indicator(player_name):
        if player_name in list_of_free_agents:
            indicator=1
        else:
            indicator=0
        return indicator

    merged_df["free_agent_indicator"] = merged_df["Player"].apply(lambda x: apply_fa_indicator(x))

    # get roster indicator
    print()
    print("Getting roster for Runaway Achane")
    roster_names = []
    try:
        roster = league.load_roster_week(week=1)
        print(roster)

        for player in roster:
            name = player.name
            roster_names.append(name)

        roster_df = merged_df

        roster_df['BestMatch'] = roster_df['Player'].apply(lambda x: get_best_match(x, roster_names))

        # filter to just roster players
        roster_df = roster_df[roster_df["BestMatch"].str.len()>0]

        list_of_roster_players = roster_df["Player"].to_list()
    except Exception as e:
        # print(f"Error pulling ESPN roster: {e}")
        print("Unable to pull roster from ESPN. Using last manually inputted roster (7/10/24).")
        
        roster = ["Josh Allen", "Saquon Barkley", "Travis Etienne Jr.", "Garrett Wilson", "Justin Jefferson", "Trey McBride", "De'Von Achane", "Cowboys D/ST", "Justin Tucker", "D'Onta Foreman", "Gus Edwards", "Dallas Goedert", "Geno Smith", "Jahan Dotson", "Jermaine Burton", "Ray Davis", "Tee Higgins", "Jake Ferguson", "Zack Moss", "Tank Bigsby", "Nick Chubb", "Braelon Allen", "Aaron Rodgers", "Rico Dowdle", "Rasheen Ali"]
        
        for player in roster:
            name = player
            roster_names.append(name)

        roster_df = merged_df

        roster_df['BestMatch'] = roster_df['Player'].apply(lambda x: get_best_match(x, roster_names))

        # filter to just roster players
        roster_df = roster_df[roster_df["BestMatch"].str.len()>0]

        list_of_roster_players = roster_df["Player"].to_list()

elif league_name in ["Dirty Dozen", "Fantasy Degens"]:
    from sleeper_wrapper import League, Players

    if league_name=="Dirty Dozen":
        league_id = 1048295250541785088
    else:
        league_id = 1049034345945649152
    league = League(league_id)

    players = Players()

    all_players = players.get_all_players("nfl")

    rosters = league.get_rosters()

    league_rosters = {}
    players_on_rosters = []

    # add list of all player names to rosters
    for team in rosters:
        list_of_players_for_current_roster = []
        team_id = team["owner_id"]
        team_player_ids = team["players"]
        for player in team_player_ids:
            player_object = all_players[player]
            player_name = player_object["first_name"]+" "+player_object["last_name"]
            players_on_rosters.append(player_name)
            list_of_players_for_current_roster.append(player_name)

        league_rosters[team_id]=list_of_players_for_current_roster
    

    # fuzzy match players
    # Apply the matching function
    free_agents_df = merged_df

    free_agents_df['BestMatch'] = free_agents_df['Player'].apply(lambda x: get_best_match(x, players_on_rosters))
    print(free_agents_df)

    # filter to just free agents
    free_agents_df = free_agents_df[free_agents_df["BestMatch"].isnull()]

    list_of_free_agents = free_agents_df["Player"].to_list()

    def apply_fa_indicator(player_name):
        if player_name in list_of_free_agents:
            indicator=1
        else:
            indicator=0
        return indicator

    merged_df["free_agent_indicator"] = merged_df["Player"].apply(lambda x: apply_fa_indicator(x))

    # my roster
    my_roster = league_rosters['474455912807919616']

    # nick's roster
    # my_roster = league_rosters["978403408090615808"]

    

    print(f"Getting rostered players for {league_name}")
    roster_names = my_roster

    roster_df = merged_df

    roster_df['BestMatch'] = roster_df['Player'].apply(lambda x: get_best_match(x, roster_names))

    # filter to just roster players
    roster_df = roster_df[roster_df["BestMatch"].str.len()>0]

    list_of_roster_players = roster_df["Player"].to_list()


# for all leagues
def apply_roster_indicator(player_name):
    if player_name in list_of_roster_players:
        indicator=1
    else:
        indicator=0
    return indicator

merged_df["rostered_indicator"] = merged_df["Player"].apply(lambda x: apply_roster_indicator(x))

def change_player_positions(row):
    if row["Player"]=="Taysom Hill":
        position = "TE"
    else:
        position=row["Position"]
    return position

merged_df["Position"] = merged_df.apply(lambda row: change_player_positions(row), axis=1)

# save the df with the free agent indicators and roster indicators to CSV
merged_df.to_csv(f"trade_value_comps/trade_value_comparison_{date_str}.csv", index=False)

# identify valuable free agents compared to bottom of roster
bottom_roster_players = merged_df[merged_df["rostered_indicator"]==1].sort_values(by="weighted_avg_trade_value").head(10)

top_free_agents = merged_df[merged_df["free_agent_indicator"]==1].sort_values(by="weighted_avg_trade_value", ascending=False)

top_free_agents = top_free_agents[top_free_agents["Player"]!="Brian Thomas Jr."]

# for specific position only
# top_free_agents = top_free_agents[top_free_agents["Position"]=="RB"]

top_free_agents = top_free_agents[["Player", "Position", "Team", "Age", "JB Trade Value", "KTC Trade Value", "JB_normalized", "KTC_normalized", "weighted_avg_trade_value"]]

bottom_roster_players = bottom_roster_players[["Player", "Position", "Team", "Age", "JB Trade Value", "KTC Trade Value", "JB_normalized", "KTC_normalized", "weighted_avg_trade_value"]]

top_free_agents = top_free_agents.rename(columns={"weighted_avg_trade_value":"avg_value"})

top_free_agents["avg_value"] = top_free_agents["avg_value"].astype(int)

bottom_roster_players = bottom_roster_players.rename(columns={"weighted_avg_trade_value":"avg_value"})

bottom_roster_players["avg_value"] = bottom_roster_players["avg_value"].astype(int)

pd.set_option("display.max_columns", 8)

print()
print("Bottom 10 Roster Players:")
print(bottom_roster_players.head(10).to_string(index=False))
print()
print("Top 30 Free Agents:")
print(top_free_agents.head(30).to_string(index=False))

print()
print()


# Sort bottom roster players by avg_value and top free agents by avg_value
bottom_roster_players_sorted = bottom_roster_players.sort_values(by='avg_value')
top_free_agents_sorted = top_free_agents.sort_values(by='avg_value', ascending=False)

# Initialize lists to keep track of players to drop and add
players_to_drop = []
players_to_add = []

# Compare and suggest players to drop and add (overall)
for _, free_agent in top_free_agents_sorted.iterrows():
    for _, roster_player in bottom_roster_players_sorted.iterrows():
        if free_agent['avg_value'] > roster_player['avg_value'] or (free_agent['avg_value'] <= roster_player['avg_value'] <= free_agent['avg_value'] + recommend_adds_within_x_value_points):
            players_to_drop.append({
                'Player': roster_player['Player'],
                'Position': roster_player['Position'],
                'Team': roster_player['Team'],
                'Age': roster_player['Age'],
                'avg_value': roster_player['avg_value']
            })
            players_to_add.append({
                'Player': free_agent['Player'],
                'Position': free_agent['Position'],
                'Team': free_agent['Team'],
                'Age': free_agent['Age'],
                'avg_value': free_agent['avg_value']
            })
            bottom_roster_players_sorted = bottom_roster_players_sorted[bottom_roster_players_sorted['Player'] != roster_player['Player']]
            break

# Output overall recommendations
if players_to_drop and players_to_add:
    print("You should consider making the following transactions (overall):")
    for i in range(len(players_to_drop)):
        drop_player = players_to_drop[i]
        add_player = players_to_add[i]
        suggestion_type = "Maybe " if add_player['avg_value'] <= drop_player['avg_value'] <= add_player['avg_value'] + recommend_adds_within_x_value_points else ""
        print(f"{i+1}) {suggestion_type}Add: {add_player['Player']}, {add_player['Position']}, {add_player['Team']}, {int(add_player['Age'])}yo (Trade Value {add_player['avg_value']}) / {suggestion_type}Drop: {drop_player['Player']}, {drop_player['Position']}, {drop_player['Team']}, {int(drop_player['Age'])}yo (Trade Value {drop_player['avg_value']})")
else:
    print("No recommendations for dropping or adding players based on trade value differences (overall).")

# Initialize lists for position-based suggestions
position_based_recommendations = {}

# Compare and suggest players to drop and add within position groups
for pos in bottom_roster_players['Position'].unique():
    bottom_roster_players_pos_sorted = bottom_roster_players[bottom_roster_players['Position'] == pos].sort_values(by='avg_value')
    top_free_agents_pos_sorted = top_free_agents[top_free_agents['Position'] == pos].sort_values(by='avg_value', ascending=False)
    for _, roster_player in bottom_roster_players_pos_sorted.iterrows():
        for _, free_agent in top_free_agents_pos_sorted.iterrows():
            if free_agent['avg_value'] > roster_player['avg_value'] or (free_agent['avg_value'] <= roster_player['avg_value'] <= free_agent['avg_value'] + recommend_adds_within_x_value_points):
                if roster_player['Player'] not in position_based_recommendations:
                    position_based_recommendations[roster_player['Player']] = {
                        'drop': {
                            'Player': roster_player['Player'],
                            'Position': roster_player['Position'],
                            'Team': roster_player['Team'],
                            'Age': roster_player['Age'],
                            'avg_value': roster_player['avg_value']
                        },
                        'add_candidates': []
                    }
                position_based_recommendations[roster_player['Player']]['add_candidates'].append({
                    'Player': free_agent['Player'],
                    'Position': free_agent['Position'],
                    'Team': free_agent['Team'],
                    'Age': free_agent['Age'],
                    'avg_value': free_agent['avg_value']
                })

# Output position-based recommendations
if position_based_recommendations:
    print("\n\nYou should consider making the following transactions (position-based):")
    for drop_player, recommendation in position_based_recommendations.items():
        drop_info = recommendation['drop']
        print(f"\nDrop: {drop_info['Player']}, {drop_info['Position']}, {drop_info['Team']}, {int(drop_info['Age'])}yo (Trade Value {drop_info['avg_value']})")
        for i, add_candidate in enumerate(recommendation['add_candidates'], start=1):
            suggestion_type = "Maybe " if add_candidate['avg_value'] <= drop_info['avg_value'] <= add_candidate['avg_value'] + recommend_adds_within_x_value_points else ""
            print(f"    {i}) {suggestion_type}Add: {add_candidate['Player']}, {add_candidate['Position']}, {add_candidate['Team']}, {int(add_candidate['Age'])}yo (Trade Value {add_candidate['avg_value']})")
else:
    print("\nNo position-based recommendations for dropping or adding players based on trade value differences.")
