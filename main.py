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
from compare_trade_values import run_league
from sklearn.preprocessing import MinMaxScaler

# Define how the process should run
offline=False
show_visual=False

# Choose if you want high level recommendations for all leagues, or specific recommendations for one league
high_level_recommendations=True

if high_level_recommendations==True:
    leagues = ["Nerd Herd Dynasty", "Fantasy Degens", "Dirty Dozen"]
    recommend_adds_within_x_value_points = 0
    recommend_maybe = False
    print_tables = False

    for league in leagues:
        print()
        run_league(league, recommend_adds_within_x_value_points, recommend_maybe, offline, show_visual, print_tables)
        print("----------------------------------------------------------------------------")
        print()

else:
    recommend_adds_within_x_value_points = 3
    recommend_maybe=True
    print_tables = True

    ### Select a specific league here:
    # league_name = "Nerd Herd Dynasty"
    league_name = "Fantasy Degens"
    # league_name = "Dirty Dozen"

    run_league(league_name, recommend_adds_within_x_value_points, recommend_maybe, offline, show_visual, print_tables)