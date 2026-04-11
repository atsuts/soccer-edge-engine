import csv\r\nfrom pathlib import Path\r\nimport tkinter as tk\r\nfrom soccer_phase1_engine import SoccerEdgeEngine, MatchState, MarketInput\r\nfrom history_logger import log_analysis, settle_match_by_index, summarize_accuracy\r\nfrom watchlist import add_match, get_watchlist, get_match_by_index\r\n\r\n\r\nHISTORY_FILE = Path(__file__).with_name(\ analysis_history.csv\)\r\n\r\n# MOCK DATA STRUCTURES FOR FILTER INTERACTION\r\nMOCK_DATA = {\r\n    \countries\: [\ALL\, \England\, \Spain\, \Italy\, \Germany\, \France\],\r\n    \leagues\: {\r\n        \ALL\: [\ALL\, \Premier League\, \La Liga\, \Serie A\, \Bundesliga\, \Ligue 1\],\r\n        \England\: [\ALL\, \Premier League\, \Championship\, \League One\, \League Two\],\r\n        \Spain\: [\ALL\, \La Liga\, \Segunda Division\, \Copa del Rey\],\r\n        \Italy\: [\ALL\, \Serie A\, \Serie B\, \Coppa Italia\],\r\n        \Germany\: [\ALL\, \Bundesliga\, \2. Bundesliga\, \DFB Pokal\],\r\n        \France\: [\ALL\, \Ligue 1\, \Ligue 2\, \Coupe de France\]\r\n    },\r\n    \matches\: {\r\n        \Premier League\: [\r\n            {\home\: \Man City\, \away\: \Liverpool\, \home_score\: 2, \away_score\: 1, \minute\: 67, \status\: \LIVE\},\r\n            {\home\: \Arsenal\, \away\: \Chelsea\, \home_score\: 1, \away_score\: 0, \minute\: 45, \status\: \LIVE\},\r\n            {\home\: \Man United\, \away\: \Newcastle\, \home_score\: 0, \away_score\: 0, \minute\: 0, \status\: \Today 20:00\},\r\n            {\home\: \Liverpool\, \away\: \Tottenham\, \home_score\: 0, \away_score\: 0, \minute\: 0, \status\: \Upcoming 19:45\}\r\n        ],\r\n        \La Liga\: [\r\n            {\home\: \Real Madrid\, \away\: \Barcelona\, \home_score\: 0, \away_score\: 0, \minute\: 0, \status\: \Today 20:00\},\r\n            {\home\: \Atletico Madrid\, \away\: \Sevilla\, \home_score\: 0, \away_score\: 0, \minute\: 0, \status\: \Upcoming 17:30\},\r\n            {\home\: \Valencia\, \away\: \Real Sociedad\, \home_score\: 0, \away_score\: 0, \minute\: 0, \status\: \Today 18:00\}\r\n        ],\r\n        \Serie A\: [\r\n            {\home\: \Juventus\, \away\: \AC Milan\, \home_score\: 0, \away_score\: 0, \minute\: 0, \status\: \Today 17:15\},\r\n            {\home\: \Inter Milan\, \away\: \Napoli\, \home_score\: 0, \away_score\: 0, \minute\: 0, \status\: \Upcoming 15:00\},\r\n            {\home\: \Roma\, \away\: \Lazio\, \home_score\: 2, \away_score\: 1, \minute\: 90, \status\: \FT\}\r\n        ],\r\n        \Bundesliga\: [\r\n            {\home\: \Bayern Munich\, \away\: \Dortmund\, \home_score\: 0, \away_score\: 0, \minute\: 0, \status\: \Today 18:30\},\r\n            {\home\: \RB Leipzig\, \away\: \Leverkusen\, \home_score\: 0, \away_score\: 0, \minute\: 0, \status\: \Today 15:30\}\r\n        ],\r\n        \Champions League\: [\r\n            {\home\: \Barcelona\, \away\: \PSG\, \home_score\: 0, \away_score\: 0, \minute\: 0, \status\: \Champions League 20:00\},\r\n            {\home\: \Real Madrid\, \away\: \Man City\, \home_score\: 0, \away_score\: 0, \minute\: 0, \status\: \Champions League 20:00\}\r\n        ],\r\n        \FA Cup\: [\r\n            {\home\: \Arsenal\, \away\: \Leicester\, \home_score\: 0, \away_score\: 0, \minute\: 0, \status\: \FA Cup 15:00\},\r\n            {\home\: \Chelsea\, \away\: \Aston Villa\, \home_score\: 0, \away_score\: 0, \minute\: 0, \status\: \FA Cup 17:30\}\r\n        ]\r\n    }\r\n}\r\n\r\nroot = tk.Tk()\r\n\r\n# Global filter state
current_country = tk.StringVar( value="ALL")
current_league = tk.StringVar( value="ALL")

def on_country_select(event):
    """Handle country selection to update league list"""
    selection = countries_listbox.curselection()
    if selection:  # Check if selection is not empty
        selected_country = countries_listbox.get(selection[0])
        current_country.set(selected_country)
        update_league_list(selected_country)

def on_league_select(event):
    """Handle league selection to update matches list"""
    selection = leagues_listbox.curselection()
    if selection:  # Check if selection is not empty
        selected_league = leagues_listbox.get(selection[0])
        current_league.set(selected_league)
        update_matches_list(selected_league)

def on_match_select(event):
    """Handle match selection to load match into center"""
    selection = matches_listbox.curselection()
    if selection:  # Check if selection is not empty
        match_text = matches_listbox.get(selection[0])
        # Skip league headers (lines with ===)
        if not match_text.startswith("===") and match_text.strip():
            # Parse match text to extract team names and scores
            load_match_from_text(match_text)

def on_match_double_click(event):
    """Handle double-click on match to load into center"""
    selection = matches_listbox.curselection()
    if selection:  # Check if selection is not empty
        match_text = matches_listbox.get(selection[0])
        # Skip league headers (lines with ===)
        if not match_text.startswith("===") and match_text.strip():
            # Parse match text to extract team names and scores
            load_match_from_text(match_text)

def add_selected_match_to_watchlist():
    """Add currently selected match to watchlist"""
    selection = matches_listbox.curselection()
    if selection:
        match_text = matches_listbox.get(selection[0])
        # Skip league headers (lines with ===)
        if not match_text.startswith("===") and match_text.strip():
            # Avoid duplicates
            existing_items = list(watch_listbox.get(0, tk.END))
            if match_text not in existing_items:
                watch_listbox.insert(tk.END, match_text)

