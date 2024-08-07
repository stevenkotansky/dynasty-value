from flask import Flask, render_template, redirect, url_for, jsonify
import pandas as pd
from compare_trade_values_v2 import run_league
import threading

app = Flask(__name__)

offline=True
show_visual=False
print_tables=False
mobile=False

# Initialize global variables
data_ready = False
bottom_roster_players = pd.DataFrame()
top_free_agents = pd.DataFrame()
printout = ""

def process_data():
    global data_ready, bottom_roster_players, top_free_agents, printout
    try:
        league_name = "Nerd Herd Dynasty"
        recommend_adds_within_x_value_points = 3
        recommend_maybe = True
        print_tables = True

        # Simulate data processing
        import time
        time.sleep(5)  # Simulate a delay
        bottom_roster_players, top_free_agents, printout = run_league(league_name, recommend_adds_within_x_value_points, recommend_maybe, offline, show_visual, print_tables, mobile)
        print("Data processing completed successfully.")
    except Exception as e:
        print(f"Error during data processing: {e}")
    finally:
        data_ready = True

@app.route('/')
def index():
    if not data_ready:
        return redirect(url_for('loading'))
    return render_template('index.html',
                           bottom_roster_players=bottom_roster_players.head(10).to_html(index=False),
                           top_free_agents=top_free_agents.head(30).to_html(index=False),
                           printout=printout)

@app.route('/loading')
def loading():
    return render_template('loading.html')

@app.route('/status')
def status():
    if data_ready:
        return jsonify({"status": "ready"})
    else:
        return jsonify({"status": "not_ready"}), 503

@app.route('/start_processing')
def start_processing():
    if not data_ready:
        threading.Thread(target=process_data).start()
    return redirect(url_for('loading'))

if __name__ == '__main__':
    threading.Thread(target=process_data).start()
    app.run(debug=True)
