from flask import Flask, render_template

import pandas as pd
from fuzzywuzzy import process, fuzz
import matplotlib.pyplot as plt
import numpy as np
import re
from datetime import datetime
import math
import os
from jb.get_jb import get_jb_trade_values, get_jb_redraft
from ktc.get_ktc import get_ktc_trade_values
from compare_trade_values_v2 import run_league
from sklearn.preprocessing import MinMaxScaler

# Define how the process should run
offline=True
show_visual=False
mobile=False

# Choose if you want high level recommendations for all leagues, or specific recommendations for one league
high_level_recommendations=False

if high_level_recommendations==True:
    leagues = ["Nerd Herd Dynasty", "Fantasy Degens", "Dirty Dozen"]
    recommend_adds_within_x_value_points = 0
    recommend_maybe = False
    print_tables = False

    for league in leagues:
        print()
        bottom_roster_players, top_free_agents, printout = run_league(league, recommend_adds_within_x_value_points, recommend_maybe, offline, show_visual, print_tables, mobile)
        print("----------------------------------------------------------------------------")
        print()

else:
    recommend_adds_within_x_value_points = 3
    recommend_maybe=True
    print_tables = True

    ### Select a specific league here:
    league_name = "Nerd Herd Dynasty"
    # league_name = "Fantasy Degens"
    # league_name = "Dirty Dozen"

    bottom_roster_players, top_free_agents, printout = run_league(league_name, recommend_adds_within_x_value_points, recommend_maybe, offline, show_visual, print_tables, mobile)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html',
                           bottom_roster_players=bottom_roster_players.head(10).to_html(index=False),
                           top_free_agents=top_free_agents.head(30).to_html(index=False),
                           printout=printout)

if __name__ == '__main__':
    app.run(debug=True)