def update_league_list(country):
    """Update league list based on selected country"""
    current_selection = None
    if leagues_listbox.curselection():
        current_selection = leagues_listbox.get(leagues_listbox.curselection()[0])
    
    leagues_listbox.delete(0, tk.END)
    leagues = MOCK_DATA['leagues'].get(country, MOCK_DATA['leagues']['ALL'])
    for i, league in enumerate(leagues):
        leagues_listbox.insert(tk.END, league)
        # Restore previous selection if it exists in new list
        if league == current_selection:
            leagues_listbox.selection_set(i)
            leagues_listbox.see(i)

def update_matches_list(league):
    """Update matches list based on selected league"""
    current_selection = None
    if matches_listbox.curselection():
        current_selection = matches_listbox.get(matches_listbox.curselection()[0])
    
    matches_listbox.delete(0, tk.END)
    
    if league == 'ALL':
        # Show all matches grouped by league
        for league_name, matches in MOCK_DATA['matches'].items():
            if matches:  # Only add leagues that have matches
                matches_listbox.insert(tk.END, f"=== {league_name.upper()} ===")
                for match in matches:
                    match_text = format_match_text(match)
                    matches_listbox.insert(tk.END, match_text)
                matches_listbox.insert(tk.END, "")  # Empty line for separation
    else:
        # Show matches for specific league
        matches = MOCK_DATA['matches'].get(league, [])
        for match in matches:
            match_text = format_match_text(match)
            matches_listbox.insert(tk.END, match_text)

def format_match_text(match):
    """Format match data for display"""
    if match['status'] == 'LIVE':
        return f"LIVE {match['minute']}' {match['home']} {match['home_score']}-{match['away_score']} {match['away']}"
    elif match['status'] == 'FT':
        return f"FT {match['home']} {match['home_score']}-{match['away_score']} {match['away']}"
    else:
        return f"{match['status']} {match['home']} vs {match['away']}"

def load_match_from_text(match_text):
    """Load match data into center inputs from match text"""
    try:
        # Parse different match formats
        if 'LIVE' in match_text:
            # Format: "LIVE 67' Man City 2-1 Liverpool"
            parts = match_text.split()
            minute_part = parts[1]  # "67'"
            minute = int(minute_part.replace("'", ""))
            # Handle multi-word team names by finding score position
            score_idx = None
            for i, part in enumerate(parts):
                if '-' in part and i > 1:  # Score should be after minute and team names
                    score_idx = i
                    break
            if score_idx:
                score_parts = parts[score_idx].split('-')
                home_score = int(score_parts[0])
                away_score = int(score_parts[1])
                # Home team is everything between minute and score
                home_team = ' '.join(parts[2:score_idx])
                # Away team is everything after score
                away_team = ' '.join(parts[score_idx+1:])
            status = 'LIVE'
        elif 'FT' in match_text:
            # Format: "FT Man City 2-1 Liverpool"
            parts = match_text.split()
            minute = 90
            # Handle multi-word team names
            score_idx = None
            for i, part in enumerate(parts):
                if '-' in part and i > 0:  # Score should be after "FT" and team names
                    score_idx = i
                    break
            if score_idx:
                score_parts = parts[score_idx].split('-')
                home_score = int(score_parts[0])
                away_score = int(score_parts[1])
                # Home team is everything between FT and score
                home_team = ' '.join(parts[1:score_idx])
                # Away team is everything after score
                away_team = ' '.join(parts[score_idx+1:])
            status = 'FT'
        else:
            # Format: "Today 20:00 Real Madrid vs Barcelona"
            parts = match_text.split()
            minute = 0
            home_score = 0
            away_score = 0
            status = 'NS'
            # Find "vs" position
            vs_idx = None
            for i, part in enumerate(parts):
                if part == 'vs':
                    vs_idx = i
                    break
            if vs_idx:
                home_team = ' '.join(parts[2:vs_idx])
                away_team = ' '.join(parts[vs_idx+1:])
        
        # Update center inputs
        set_entry(home_team, home_team_str)
        set_entry(away_team, away_team_str)
        set_entry(minute, minute_val)
        set_entry(home_goals, home_score_val)
        set_entry(away_goals, away_score_val)
        
        # Update digital scoreboard
        update_digital_scoreboard_with_data(home_team, away_team, home_score, away_score, minute, status)
        
    except Exception as e:
        print(f"Error loading match: {e}")

def update_digital_scoreboard_with_data(home_team, away_team, home_score, away_score, minute, status):
    """Update digital scoreboard with parsed match data"""
    scoreboard['home_team'].config(text=home_team[:12])
    scoreboard['away_team'].config(text=away_team[:12])
    scoreboard['home_score'].config(text=str(home_score))
    scoreboard['away_score'].config(text=str(away_score))
    scoreboard['minute'].config(text=f"{minute:02d}'")
    
    # Update status color and text
    if status == 'LIVE':
        scoreboard['status'].config(text="LIVE", fg=DIGITAL_YELLOW)
    elif status == 'FT':
        scoreboard['status'].config(text="FT", fg=DIGITAL_RED)
    else:
        scoreboard['status'].config(text="NS", fg=DIGITAL_TEXT)

BG = "#111827"
CARD = "#1f2937"
CARD2 = "#0f172a"
TEXT = "#f9fafb"
MUTED = "#9ca3af"
GREEN = "#22c55e"
RED = "#ef4444"
CYAN = "#22d3ee"
GOLD = "#fbbf24"
PURPLE = "#6366f1"
PURPLE_HOVER = "#7c83ff"
BORDER = "#374151"

# Digital Scoreboard Colors - Realistic Stadium Style
DIGITAL_BG = "#1a1a1a"  # Dark gray instead of pure black
DIGITAL_TEXT = "#ff6b35"  # Warm orange-red like real LEDs
DIGITAL_RED = "#cc3333"  # Muted red
DIGITAL_BLUE = "#3366cc"  # Standard blue
DIGITAL_YELLOW = "#ffaa00"  # Amber yellow
DIGITAL_SHADOW = "#0d0d0d"  # Dark shadow for depth

def create_digital_scoreboard(parent):
    """Create a perfectly symmetrical digital scoreboard display."""
    # Main scoreboard frame with realistic styling
    scoreboard_frame = tk.Frame(parent, bg="#2d2d2d", relief="ridge", borderwidth=3)
    scoreboard_frame.pack(fill="x", padx=10, pady=(0, 15))
    
    # Inner frame for depth effect
    inner_frame = tk.Frame(scoreboard_frame, bg=DIGITAL_BG, relief="sunken", borderwidth=2)
    inner_frame.pack(fill="x", padx=3, pady=3)
    
    # Top row - Team Names with perfect symmetry
    teams_frame = tk.Frame(inner_frame, bg=DIGITAL_BG)
    teams_frame.pack(fill="x", pady=(12, 8))
    
    # Home team section
    home_section = tk.Frame(teams_frame, bg=DIGITAL_BG)
    home_section.pack(side="left", expand=True, fill="both", padx=(25, 4))
    
    home_team_frame = tk.Frame(home_section, bg="#0a0a0a", relief="ridge", borderwidth=2)
    home_team_frame.pack(fill="both", expand=True)
    
    home_team_label = tk.Label(
        home_team_frame,
        text="HOME",
        bg="#0a0a0a",
        fg=DIGITAL_BLUE,
        font=("Courier New", 20, "bold"),
        anchor="center"
    )
    home_team_label.pack(fill="both", expand=True, padx=8, pady=6)
    
    # VS section (center)
    vs_section = tk.Frame(teams_frame, bg=DIGITAL_BG, width=60)
    vs_section.pack(side="left", padx=4)
    vs_section.pack_propagate(False)
    
    vs_label = tk.Label(
        vs_section,
        text="VS",
        bg=DIGITAL_BG,
        fg=DIGITAL_YELLOW,
        font=("Courier New", 16, "bold"),
        anchor="center"
    )
    vs_label.pack(fill="both", expand=True, pady=6)
    
    # Away team section
    away_section = tk.Frame(teams_frame, bg=DIGITAL_BG)
    away_section.pack(side="left", expand=True, fill="both", padx=(4, 25))
    
    away_team_frame = tk.Frame(away_section, bg="#0a0a0a", relief="ridge", borderwidth=2)
    away_team_frame.pack(fill="both", expand=True)
    
    away_team_label = tk.Label(
        away_team_frame,
        text="AWAY",
        bg="#0a0a0a",
        fg=DIGITAL_RED,
        font=("Courier New", 20, "bold"),
        anchor="center"
    )
    away_team_label.pack(fill="both", expand=True, padx=8, pady=6)
    
    # Score row with perfect symmetry
    score_frame = tk.Frame(inner_frame, bg=DIGITAL_BG)
    score_frame.pack(fill="x", pady=8)
    
    # Home score section
    home_score_section = tk.Frame(score_frame, bg=DIGITAL_BG)
    home_score_section.pack(side="left", expand=True, fill="both", padx=(25, 4))
    
    home_score_frame = tk.Frame(home_score_section, bg="#0a0a0a", relief="ridge", borderwidth=3)
    home_score_frame.pack(fill="both", expand=True)
    
    home_score_label = tk.Label(
        home_score_frame,
        text="0",
        bg="#0a0a0a",
        fg=DIGITAL_BLUE,
        font=("Courier New", 64, "bold"),
        anchor="center"
    )
    home_score_label.pack(fill="both", expand=True, padx=10, pady=8)
    
    # Dash section (center)
    dash_section = tk.Frame(score_frame, bg=DIGITAL_BG, width=40)
    dash_section.pack(side="left", padx=4)
    dash_section.pack_propagate(False)
    
    dash_label = tk.Label(
        dash_section,
        text="-",
        bg=DIGITAL_BG,
        fg=DIGITAL_TEXT,
        font=("Courier New", 40, "bold"),
        anchor="center"
    )
    dash_label.pack(fill="both", expand=True, pady=8)
    
    # Away score section
    away_score_section = tk.Frame(score_frame, bg=DIGITAL_BG)
    away_score_section.pack(side="left", expand=True, fill="both", padx=(4, 25))
    
    away_score_frame = tk.Frame(away_score_section, bg="#0a0a0a", relief="ridge", borderwidth=3)
    away_score_frame.pack(fill="both", expand=True)
    
    away_score_label = tk.Label(
        away_score_frame,
        text="0",
        bg="#0a0a0a",
        fg=DIGITAL_RED,
        font=("Courier New", 64, "bold"),
        anchor="center"
    )
    away_score_label.pack(fill="both", expand=True, padx=10, pady=8)
    
    # Bottom row - Match info with perfect symmetry
    info_frame = tk.Frame(inner_frame, bg=DIGITAL_BG)
    info_frame.pack(fill="x", pady=(8, 12))
    
    # Minute section
    minute_section = tk.Frame(info_frame, bg=DIGITAL_BG)
    minute_section.pack(side="left", expand=True, fill="both", padx=(25, 4))
    
    minute_frame = tk.Frame(minute_section, bg="#1a1a1a", relief="ridge", borderwidth=2)
    minute_frame.pack(fill="both", expand=True)
    
    minute_label = tk.Label(
        minute_frame,
        text="00'",
        bg="#1a1a1a",
        fg=DIGITAL_TEXT,
        font=("Courier New", 14, "bold"),
        anchor="center"
    )
    minute_label.pack(fill="both", expand=True, padx=8, pady=4)
    
    # Status section
    status_section = tk.Frame(info_frame, bg=DIGITAL_BG)
    status_section.pack(side="left", expand=True, fill="both", padx=(4, 25))
    
    status_frame = tk.Frame(status_section, bg="#1a1a1a", relief="ridge", borderwidth=2)
    status_frame.pack(fill="both", expand=True)
    
    status_label = tk.Label(
        status_frame,
        text="NS",
        bg="#1a1a1a",
        fg=DIGITAL_YELLOW,
        font=("Courier New", 14, "bold"),
        anchor="center"
    )
    status_label.pack(fill="both", expand=True, padx=8, pady=4)
    
    # Store references for updating
    return {
        'home_team': home_team_label,
        'away_team': away_team_label,
        'home_score': home_score_label,
        'away_score': away_score_label,
        'minute': minute_label,
        'status': status_label
    }


def update_digital_scoreboard():
    """Update the digital scoreboard with current match data."""
    home = home_team.get().strip().upper() or "HOME"
    away = away_team.get().strip().upper() or "AWAY"
    home_score = home_goals.get() or "0"
    away_score = away_goals.get() or "0"
    minute = minute.get() or "0"
    
    # Handle single team analysis
    if not away_team.get().strip():
        # Single team mode - show only home team
        scoreboard['home_team'].config(text=home[:12])
        scoreboard['away_team'].config(text="ANALYSIS")
        scoreboard['home_score'].config(text=home_score)
        scoreboard['away_score'].config(text="")
    elif not home_team.get().strip():
        # Single team mode - show only away team
        scoreboard['home_team'].config(text="ANALYSIS")
        scoreboard['away_team'].config(text=away[:12])
        scoreboard['home_score'].config(text="")
        scoreboard['away_score'].config(text=away_score)
    else:
        # Full match mode
        scoreboard['home_team'].config(text=home[:12])
        scoreboard['away_team'].config(text=away[:12])
        scoreboard['home_score'].config(text=home_score)
        scoreboard['away_score'].config(text=away_score)
    
    # Update minute
    scoreboard['minute'].config(text=f"{minute_val.zfill(2)}'")
    
    # Update status based on minute
    if int(minute_val) >= 90:
        scoreboard['status'].config(text="FT", fg=DIGITAL_RED)
    elif int(minute_val) >= 45:
        scoreboard['status'].config(text="LIVE", fg=DIGITAL_YELLOW)
    elif int(minute_val) > 0:
        scoreboard['status'].config(text="1H", fg=DIGITAL_TEXT)
    else:
        scoreboard['status'].config(text="NS", fg=DIGITAL_TEXT)


live_job = None
live_running = False
live_interval_ms = 5000


def classify_edge(edge: float) -> str:
    if edge >= 25:
        return "HIGH VALUE"
    elif edge >= 8:
        return "VALUE"
    elif edge > 0:
        return "SMALL EDGE"
    else:
        return "AVOID"


def tag_for_edge(edge: float) -> str:
    return "green" if edge > 0 else "red"


def load_history_rows(limit: int = 10):
    if not HISTORY_FILE.exists():
        return []

    with open(HISTORY_FILE, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    return rows[-limit:]


def refresh_history_panel():
    history_box.config(state="normal")
    history_box.delete("1.0", tk.END)

    rows = load_history_rows(limit=10)

    if not rows:
        history_box.insert(tk.END, "No history yet. Run Analyze to create entries.", "muted")
        history_box.config(state="disabled")
        return

    header = f"{'IDX':<5}{'TIME':<12}{'MATCH':<24}{'REC':<12}{'EDGE':<8}{'SETTLED'}\n"
    divider = "-" * 78 + "\n"

    history_box.insert(tk.END, header, "header")
    history_box.insert(tk.END, divider, "header")

    start_index = max(0, len(rows) - 10)

    for local_i, row in enumerate(reversed(rows)):
        actual_index = start_index + (len(rows) - 1 - local_i)
        ts = row.get("timestamp", "")[-8:]
        match = f"{row.get('home_team', '')} vs {row.get('away_team', '')}"
        rec = row.get("recommended", "")
        edge = row.get("best_edge", "")
        settled = "YES" if row.get("settled", "0") == "1" else "NO"

        line = f"{actual_index:<5}{ts:<12}{match[:22]:<24}{rec[:10]:<12}{edge:<8}{settled}\n"

        tag = "muted"
        if settled == "YES":
            tag = "green" if row.get("recommended_hit") == "1" else "red"
        else:
            if edge.startswith("+"):
                tag = "green"
            elif edge.startswith("-"):
                tag = "red"

        history_box.insert(tk.END, line, tag)

    history_box.config(state="disabled")


def refresh_accuracy_panel():
    stats = summarize_accuracy()

    accuracy_box.config(state="normal")
    accuracy_box.delete("1.0", tk.END)

    accuracy_box.insert(tk.END, "ACCURACY SUMMARY\n", "header")
    accuracy_box.insert(tk.END, "-" * 32 + "\n", "header")
    accuracy_box.insert(tk.END, f"Settled analyses : {stats['total_settled']}\n", "white")
    accuracy_box.insert(tk.END, f"Recommended hit %: {stats['recommended_hit_rate']}%\n", "white")
    accuracy_box.insert(tk.END, f"Draw outcome %   : {stats['draw_hit_rate']}%\n", "white")
    accuracy_box.insert(tk.END, f"Under 2.5 hit %  : {stats['under_hit_rate']}%\n", "white")
    accuracy_box.insert(tk.END, f"Over 2.5 hit %   : {stats['over_hit_rate']}%\n", "white")

    accuracy_box.config(state="disabled")


def refresh_watchlist_panel():
    watch_listbox.delete(0, tk.END)

    data = get_watchlist()

    if not data:
        watch_listbox.insert(tk.END, "No matches in watchlist.")
        return

    for i, m in enumerate(data):
        match = f"{m['home']} vs {m['away']}"
        score = f"{m['home_goals']}-{m['away_goals']}"
        line = f"{i} | {match} | {m['minute']}' | {score}"
        watch_listbox.insert(tk.END, line)


def set_summary(rec_text="—", conf_text="—", edge_text="—", color=MUTED):
    rec_value.config(text=rec_text, fg=color)
    conf_value.config(text=conf_text, fg=color)
    edge_value.config(text=edge_text, fg=color)


def set_entry(entry_widget, value):
    entry_widget.delete(0, tk.END)
    entry_widget.insert(0, str(value))


def on_watchlist_select(event):
    try:
        selection = watch_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        m = get_match_by_index(idx)
        if m is None:
            tracker_status.config(text="Invalid watchlist selection.", fg=RED)
            return

        set_entry(home_team, m["home"])
        set_entry(away_team, m["away"])
        set_entry(minute, m["minute"])
        set_entry(home_goals, m["home_goals"])
        set_entry(away_goals, m["away_goals"])
        set_entry(stoppage_minutes, m["stoppage"])
        set_entry(home_red_cards, m["home_reds"])
        set_entry(away_red_cards, m["away_reds"])
        set_entry(pressure_bias, m["pressure"])
        set_entry(draw_price, m["draw_price"])
        set_entry(under_price, m["under_price"])
        set_entry(over_price, m["over_price"])

        tracker_status.config(text=f"Loaded watchlist match #{idx}.", fg=GREEN)
    except Exception as e:
        tracker_status.config(text=f"Load error: {e}", fg=RED)


def write_analysis_to_panels(state, market, scored_rows, best_label, best_edge, confidence, engine):
    summary_color = GREEN if best_edge > 0 else RED
    set_summary(best_label, confidence, f"{best_edge:+.1f}c", summary_color)

    result_box.config(state="normal")
    result_box.delete("1.0", tk.END)

    header = f"{'MARKET':<12}{'MODEL':>8}{'MARKET':>10}{'EDGE':>10}   SIGNAL\n"
    divider = "-" * 56 + "\n"

    result_box.insert(tk.END, header, "header")
    result_box.insert(tk.END, divider, "header")

    for row in scored_rows:
        line = (
            f"{row['label']:<12}"
            f"{row['model']:>8.1f}"
            f"{row['market']:>10.1f}"
            f"{row['edge']:>+10.1f}   "
            f"{row['signal']}\n"
        )
        result_box.insert(tk.END, line, tag_for_edge(row["edge"]))

    result_box.insert(tk.END, "\n")
    result_box.insert(tk.END, f"RECOMMENDED: {best_label}\n", "best")
    result_box.insert(tk.END, f"CONFIDENCE : {confidence}\n", "best")
    result_box.insert(tk.END, f"BEST EDGE  : {best_edge:+.1f}c\n", "best")
    result_box.insert(
        tk.END,
        f"\nContext: stoppage={state.stoppage_minutes_remaining}, "
        f"home reds={state.home_red_cards}, away reds={state.away_red_cards}, "
        f"pressure={state.pressure_bias}\n",
        "muted",
    )
    result_box.config(state="disabled")

    home_profile = engine.get_team_profile(state.home_team)
    away_profile = engine.get_team_profile(state.away_team)

    profile_box.config(state="normal")
    profile_box.delete("1.0", tk.END)

    profile_box.insert(tk.END, "HOME PROFILE\n", "header")
    profile_box.insert(
        tk.END,
        f"Team    : {state.home_team}\n"
        f"Attack  : {home_profile['attack']:.2f}\n"
        f"Defense : {home_profile['defense']:.2f}\n"
        f"Draw    : {home_profile['draw']:.2f}\n"
        f"Late    : {home_profile['late']:.2f}\n\n",
        "white",
    )

    profile_box.insert(tk.END, "AWAY PROFILE\n", "header")
    profile_box.insert(
        tk.END,
        f"Team    : {state.away_team}\n"
        f"Attack  : {away_profile['attack']:.2f}\n"
        f"Defense : {away_profile['defense']:.2f}\n"
        f"Draw    : {away_profile['draw']:.2f}\n"
        f"Late    : {away_profile['late']:.2f}\n",
        "white",
    )

    profile_box.config(state="disabled")


def calculate_analysis(log_to_history=True):
    engine = SoccerEdgeEngine()

    state = MatchState(
        home_team=home_team.get() or "Home",
        away_team=away_team.get() or "Away",
        minute=int(minute.get() or 75),
        home_goals=int(home_goals.get() or 0),
        away_goals=int(away_goals.get() or 0),
        stoppage_minutes_remaining=int(stoppage_minutes.get() or 0),
        home_red_cards=int(home_red_cards.get() or 0),
        away_red_cards=int(away_red_cards.get() or 0),
        pressure_bias=int(pressure_bias.get() or 0),
    )

    market = MarketInput(
        total_line=2.5,
        draw_cents=float(draw_price.get() or 0),
        under_cents=float(under_price.get() or 0),
        over_cents=float(over_price.get() or 0),
    )

    results = engine.full_analysis(state, market)

    rows = [
        ("DRAW", results["draw_prob"], market.draw_cents),
        ("UNDER 2.5", results["under_prob"], market.under_cents),
        ("OVER 2.5", results["over_prob"], market.over_cents),
    ]

    scored_rows = []
    best_label = None
    best_edge = -999

    for label, prob, price in rows:
        model_cents = engine.fair_cents(prob)
        edge = model_cents - price
        signal = classify_edge(edge)

        scored_rows.append(
            {
                "label": label,
                "model": model_cents,
                "market": price,
                "edge": edge,
                "signal": signal,
            }
        )

        if edge > best_edge:
            best_edge = edge
            best_label = label

    confidence = "HIGH" if best_edge >= 25 else "MEDIUM" if best_edge >= 8 else "LOW"

    if log_to_history:
        log_analysis(
            {
                "home_team": state.home_team,
                "away_team": state.away_team,
                "minute": state.minute,
                "home_goals": state.home_goals,
                "away_goals": state.away_goals,
                "stoppage": state.stoppage_minutes_remaining,
                "home_reds": state.home_red_cards,
                "away_reds": state.away_red_cards,
                "pressure": state.pressure_bias,
                "draw_price": market.draw_cents,
                "under_price": market.under_cents,
                "over_price": market.over_cents,
                "recommended": best_label,
                "confidence": confidence,
                "best_edge": f"{best_edge:+.1f}",
            }
        )

    write_analysis_to_panels(state, market, scored_rows, best_label, best_edge, confidence, engine)
    refresh_history_panel()
    refresh_accuracy_panel()


def run_analysis():
    try:
        calculate_analysis(log_to_history=True)
        tracker_status.config(text="Manual analysis complete.", fg=MUTED)
    except Exception as e:
        set_summary("ERROR", "—", "—", RED)

        result_box.config(state="normal")
        result_box.delete("1.0", tk.END)
        result_box.insert(tk.END, f"Error: {e}", "red")
        result_box.config(state="disabled")

        profile_box.config(state="normal")
        profile_box.delete("1.0", tk.END)
        profile_box.insert(tk.END, "Profile display unavailable", "red")
        profile_box.config(state="disabled")

        tracker_status.config(text=f"Analysis error: {e}", fg=RED)


def add_current_match():
    try:
        state = MatchState(
            home_team=home_team.get() or "Home",
            away_team=away_team.get() or "Away",
            minute=int(minute.get() or 0),
            home_goals=int(home_goals.get() or 0),
            away_goals=int(away_goals.get() or 0),
            stoppage_minutes_remaining=int(stoppage_minutes.get() or 0),
            home_red_cards=int(home_red_cards.get() or 0),
            away_red_cards=int(away_red_cards.get() or 0),
            pressure_bias=int(pressure_bias.get() or 0),
        )

        market = MarketInput(
            total_line=2.5,
            draw_cents=float(draw_price.get() or 0),
            under_cents=float(under_price.get() or 0),
            over_cents=float(over_price.get() or 0),
        )

        add_match(state, market)
        refresh_watchlist_panel()
        tracker_status.config(text="Match added to watchlist.", fg=GREEN)

    except Exception as e:
        tracker_status.config(text=f"Watchlist error: {e}", fg=RED)


def live_tick():
    global live_job, live_running

    if not live_running:
        return

    try:
        current_minute = int(minute.get() or 0)
        if current_minute < 120:
            set_entry(minute, current_minute + 1)

        calculate_analysis(log_to_history=False)
        tracker_status.config(
            text=f"Live tracker running. Minute auto-updated to {minute.get()}.",
            fg=GREEN,
        )
    except Exception as e:
        tracker_status.config(text=f"Live tracker error: {e}", fg=RED)
        live_running = False
        return

    live_job = root.after(live_interval_ms, live_tick)


def start_live_tracker():
    global live_job, live_running

    if live_running:
        tracker_status.config(text="Live tracker already running.", fg=MUTED)
        return

    live_running = True
    tracker_status.config(text="Live tracker started.", fg=GREEN)
    live_tick()


def stop_live_tracker():
    global live_job, live_running

    live_running = False
    if live_job is not None:
        root.after_cancel(live_job)
        live_job = None

    tracker_status.config(text="Live tracker stopped.", fg=MUTED)


def settle_selected():
    try:
        idx = int(settle_index.get())
        fh = int(final_home_goals.get() or 0)
        fa = int(final_away_goals.get() or 0)

        ok = settle_match_by_index(idx, fh, fa)
        if ok:
            settle_status.config(text=f"Settled row {idx}.", fg=GREEN)
        else:
            settle_status.config(text="Invalid index or no history.", fg=RED)

        refresh_history_panel()
        refresh_accuracy_panel()

    except Exception as e:
        settle_status.config(text=f"Settle error: {e}", fg=RED)


def create_input(parent, label_text):
    frame = tk.Frame(parent, bg=CARD)
    frame.pack(fill="x", pady=4)

    label = tk.Label(
        frame,
        text=label_text,
        width=22,
        anchor="w",
        bg=CARD,
        fg=TEXT,
        font=("Segoe UI", 10),
    )
    label.pack(side="left")

    entry = tk.Entry(
        frame,
        width=18,
        bg=CARD2,
        fg=TEXT,
        insertbackground=TEXT,
        relief="flat",
        font=("Segoe UI", 10),
    )
    entry.pack(side="right", ipady=4)

    return entry


def make_card(parent, title):
    outer = tk.Frame(parent, bg=BG, highlightbackground=BORDER, highlightthickness=1)
    outer.pack(fill="both", expand=False, padx=12, pady=8)

    title_label = tk.Label(
        outer,
        text=title,
        bg=BG,
        fg=CYAN,
        font=("Segoe UI", 11, "bold"),
        anchor="w",
    )
    title_label.pack(fill="x", padx=10, pady=(8, 4))

    body = tk.Frame(outer, bg=CARD)
    body.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    return outer, body


def make_filter_card(parent, title):
    """Create a compact card for horizontal filter layout"""
    outer = tk.Frame(parent, bg=BG, highlightbackground=BORDER, highlightthickness=1)
    
    title_label = tk.Label(
        outer,
        text=title,
        bg=BG,
        fg=CYAN,
        font=("Segoe UI", 10, "bold"),
        anchor="w",
    )
    title_label.pack(fill="x", padx=8, pady=(6, 2))

    body = tk.Frame(outer, bg=CARD)
    body.pack(fill="both", expand=True, padx=6, pady=(0, 6))

    return outer, body


root = tk.Tk()
root.title("Soccer Edge Engine — Click Watchlist")
root.geometry("1120x1180")
root.configure(bg=BG)

topbar = tk.Frame(root, bg=BG)
topbar.pack(fill="x", padx=12, pady=(12, 6))

title = tk.Label(
    topbar,
    text="SOCCER EDGE ENGINE",
    font=("Segoe UI", 22, "bold"),
    bg=BG,
    fg=TEXT,
)
title.pack(side="left")

summary_bar = tk.Frame(root, bg=BG)
summary_bar.pack(fill="x", padx=12, pady=(0, 10))

for i in range(3):
    summary_bar.grid_columnconfigure(i, weight=1)


def make_stat(parent, col, label_text):
    card = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    card.grid(row=0, column=col, padx=6, sticky="nsew")
    lbl = tk.Label(card, text=label_text, bg=CARD, fg=MUTED, font=("Segoe UI", 9, "bold"))
    lbl.pack(anchor="w", padx=12, pady=(8, 2))
    val = tk.Label(card, text="—", bg=CARD, fg=TEXT, font=("Segoe UI", 16, "bold"))
    val.pack(anchor="w", padx=12, pady=(0, 10))
    return val

rec_value = make_stat(summary_bar, 0, "RECOMMENDED")
conf_value = make_stat(summary_bar, 1, "CONFIDENCE")
edge_value = make_stat(summary_bar, 2, "BEST EDGE")

scroll_canvas = tk.Canvas(root, bg=BG, highlightthickness=0)
scroll_canvas.pack(fill="both", expand=True, padx=12, pady=6)

scrollbar = tk.Scrollbar(root, orient="vertical", command=scroll_canvas.yview)
scrollbar.pack(side="right", fill="y")

h_scrollbar = tk.Scrollbar(root, orient="horizontal", command=scroll_canvas.xview)
h_scrollbar.pack(side="bottom", fill="x")

scroll_canvas.configure(yscrollcommand=scrollbar.set, xscrollcommand=h_scrollbar.set)
scroll_canvas.bind('<Configure>', lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all")))

def _on_mousewheel(event):
    # Determine if we should scroll horizontally or vertically based on shift key
    if event.state & 0x0001:  # Shift key pressed
        scroll_canvas.xview_scroll(int(-1*(event.delta/120)), "units")
    else:
        scroll_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
scroll_canvas.bind("<MouseWheel>", _on_mousewheel)

def _on_countries_mousewheel(event):
    countries_listbox.yview_scroll(int(-1*(event.delta/120)), "units")
    return "break"

def _on_leagues_mousewheel(event):
    leagues_listbox.yview_scroll(int(-1*(event.delta/120)), "units")
    return "break"

def _on_matches_mousewheel(event):
    matches_listbox.yview_scroll(int(-1*(event.delta/120)), "units")
    return "break"

def _on_tournaments_mousewheel(event):
    tournaments_listbox.yview_scroll(int(-1*(event.delta/120)), "units")
    return "break"

def _on_view_mousewheel(event):
    view_listbox.yview_scroll(int(-1*(event.delta/120)), "units")
    return "break"

def _on_watchlist_mousewheel(event):
    watch_listbox.yview_scroll(int(-1*(event.delta/120)), "units")
    return "break"

main = tk.Frame(scroll_canvas, bg=BG)
scroll_canvas.create_window((0, 0), window=main, anchor="nw")

for i in range(3):
    main.grid_columnconfigure(i, weight=1, uniform="cols")
main.grid_rowconfigure(0, weight=1)

# Adjust column weights for better width distribution
main.grid_columnconfigure(0, weight=25)  # LEFT - 25%
main.grid_columnconfigure(1, weight=35)  # CENTER - 35% 
main.grid_columnconfigure(2, weight=40)  # RIGHT - 40%

left_col = tk.Frame(main, bg=BG)
left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

center_col = tk.Frame(main, bg=BG)
center_col.grid(row=0, column=1, sticky="nsew", padx=6)

right_col = tk.Frame(main, bg=BG)
right_col.grid(row=0, column=2, sticky="nsew", padx=(6, 0))

# LEFT COLUMN - Top filter row with 4 sections
filter_row = tk.Frame(left_col, bg=BG)
filter_row.pack(fill="x", padx=0, pady=(0, 4))

# Configure grid columns for equal width
for i in range(4):
    filter_row.grid_columnconfigure(i, weight=1, uniform="filter_cols")

# Country section
countries_outer = tk.Frame(filter_row, bg=BG, highlightbackground=BORDER, highlightthickness=1)
countries_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 2), pady=0)

countries_title = tk.Label(
    countries_outer,
    text="COUNTRY",
    bg=BG,
    fg=CYAN,
    font=("Segoe UI", 10, "bold"),
    anchor="w",
)
countries_title.pack(fill="x", padx=8, pady=(6, 2))

countries_body = tk.Frame(countries_outer, bg=CARD)
countries_body.pack(fill="both", expand=True, padx=6, pady=(0, 6))

countries_listbox = tk.Listbox(
    countries_body,
    height=4,
    width=18,
    bg=CARD2,
    fg=TEXT,
    font=("Consolas", 10),
    relief="flat",
    highlightthickness=0,
    selectbackground=PURPLE_HOVER,
    selectforeground="white",
    exportselection=False,  # Keep selection visible
)
countries_listbox.pack(fill="both", expand=True, padx=6, pady=6)
countries_listbox.bind("<MouseWheel>", _on_countries_mousewheel)
countries_listbox.bind("<<ListboxSelect>>", on_country_select)
# Add placeholder countries from mock data
for country in MOCK_DATA['countries']:
    countries_listbox.insert(tk.END, country)

# League section
leagues_outer = tk.Frame(filter_row, bg=BG, highlightbackground=BORDER, highlightthickness=1)
leagues_outer.grid(row=0, column=1, sticky="nsew", padx=2, pady=0)

leagues_title = tk.Label(
    leagues_outer,
    text="LEAGUE",
    bg=BG,
    fg=CYAN,
    font=("Segoe UI", 10, "bold"),
    anchor="w",
)
leagues_title.pack(fill="x", padx=8, pady=(6, 2))

leagues_body = tk.Frame(leagues_outer, bg=CARD)
leagues_body.pack(fill="both", expand=True, padx=6, pady=(0, 6))

leagues_listbox = tk.Listbox(
    leagues_body,
    height=4,
    width=18,
    bg=CARD2,
    fg=TEXT,
    font=("Consolas", 10),
    relief="flat",
    highlightthickness=0,
    selectbackground=PURPLE_HOVER,
    selectforeground="white",
    exportselection=False,  # Keep selection visible
)
leagues_listbox.pack(fill="both", expand=True, padx=6, pady=6)
leagues_listbox.bind("<MouseWheel>", _on_leagues_mousewheel)
leagues_listbox.bind("<<ListboxSelect>>", on_league_select)
# Add placeholder leagues from mock data
for league in MOCK_DATA['leagues']['ALL']:
    leagues_listbox.insert(tk.END, league)

# Tournament section
tournaments_outer = tk.Frame(filter_row, bg=BG, highlightbackground=BORDER, highlightthickness=1)
tournaments_outer.grid(row=0, column=2, sticky="nsew", padx=2, pady=0)

tournaments_title = tk.Label(
    tournaments_outer,
    text="TOURNAMENT",
    bg=BG,
    fg=CYAN,
    font=("Segoe UI", 10, "bold"),
    anchor="w",
)
tournaments_title.pack(fill="x", padx=8, pady=(6, 2))

tournaments_body = tk.Frame(tournaments_outer, bg=CARD)
tournaments_body.pack(fill="both", expand=True, padx=6, pady=(0, 6))

tournaments_listbox = tk.Listbox(
    tournaments_body,
    height=4,
    width=18,
    bg=CARD2,
    fg=TEXT,
    font=("Consolas", 10),
    relief="flat",
    highlightthickness=0,
    selectbackground=PURPLE_HOVER,
    selectforeground="white",
    exportselection=False,  # Keep selection visible
)
tournaments_listbox.pack(fill="both", expand=True, padx=6, pady=6)
tournaments_listbox.bind("<MouseWheel>", _on_tournaments_mousewheel)
# Add placeholder tournaments
for tournament in ["ALL", "Premier League", "Champions League", "FA Cup"]:
    tournaments_listbox.insert(tk.END, tournament)

# View section
view_outer = tk.Frame(filter_row, bg=BG, highlightbackground=BORDER, highlightthickness=1)
view_outer.grid(row=0, column=3, sticky="nsew", padx=(2, 0), pady=0)

view_title = tk.Label(
    view_outer,
    text="VIEW",
    bg=BG,
    fg=CYAN,
    font=("Segoe UI", 10, "bold"),
    anchor="w",
)
view_title.pack(fill="x", padx=8, pady=(6, 2))

view_body = tk.Frame(view_outer, bg=CARD)
view_body.pack(fill="both", expand=True, padx=6, pady=(0, 6))

view_listbox = tk.Listbox(
    view_body,
    height=4,
    width=18,
    bg=CARD2,
    fg=TEXT,
    font=("Consolas", 10),
    relief="flat",
    highlightthickness=0,
    selectbackground=PURPLE_HOVER,
    selectforeground="white",
    exportselection=False,  # Keep selection visible
)
view_listbox.pack(fill="both", expand=True, padx=6, pady=6)
view_listbox.bind("<MouseWheel>", _on_view_mousewheel)
# Add placeholder view options
for view in ["Live", "Today", "Yesterday", "Upcoming"]:
    view_listbox.insert(tk.END, view)

_, matches_body = make_card(left_col, "MATCHES")
matches_listbox = tk.Listbox(
    matches_body,
    height=25,  # Increased from 20 to make Matches more dominant
    width=36,
    bg=CARD2,
    fg=TEXT,
    font=("Consolas", 10),
    relief="flat",
    highlightthickness=0,
    selectbackground=PURPLE_HOVER,
    selectforeground="white",
)
matches_listbox.pack(fill="both", expand=True, padx=10, pady=10)
matches_listbox.bind("<MouseWheel>", _on_matches_mousewheel)
matches_listbox.bind("<<ListboxSelect>>", on_match_select)
matches_listbox.bind("<Double-Button-1>", on_match_double_click)

# Initialize with ALL league matches
update_matches_list("ALL")

_, watchlist_body = make_card(left_col, "WATCHLIST")
watch_listbox = tk.Listbox(
    watchlist_body,
    height=8,  
    width=36,
    bg=CARD2,
    fg=TEXT,
    font=("Consolas", 10),
    relief="flat",
    highlightthickness=0,
    selectbackground=PURPLE_HOVER,
    selectforeground="white",
)
watch_listbox.pack(fill="both", expand=True, padx=10, pady=10)
watch_listbox.bind("<MouseWheel>", _on_watchlist_mousewheel)
# Add placeholder watchlist items
for i in range(5):
    watch_listbox.insert(tk.END, f"{i} | Team X vs Team Y | {45}' | 2-1")

# CENTER COLUMN
_, input_body = make_card(center_col, "MATCH INPUTS")
scoreboard = create_digital_scoreboard(input_body)

home_team = create_input(input_body, "Home Team")
away_team = create_input(input_body, "Away Team")
minute = create_input(input_body, "Minute")
home_goals = create_input(input_body, "Home Goals")
away_goals = create_input(input_body, "Away Goals")
stoppage_minutes = create_input(input_body, "Stoppage Minutes")
home_red_cards = create_input(input_body, "Home Red Cards")
away_red_cards = create_input(input_body, "Away Red Cards")
pressure_bias = create_input(input_body, "Pressure Bias (-2 to 2)")
draw_price = create_input(input_body, "Draw Price")
under_price = create_input(input_body, "Under Price")
over_price = create_input(input_body, "Over Price")

set_entry(home_team, "")
set_entry(away_team, "")
set_entry(minute, 75)
set_entry(home_goals, 0)
set_entry(away_goals, 0)
set_entry(stoppage_minutes, 0)
set_entry(home_red_cards, 0)
set_entry(away_red_cards, 0)
set_entry(pressure_bias, 0)
set_entry(draw_price, 40)
set_entry(under_price, 45)
set_entry(over_price, 60)

analyze_btn = tk.Button(
    input_body,
    text="Analyze",
    command=run_analysis,
    bg=CYAN,
    fg="#001018",
    font=("Segoe UI", 11, "bold"),
    relief="flat",
    padx=12,
    pady=10,
)
analyze_btn.pack(fill="x", padx=10, pady=(12, 8))

add_watch_btn = tk.Button(
    input_body,
    text="Add to Watchlist",
    command=add_current_match,
    bg=PURPLE,
    fg="white",
    font=("Segoe UI", 10, "bold"),
    relief="flat",
    padx=12,
    pady=8,
)
add_watch_btn.pack(fill="x", padx=10, pady=4)

add_selected_btn = tk.Button(
    input_body,
    text="Add Selected Match to Watchlist",
    command=add_selected_match_to_watchlist,
    bg=CYAN,
    fg="#001018",
    font=("Segoe UI", 10, "bold"),
    relief="flat",
    padx=12,
    pady=8,
)
add_selected_btn.pack(fill="x", padx=10, pady=4)

live_start_btn = tk.Button(
    input_body,
    text="Start Live Tracker",
    command=start_live_tracker,
    bg=GREEN,
    fg="#06110a",
    font=("Segoe UI", 10, "bold"),
    relief="flat",
    padx=12,
    pady=8,
)
live_start_btn.pack(fill="x", padx=10, pady=4)

live_stop_btn = tk.Button(
    input_body,
    text="Stop Live Tracker",
    command=stop_live_tracker,
    bg=RED,
    fg="#1a0a0a",
    font=("Segoe UI", 10, "bold"),
    relief="flat",
    padx=12,
    pady=8,
)
live_stop_btn.pack(fill="x", padx=10, pady=4)

tracker_status = tk.Label(
    input_body,
    text="Click a watchlist row to load it.",
    bg=CARD,
    fg=MUTED,
    font=("Segoe UI", 9),
    anchor="w",
)
tracker_status.pack(fill="x", padx=10, pady=(6, 12))

# RIGHT COLUMN
_, result_body = make_card(right_col, "MODEL OUTPUT")
result_box = tk.Text(
    result_body,
    height=14,
    width=72,
    bg=CARD2,
    fg=TEXT,
    insertbackground=TEXT,
    font=("Consolas", 11),
    relief="flat",
    wrap="none",
)
result_box.pack(fill="x", padx=10, pady=10)
result_box.insert(tk.END, "Results will appear here")

result_box.tag_configure("green", foreground=GREEN)
result_box.tag_configure("red", foreground=RED)
result_box.tag_configure("white", foreground=TEXT)
result_box.tag_configure("muted", foreground=MUTED)
result_box.tag_configure("header", foreground=GOLD, font=("Consolas", 11, "bold"))
result_box.tag_configure("best", foreground=CYAN, font=("Consolas", 12, "bold"))
result_box.config(state="disabled")

_, profile_body = make_card(right_col, "TEAM PROFILES")
profile_box = tk.Text(
    profile_body,
    height=10,
    width=72,
    bg=CARD2,
    fg=TEXT,
    insertbackground=TEXT,
    font=("Consolas", 10),
    relief="flat",
    wrap="none",
)
profile_box.pack(fill="x", padx=10, pady=10)
profile_box.insert(tk.END, "Team profiles will appear here")

profile_box.tag_configure("header", foreground=GOLD, font=("Consolas", 11, "bold"))
profile_box.tag_configure("white", foreground=TEXT)
profile_box.tag_configure("red", foreground=RED)
profile_box.config(state="disabled")

_, watch_body = make_card(right_col, "WATCHLIST")
watch_listbox = tk.Listbox(
    watch_body,
    height=8,
    width=72,
    bg=CARD2,
    fg=TEXT,
    font=("Consolas", 10),
    relief="flat",
    highlightthickness=0,
    selectbackground=PURPLE_HOVER,
    selectforeground="white",
)
watch_listbox.pack(fill="x", padx=10, pady=10)
watch_listbox.bind("<<ListboxSelect>>", on_watchlist_select)

_, history_body = make_card(right_col, "RECENT HISTORY")
history_box = tk.Text(
    history_body,
    height=8,
    width=72,
    bg=CARD2,
    fg=TEXT,
    insertbackground=TEXT,
    font=("Consolas", 10),
    relief="flat",
    wrap="none",
)
history_box.pack(fill="x", padx=10, pady=10)
history_box.insert(tk.END, "History will appear here")

history_box.tag_configure("header", foreground=GOLD, font=("Consolas", 11, "bold"))
history_box.tag_configure("white", foreground=TEXT)
history_box.tag_configure("muted", foreground=MUTED)
history_box.tag_configure("green", foreground=GREEN)
history_box.tag_configure("red", foreground=RED)
history_box.config(state="disabled")

_, accuracy_body = make_card(right_col, "ACCURACY DASHBOARD")
accuracy_box = tk.Text(
    accuracy_body,
    height=7,
    width=72,
    bg=CARD2,
    fg=TEXT,
    insertbackground=TEXT,
    font=("Consolas", 10),
    relief="flat",
    wrap="none",
)
accuracy_box.pack(fill="x", padx=10, pady=10)
accuracy_box.insert(tk.END, "Accuracy stats will appear here")

accuracy_box.tag_configure("header", foreground=GOLD, font=("Consolas", 11, "bold"))
accuracy_box.tag_configure("white", foreground=TEXT)
accuracy_box.config(state="disabled")

refresh_watchlist_panel()
refresh_history_panel()
refresh_accuracy_panel()
set_summary()

root.mainloop()
