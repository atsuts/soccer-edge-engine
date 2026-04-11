import csv
from pathlib import Path
import tkinter as tk
from soccer_phase1_engine import SoccerEdgeEngine, MatchState, MarketInput
from history_logger import log_analysis, settle_match_by_index, summarize_accuracy
from watchlist import add_match, get_watchlist, get_match_by_index


HISTORY_FILE = Path(__file__).with_name('analysis_history.csv')

# MOCK DATA STRUCTURES FOR FILTER INTERACTION
MOCK_DATA = {
    'countries': ['ALL', 'England', 'Spain', 'Italy', 'Germany', 'France'],
    'leagues': {
        'ALL': ['ALL', 'Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1'],
        'England': ['ALL', 'Premier League', 'Championship', 'League One', 'League Two'],
        'Spain': ['ALL', 'La Liga', 'Segunda Division', 'Copa del Rey'],
        'Italy': ['ALL', 'Serie A', 'Serie B', 'Coppa Italia'],
        'Germany': ['ALL', 'Bundesliga', '2. Bundesliga', 'DFB Pokal'],
        'France': ['ALL', 'Ligue 1', 'Ligue 2', 'Coupe de France']
    },
    'matches': {
        'Premier League': [
            {'home': 'Man City', 'away': 'Liverpool', 'home_score': 2, 'away_score': 1, 'minute': 67, 'status': 'LIVE'},
            {'home': 'Arsenal', 'away': 'Chelsea', 'home_score': 1, 'away_score': 0, 'minute': 45, 'status': 'LIVE'},
            {'home': 'Man United', 'away': 'Newcastle', 'home_score': 0, 'away_score': 0, 'minute': 0, 'status': 'Today 20:00'},
            {'home': 'Liverpool', 'away': 'Tottenham', 'home_score': 0, 'away_score': 0, 'minute': 0, 'status': 'Upcoming 19:45'}
        ],
        'La Liga': [
            {'home': 'Real Madrid', 'away': 'Barcelona', 'home_score': 0, 'away_score': 0, 'minute': 0, 'status': 'Today 20:00'},
            {'home': 'Atletico Madrid', 'away': 'Sevilla', 'home_score': 0, 'away_score': 0, 'minute': 0, 'status': 'Upcoming 17:30'},
            {'home': 'Valencia', 'away': 'Real Sociedad', 'home_score': 0, 'away_score': 0, 'minute': 0, 'status': 'Today 18:00'}
        ],
        'Serie A': [
            {'home': 'Juventus', 'away': 'AC Milan', 'home_score': 0, 'away_score': 0, 'minute': 0, 'status': 'Today 17:15'},
            {'home': 'Inter Milan', 'away': 'Napoli', 'home_score': 0, 'away_score': 0, 'minute': 0, 'status': 'Upcoming 15:00'},
            {'home': 'Roma', 'away': 'Lazio', 'home_score': 2, 'away_score': 1, 'minute': 90, 'status': 'FT'}
        ],
        'Bundesliga': [
            {'home': 'Bayern Munich', 'away': 'Dortmund', 'home_score': 0, 'away_score': 0, 'minute': 0, 'status': 'Today 18:30'},
            {'home': 'RB Leipzig', 'away': 'Leverkusen', 'home_score': 0, 'away_score': 0, 'minute': 0, 'status': 'Today 15:30'}
        ],
        'Champions League': [
            {'home': 'Barcelona', 'away': 'PSG', 'home_score': 0, 'away_score': 0, 'minute': 0, 'status': 'Champions League 20:00'},
            {'home': 'Real Madrid', 'away': 'Man City', 'home_score': 0, 'away_score': 0, 'minute': 0, 'status': 'Champions League 20:00'}
        ],
        'FA Cup': [
            {'home': 'Arsenal', 'away': 'Leicester', 'home_score': 0, 'away_score': 0, 'minute': 0, 'status': 'FA Cup 15:00'},
            {'home': 'Chelsea', 'away': 'Aston Villa', 'home_score': 0, 'away_score': 0, 'minute': 0, 'status': 'FA Cup 17:30'}
        ]
    }
}

# Global filter state

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
    global current_matches
    selection = matches_listbox.curselection()
    if selection:  # Check if selection is not empty
        match_text = matches_listbox.get(selection[0])
        # Skip league headers (lines with ===)
        if not match_text.startswith("===") and match_text.strip():
            # Find corresponding match object from current_matches
            match_index = selection[0]
            # Adjust index to account for league headers and empty lines
            actual_match_index = find_match_index_by_display_index(match_index)
            if actual_match_index is not None and actual_match_index < len(current_matches):
                match = current_matches[actual_match_index]
                load_match_from_structured_data(match)

def find_match_index_by_display_index(display_index):
    """Find actual match index accounting for headers and empty lines"""
    # Count non-match lines before the display index
    match_count = 0
    for i in range(display_index):
        text = matches_listbox.get(i)
        if text and not text.startswith("==="):
            match_count += 1
    return match_count

def load_match_from_structured_data(match):
    """Load match data from structured match object"""
    # Extract structured data
    home_team_val = match['home']
    away_team_val = match['away']
    home_score_val = match['home_score']
    away_score_val = match['away_score']
    minute_val = match['minute']
    status = match['status']
    
    # Debug prints for team values
    print("HOME TEAM:", home_team_val)
    print("AWAY TEAM:", away_team_val)
    
    # Update center inputs using Entry widgets
    set_entry(home_team, home_team_val)
    set_entry(away_team, away_team_val)
    set_entry(minute, str(minute_val))
    set_entry(home_goals, str(home_score_val))
    set_entry(away_goals, str(away_score_val))
    
    # Update digital scoreboard with structured data
    update_digital_scoreboard_with_data(home_team_val, away_team_val, home_score_val, away_score_val, minute_val, status)

def on_match_double_click(event):
    """Handle double-click on match to load into center"""
    global current_matches
    selection = matches_listbox.curselection()
    if selection:  # Check if selection is not empty
        match_text = matches_listbox.get(selection[0])
        # Skip league headers (lines with ===)
        if not match_text.startswith("===") and match_text.strip():
            # Find corresponding match object from current_matches
            match_index = selection[0]
            # Adjust index to account for league headers and empty lines
            actual_match_index = find_match_index_by_display_index(match_index)
            if actual_match_index is not None and actual_match_index < len(current_matches):
                match = current_matches[actual_match_index]
                load_match_from_structured_data(match)

def on_match_add_to_watchlist(event):
    """Handle add-to-watchlist for match rows"""
    selection = matches_listbox.curselection()
    if selection:
        match_text = matches_listbox.get(selection[0])
        # Skip league headers and empty lines
        if not match_text.startswith("===") and match_text.strip() and "[+]" in match_text:
            # Extract clean match text (remove [+] part)
            clean_match_text = match_text.replace(" [+]", "").strip()
            # Add to watchlist
            existing_items = list(watch_listbox.get(0, tk.END))
            if clean_match_text not in existing_items:
                watch_listbox.insert(tk.END, clean_match_text)

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
    global current_matches, match_widgets
    current_selection = None
    if matches_listbox.curselection():
        current_selection = matches_listbox.get(matches_listbox.curselection()[0])
    
    # Clear existing widgets safely
    try:
        for widget in matches_body.winfo_children():
            widget.destroy()
    except:
        pass  # Handle case where widgets don't exist yet
    
    # Hide the listbox since we're using widget rows instead
    matches_listbox.pack_forget()
    
    current_matches = []  # Reset match objects list
    match_widgets = []  # Reset match widgets list
    
    if league == 'ALL':
        # Show all matches grouped by league
        for league_name, matches in MOCK_DATA['matches'].items():
            if matches:  # Only add leagues that have matches
                # Add league header
                header_label = tk.Label(matches_body, text=f"=== {league_name.upper()} ===", 
                                     bg="#2d2d2d", fg="#ffffff", font=("Courier New", 10, "bold"))
                header_label.pack(fill="x", pady=(5, 2))
                
                for match in matches:
                    # Store match object and create widget row
                    current_matches.append(match)
                    match_widget = create_match_row_widget(matches_body, match)
                    match_widgets.append(match_widget)
                    
                # Add separator
                separator = tk.Frame(matches_body, height=1, bg="#374151")
                separator.pack(fill="x", pady=5)
    else:
        # Show matches for specific league
        matches = MOCK_DATA['matches'].get(league, [])
        for match in matches:
            # Store match object and create widget row
            current_matches.append(match)
            match_widget = create_match_row_widget(matches_body, match)
            match_widgets.append(match_widget)

def create_match_row_widget(parent, match):
    """Create a single match row widget with clickable elements"""
    # Main row container
    row_frame = tk.Frame(parent, bg="#1f2937", relief="flat", borderwidth=0)
    row_frame.pack(fill="x", pady=1)
    
    # Create match identifier for watchlist tracking
    match_id = f"{match['home']} vs {match['away']}"
    
    # Add mock edge and odds
    import random
    edge_value = random.uniform(-5.0, 10.0)
    home_odds = round(random.uniform(1.2, 4.5), 2)
    draw_odds = round(random.uniform(2.8, 4.2), 2)
    away_odds = round(random.uniform(2.5, 6.8), 2)
    
    # Determine edge color
    if edge_value > 0:
        edge_color = "#22c55e"  # Green
    else:
        edge_color = "#ef4444"  # Red
    
    # Check if in watchlist
    is_starred = match_id in watchlist_matches
    star_color = "#fbbf24" if is_starred else "#9ca3af"
    
    # Format status and minute
    if match['status'] == 'LIVE':
        status_text = "LIVE"
        minute_text = f"{match['minute']}"
        score_text = f"{match['home_score']}-{match['away_score']}"
    elif match['status'] == 'FT':
        status_text = "FT"
        minute_text = "90"
        score_text = f"{match['home_score']}-{match['away_score']}"
    else:
        status_text = "UP"
        minute_text = ""
        score_text = "0-0"
    
    # Status label
    status_label = tk.Label(row_frame, text=status_text, bg="#1f2937", fg="#ffffff",
                        font=("Courier New", 9), width=4, anchor="w")
    status_label.pack(side="left", padx=(5, 2))
    
    # Minute label
    minute_label = tk.Label(row_frame, text=minute_text, bg="#1f2937", fg="#3366cc",
                        font=("Courier New", 9), width=3, anchor="center")
    minute_label.pack(side="left", padx=2)
    
    # Home team label
    home_label = tk.Label(row_frame, text=match['home'][:10], bg="#1f2937", fg="#ffffff",
                       font=("Courier New", 9), width=10, anchor="w")
    home_label.pack(side="left", padx=2)
    
    # Score label (prominent)
    score_label = tk.Label(row_frame, text=score_text, bg="#1f2937", fg="#ff6b35",
                       font=("Courier New", 11, "bold"), width=3, anchor="center")
    score_label.pack(side="left", padx=2)
    
    # Away team label
    away_label = tk.Label(row_frame, text=match['away'][:10], bg="#1f2937", fg="#ffffff",
                       font=("Courier New", 9), width=10, anchor="w")
    away_label.pack(side="left", padx=2)
    
    # Edge label
    edge_label = tk.Label(row_frame, text=f"{edge_value:+.1f}", bg="#1f2937", fg=edge_color,
                       font=("Courier New", 9), width=5, anchor="center")
    edge_label.pack(side="left", padx=2)
    
    # Odds label
    odds_label = tk.Label(row_frame, text=f"{home_odds:.2f}/{draw_odds:.2f}/{away_odds:.2f}", 
                        bg="#1f2937", fg="#9ca3af", font=("Courier New", 8), width=12, anchor="center")
    odds_label.pack(side="left", padx=2)
    
    # Star button - separate click target
    star_btn = tk.Button(row_frame, text="Star" if is_starred else "Star", 
                      bg="#1f2937", fg=star_color, font=("Courier New", 10),
                      relief="flat", borderwidth=0, width=2,
                      command=lambda m=match: handle_star_click(m))
    star_btn.pack(side="left", padx=(5, 5))
    
    # Bind click to load match on entire row (not just label)
    row_frame.bind("<Button-1>", lambda e: load_match_from_structured_data(match))
    # Also bind individual elements to ensure click anywhere works
    status_label.bind("<Button-1>", lambda e, m=match: load_match_from_structured_data(match))
    minute_label.bind("<Button-1>", lambda e, m=match: load_match_from_structured_data(match))
    home_label.bind("<Button-1>", lambda e, m=match: load_match_from_structured_data(match))
    score_label.bind("<Button-1>", lambda e, m=match: load_match_from_structured_data(match))
    away_label.bind("<Button-1>", lambda e, m=match: load_match_from_structured_data(match))
    edge_label.bind("<Button-1>", lambda e, m=match: load_match_from_structured_data(match))
    odds_label.bind("<Button-1>", lambda e, m=match: load_match_from_structured_data(match))
    
    return row_frame

# Global watchlist tracking
watchlist_matches = set()
match_widgets = []

def handle_star_click(match):
    """Handle star button click - separate from row click"""
    match_id = f"{match['home']} vs {match['away']}"
    print("STAR CLICKED:", match_id)
    
    if match_id in watchlist_matches:
        print("REMOVING FROM WATCHLIST")
        watchlist_matches.remove(match_id)
    else:
        print("ADDING TO WATCHLIST")
        watchlist_matches.add(match_id)
    
    # Update display to reflect star state change
    current_league_name = current_league.get()
    if current_league_name:
        update_matches_list(current_league_name)
    
    # Update watchlist window
    update_watchlist_display()

def toggle_star_for_match(match):
    """Toggle watchlist status for a specific match"""
    global watchlist_matches
    
    match_id = f"{match['home']} vs {match['away']}"
    
    if match_id in watchlist_matches:
        watchlist_matches.remove(match_id)
        print(f"Removed from watchlist: {match_id}")
    else:
        watchlist_matches.add(match_id)
        print(f"Added to watchlist: {match_id}")
    
    # Update display to reflect star state change
    current_league_name = current_league.get()
    if current_league_name:
        update_matches_list(current_league_name)
    
    # Update watchlist window
    update_watchlist_display()

def format_match_text(match):
    """Format match data with clickable star and enhanced edge colors"""
    # Add mock edge values and odds for demonstration
    import random
    edge_value = random.uniform(-5.0, 10.0)
    home_odds = round(random.uniform(1.2, 4.5), 2)
    draw_odds = round(random.uniform(2.8, 4.2), 2)
    away_odds = round(random.uniform(2.5, 6.8), 2)
    
    # Create match identifier for watchlist tracking
    match_id = f"{match['home']} vs {match['away']}"
    
    # Determine edge color and intensity
    if edge_value > 0:
        # Positive edge - green with intensity based on magnitude
        if edge_value >= 8.0:
            edge_display = f"\033[92m{edge_value:+5.1f}\033[0m"  # Bright green
            edge_indicator = " "  # Super high alert
        elif edge_value >= 5.0:
            edge_display = f"\033[92m{edge_value:+5.1f}\033[0m"  # Bright green
            edge_indicator = " "
        elif edge_value >= 2.0:
            edge_display = f"\033[92m{edge_value:+5.1f}\033[0m"  # Medium green
        else:
            edge_display = f"\033[92m{edge_value:+5.1f}\033[0m"  # Soft green
            edge_indicator = " "
    else:
        # Negative edge - red with intensity based on magnitude
        if edge_value <= -6.0:
            edge_display = f"\033[91m{edge_value:+5.1f}\033[0m"  # Bright red
            edge_indicator = " "
        elif edge_value <= -3.0:
            edge_display = f"\033[91m{edge_value:+5.1f}\033[0m"  # Medium red
            edge_indicator = " "
        else:
            edge_display = f"\033[91m{edge_value:+5.1f}\033[0m"  # Soft red
            edge_indicator = " "
    
    # Check if match is in watchlist
    star = "★" if match_id in watchlist_matches else "☆"
    
    # Format status and minute with fixed widths
    if match['status'] == 'LIVE':
        status = "LIVE"
        minute = f"{match['minute']:>3}'"
        score = f"{match['home_score']}-{match['away_score']}"  # Score centered between teams
    elif match['status'] == 'FT':
        status = "FT "
        minute = "90'"
        score = f"{match['home_score']}-{match['away_score']}"  # Score centered between teams
    else:
        status = "UP "
        minute = "   "
        score = "0-0"  # Score centered between teams
    
    # Format team names with fixed widths (clean, no extra symbols)
    home_team = match['home'][:12].ljust(12)
    away_team = match['away'][:12].ljust(12)
    
    # Format odds with compact width
    odds_display = f"{home_odds:4.2f}/{draw_odds:4.2f}/{away_odds:4.2f}"
    
    # Create enhanced scanner row with edge prominence
    # STATUS | MIN | HOME TEAM     | SCORE | AWAY TEAM     | EDGE  | ODDS           | STAR
    scanner_row = f"{status} {minute} {home_team} {score} {away_team} {edge_display} {odds_display} {star}"
    
    return scanner_row

def toggle_watchlist_star(event):
    """Toggle watchlist status for selected match"""
    global current_matches, watchlist_matches
    
    selection = matches_listbox.curselection()
    if selection:
        match_text = matches_listbox.get(selection[0])
        # Skip league headers
        if not match_text.startswith("===") and match_text.strip():
            # Find corresponding match object
            match_index = selection[0]
            actual_match_index = find_match_index_by_display_index(match_index)
            if actual_match_index is not None and actual_match_index < len(current_matches):
                match = current_matches[actual_match_index]
                match_id = f"{match['home']} vs {match['away']}"
                
                # Toggle watchlist status
                if match_id in watchlist_matches:
                    watchlist_matches.remove(match_id)
                    print(f"Removed from watchlist: {match_id}")
                else:
                    watchlist_matches.add(match_id)
                    print(f"Added to watchlist: {match_id}")
                
                # Update display
                update_matches_list(current_league.get())
                
                # Update watchlist window
                update_watchlist_display()

def update_watchlist_display():
    """Update watchlist display with current matches"""
    global watch_listbox
    
    # Clear current watchlist
    watch_listbox.delete(0, tk.END)
    
    # Add watchlist matches
    for match_id in sorted(watchlist_matches):
        watch_listbox.insert(tk.END, match_id)

def on_watchlist_select(event):
    """Handle watchlist selection to load match into center"""
    selection = watch_listbox.curselection()
    if selection:
        match_text = watch_listbox.get(selection[0])
        # Parse match text to find teams
        if " vs " in match_text:
            parts = match_text.split(" vs ")
            home_team_name = parts[0]
            away_team_name = parts[1]
            
            # Find matching match in current_matches
            for match in current_matches:
                if match['home'] == home_team_name and match['away'] == away_team_name:
                    load_match_from_structured_data(match)
                    break

def highlight_goal_scored(match_index):
    """Briefly highlight a row when a goal is scored"""
    # Store original background
    original_bg = matches_listbox.cget("selectbackground")
    
    # Flash the row with bright color
    matches_listbox.selection_set(match_index)
    matches_listbox.configure(selectbackground="#00ff00")
    
    # Reset after short delay
    root.after(500, lambda: matches_listbox.configure(selectbackground=original_bg))
    root.after(600, lambda: matches_listbox.selection_clear(match_index))

def simulate_live_goal():
    """Simulate a live goal event for demonstration"""
    global current_matches
    
    # Randomly pick a live match
    live_matches = [i for i, match in enumerate(current_matches) if match['status'] == 'LIVE']
    if live_matches:
        match_idx = random.choice(live_matches)
        match = current_matches[match_idx]
        
        # Randomly increment home or away score
        if random.random() > 0.5:
            match['home_score'] += 1
        else:
            match['away_score'] += 1
        
        # Highlight the goal
        display_index = find_display_index_by_match_index(match_idx)
        if display_index is not None:
            highlight_goal_scored(display_index)
        
        # Update display
        update_matches_list(current_league.get())
        print(f"GOAL! {match['home']} {match['home_score']}-{match['away_score']} {match['away']}")

def find_display_index_by_match_index(match_index):
    """Find display index from match index (reverse of find_match_index_by_display_index)"""
    display_count = 0
    match_count = 0
    
    for i in range(matches_listbox.size()):
        text = matches_listbox.get(i)
        if text and not text.startswith("==="):
            if match_count == match_index:
                return i
            match_count += 1
    
    return None

def load_match_from_text(match_text):
    """Load match data into center inputs from match text"""
    try:
        # Initialize parsed values
        home_team_val = ''
        away_team_val = ''
        minute_val = 0
        home_score_val = 0
        away_score_val = 0
        status = 'NS'
        
        # Parse different match formats
        if 'LIVE' in match_text:
            # Format: "LIVE 67' Man City 2-1 Liverpool"
            parts = match_text.split()
            minute_part = parts[1]  # "67'"
            minute_val = int(minute_part.replace("'", ""))
            # Handle multi-word team names by finding score position
            score_idx = None
            for i, part in enumerate(parts):
                if '-' in part and i > 1:  # Score should be after minute and team names
                    score_idx = i
                    break
            if score_idx:
                score_parts = parts[score_idx].split('-')
                home_score_val = int(score_parts[0])
                away_score_val = int(score_parts[1])
                # Home team is everything between minute and score
                home_team_val = ' '.join(parts[2:score_idx])
                # Away team is everything after score
                away_team_val = ' '.join(parts[score_idx+1:])
            status = 'LIVE'
        elif 'FT' in match_text:
            # Format: "FT Man City 2-1 Liverpool"
            parts = match_text.split()
            minute_val = 90
            # Handle multi-word team names
            score_idx = None
            for i, part in enumerate(parts):
                if '-' in part and i > 0:  # Score should be after "FT" and team names
                    score_idx = i
                    break
            if score_idx:
                score_parts = parts[score_idx].split('-')
                home_score_val = int(score_parts[0])
                away_score_val = int(score_parts[1])
                # Home team is everything between FT and score
                home_team_val = ' '.join(parts[1:score_idx])
                # Away team is everything after score
                away_team_val = ' '.join(parts[score_idx+1:])
            status = 'FT'
        else:
            # Format: "Today 20:00 Real Madrid vs Barcelona"
            parts = match_text.split()
            minute_val = 0
            home_score_val = 0
            away_score_val = 0
            status = 'NS'
            # Find "vs" position
            vs_idx = None
            for i, part in enumerate(parts):
                if part == 'vs':
                    vs_idx = i
                    break
            if vs_idx:
                home_team_val = ' '.join(parts[2:vs_idx])
                away_team_val = ' '.join(parts[vs_idx+1:])
        
        # Update center inputs using Entry widgets
        set_entry(home_team, home_team_val)
        set_entry(away_team, away_team_val)
        set_entry(minute, str(minute_val))
        set_entry(home_goals, str(home_score_val))
        set_entry(away_goals, str(away_score_val))
        
        # Update digital scoreboard
        # Extract edge value from match text if present
        edge_value = None
        if '🟢' in match_text or '🟡' in match_text or '🔴' in match_text:
            # Extract edge value from formatted text
            import re
            edge_match = re.search(r'([🟢🟡🔴])([+-]?\d+\.?\d)', match_text)
            if edge_match:
                edge_value = float(edge_match.group(2))
        
        update_digital_scoreboard_with_data(home_team_val, away_team_val, home_score_val, away_score_val, minute_val, status, edge_value)
        
    except Exception as e:
        print(f"Error loading match: {e}")



def update_digital_scoreboard_with_data(home_team, away_team, home_score, away_score, minute, status, edge_value=None):
    """Update digital scoreboard with parsed match data"""
    # Debug prints to verify values
    print(f"DEBUG: Loading home team: '{home_team}'")
    print(f"DEBUG: Loading away team: '{away_team}'")
    
    # Truncate long team names with ...
    home_display = home_team[:12] + "..." if len(home_team) > 12 else home_team
    away_display = away_team[:12] + "..." if len(away_team) > 12 else away_team
    
    print(f"DEBUG: Home display: '{home_display}'")
    print(f"DEBUG: Away display: '{away_display}'")
    
    # Debug prints for widget references
    left_label_widget = scoreboard['home_team']
    right_label_widget = scoreboard['away_team']
    print("Updating left label:", left_label_widget)
    print("Updating right label:", right_label_widget)
    
    # Update team name boxes with ONLY team names
    scoreboard['home_team'].config(text=home_display)
    scoreboard['away_team'].config(text=away_display)
    # Update center score display
    scoreboard['home_score'].config(text=f"{home_score} - {away_score}")
    
    scoreboard['minute'].config(text=f"{minute:02d}'")
    
    # Update status color and text
    if status == 'LIVE':
        scoreboard['status'].config(text="LIVE", fg=DIGITAL_YELLOW)
    elif status == 'FT':
        scoreboard['status'].config(text="FT", fg=DIGITAL_RED)
    else:
        scoreboard['status'].config(text="NS", fg=DIGITAL_TEXT)
    
    # Update edge display if provided
    if edge_value is not None:
        if edge_value > 5.0:
            edge_color = "🟢"  # Green
        elif edge_value > 0.0:
            edge_color = "🟡"  # Yellow
        else:
            edge_color = "🔴"  # Red
        scoreboard['edge'].config(text=f"{edge_color}{edge_value:+.1f}")

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
    """Create unified match analysis panel with scoreboard, stats comparison, and tabs."""
    # Main unified container
    unified_frame = tk.Frame(parent, bg="#111827")
    unified_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # 1. HEADER/SCOREBOARD SECTION
    scoreboard_frame = tk.Frame(unified_frame, bg="#2d2d2d", relief="ridge", borderwidth=3)
    scoreboard_frame.pack(fill="x", pady=(0, 15))
    
    scoreboard_inner = tk.Frame(scoreboard_frame, bg=DIGITAL_BG, relief="sunken", borderwidth=2)
    scoreboard_inner.pack(fill="x", padx=3, pady=3)
    
    # Team names row
    teams_row = tk.Frame(scoreboard_inner, bg=DIGITAL_BG)
    teams_row.pack(fill="x", pady=(12, 8))
    
    # Home team (left)
    home_team_box = tk.Frame(teams_row, bg="#0a0a0a", relief="ridge", borderwidth=2)
    home_team_box.pack(side="left", expand=True, fill="both", padx=(25, 4))
    home_team_box.pack_propagate(False)
    
    home_team_label = tk.Label(home_team_box, text="HOME", bg="#0a0a0a", fg=DIGITAL_BLUE,
                            font=("Courier New", 16, "bold"), anchor="w", width=15, justify="left")
    home_team_label.pack(fill="both", expand=True, padx=8, pady=6)
    
    # Center score
    center_score_box = tk.Frame(teams_row, bg="#0a0a0a", relief="ridge", borderwidth=3)
    center_score_box.pack(side="left", expand=True, fill="both", padx=4)
    
    center_score_label = tk.Label(center_score_box, text="0 - 0", bg="#0a0a0a", fg=DIGITAL_TEXT,
                               font=("Courier New", 36, "bold"), anchor="center")
    center_score_label.pack(fill="both", expand=True, padx=10, pady=6)
    
    # Away team (right)
    away_team_box = tk.Frame(teams_row, bg="#0a0a0a", relief="ridge", borderwidth=2)
    away_team_box.pack(side="left", expand=True, fill="both", padx=(4, 25))
    away_team_box.pack_propagate(False)
    
    away_team_label = tk.Label(away_team_box, text="AWAY", bg="#0a0a0a", fg=DIGITAL_RED,
                            font=("Courier New", 16, "bold"), anchor="e", width=15, justify="right")
    away_team_label.pack(fill="both", expand=True, padx=8, pady=6)
    
    # Info row (minute, status, edge)
    info_row = tk.Frame(scoreboard_inner, bg=DIGITAL_BG)
    info_row.pack(fill="x", pady=(8, 12))
    
    minute_box = tk.Frame(info_row, bg="#1a1a1a", relief="ridge", borderwidth=2)
    minute_box.pack(side="left", expand=True, fill="both", padx=(25, 4))
    minute_label = tk.Label(minute_box, text="00'", bg="#1a1a1a", fg=DIGITAL_TEXT,
                         font=("Courier New", 14, "bold"), anchor="center")
    minute_label.pack(fill="both", expand=True, padx=8, pady=4)
    
    status_box = tk.Frame(info_row, bg="#1a1a1a", relief="ridge", borderwidth=2)
    status_box.pack(side="left", expand=True, fill="both", padx=(4, 4))
    status_label = tk.Label(status_box, text="NS", bg="#1a1a1a", fg=DIGITAL_YELLOW,
                         font=("Courier New", 14, "bold"), anchor="center")
    status_label.pack(fill="both", expand=True, padx=8, pady=4)
    
    edge_box = tk.Frame(info_row, bg="#1a1a1a", relief="ridge", borderwidth=2)
    edge_box.pack(side="left", expand=True, fill="both", padx=(4, 25))
    edge_label = tk.Label(edge_box, text="+0.0", bg="#1a1a1a", fg=DIGITAL_TEXT,
                       font=("Courier New", 12, "bold"), anchor="center")
    edge_label.pack(fill="both", expand=True, padx=8, pady=4)
    
    # 2. MATCH STATS COMPARISON SECTION
    stats_frame = tk.Frame(unified_frame, bg="#2d2d2d", relief="ridge", borderwidth=3)
    stats_frame.pack(fill="x", pady=(0, 15))
    
    stats_inner = tk.Frame(stats_frame, bg="#1a1a1a", relief="sunken", borderwidth=2)
    stats_inner.pack(fill="x", padx=3, pady=3)
    
    # Create centered stat rows
    create_centered_stat_row(stats_inner, "Possession", 60, 40, DIGITAL_BLUE, DIGITAL_RED)
    create_centered_stat_row(stats_inner, "Corners", 7, 2, DIGITAL_BLUE, DIGITAL_RED)
    create_centered_stat_row(stats_inner, "Shots OT", 5, 3, DIGITAL_BLUE, DIGITAL_RED)
    create_centered_stat_row(stats_inner, "Red Cards", 0, 1, DIGITAL_BLUE, DIGITAL_RED)
    create_centered_stat_row(stats_inner, "Pressure Bias", 1, -1, DIGITAL_BLUE, DIGITAL_RED)
    
    # 3. TABS SECTION
    tabs_frame = tk.Frame(unified_frame, bg="#2d2d2d", relief="ridge", borderwidth=3)
    tabs_frame.pack(fill="both", expand=True)
    
    # Tab buttons
    tab_buttons_frame = tk.Frame(tabs_frame, bg="#2d2d2d")
    tab_buttons_frame.pack(fill="x", padx=3, pady=(3, 0))
    
    stats_tab = tk.Button(tab_buttons_frame, text="Stats", bg="#3366cc", fg="white",
                         font=("Courier New", 12, "bold"), relief="raised", borderwidth=2)
    stats_tab.pack(side="left", padx=2, pady=2)
    
    info_tab = tk.Button(tab_buttons_frame, text="Info", bg="#1a1a1a", fg="white",
                        font=("Courier New", 12, "bold"), relief="flat", borderwidth=1)
    info_tab.pack(side="left", padx=2, pady=2)
    
    h2h_tab = tk.Button(tab_buttons_frame, text="H2H", bg="#1a1a1a", fg="white",
                       font=("Courier New", 12, "bold"), relief="flat", borderwidth=1)
    h2h_tab.pack(side="left", padx=2, pady=2)
    
    # Tab content
    tab_content = tk.Frame(tabs_frame, bg="#1a1a1a", relief="sunken", borderwidth=2)
    tab_content.pack(fill="both", expand=True, padx=3, pady=(0, 3))
    
    # Stats tab content (default)
    stats_content = tk.Frame(tab_content, bg="#1a1a1a")
    stats_content.pack(fill="both", expand=True, padx=10, pady=10)
    
    return {
        'home_team': home_team_label, 'away_team': away_team_label,
        'home_score': center_score_label, 'away_score': center_score_label,
        'minute': minute_label, 'status': status_label, 'edge': edge_label
    }

def create_unified_match_panel(parent):
    """Create unified match analysis panel with scoreboard, stats, tabs, and actions."""
    
    # 1. SCOREBOARD HEADER SECTION
    scoreboard_frame = tk.Frame(parent, bg="#2d2d2d", relief="ridge", borderwidth=3)
    scoreboard_frame.pack(fill="x", pady=(0, 15))
    
    scoreboard_inner = tk.Frame(scoreboard_frame, bg=DIGITAL_BG, relief="sunken", borderwidth=2)
    scoreboard_inner.pack(fill="x", padx=3, pady=3)
    
    # Team names row
    teams_row = tk.Frame(scoreboard_inner, bg=DIGITAL_BG)
    teams_row.pack(fill="x", pady=(12, 8))
    
    # Home team (left)
    home_team_box = tk.Frame(teams_row, bg="#0a0a0a", relief="ridge", borderwidth=2)
    home_team_box.pack(side="left", expand=True, fill="both", padx=(25, 4))
    home_team_box.pack_propagate(False)
    
    home_team_label = tk.Label(home_team_box, text="HOME", bg="#0a0a0a", fg=DIGITAL_BLUE,
                            font=("Courier New", 16, "bold"), anchor="w", width=15, justify="left")
    home_team_label.pack(fill="both", expand=True, padx=8, pady=6)
    
    # Center score
    center_score_box = tk.Frame(teams_row, bg="#0a0a0a", relief="ridge", borderwidth=3)
    center_score_box.pack(side="left", expand=True, fill="both", padx=4)
    
    center_score_label = tk.Label(center_score_box, text="0 - 0", bg="#0a0a0a", fg=DIGITAL_TEXT,
                               font=("Courier New", 36, "bold"), anchor="center")
    center_score_label.pack(fill="both", expand=True, padx=10, pady=6)
    
    # Away team (right)
    away_team_box = tk.Frame(teams_row, bg="#0a0a0a", relief="ridge", borderwidth=2)
    away_team_box.pack(side="left", expand=True, fill="both", padx=(4, 25))
    away_team_box.pack_propagate(False)
    
    away_team_label = tk.Label(away_team_box, text="AWAY", bg="#0a0a0a", fg=DIGITAL_RED,
                            font=("Courier New", 16, "bold"), anchor="e", width=15, justify="right")
    away_team_label.pack(fill="both", expand=True, padx=8, pady=6)
    
    # Info row (minute, status, edge)
    info_row = tk.Frame(scoreboard_inner, bg=DIGITAL_BG)
    info_row.pack(fill="x", pady=(8, 12))
    
    minute_box = tk.Frame(info_row, bg="#1a1a1a", relief="ridge", borderwidth=2)
    minute_box.pack(side="left", expand=True, fill="both", padx=(25, 4))
    minute_label = tk.Label(minute_box, text="00'", bg="#1a1a1a", fg=DIGITAL_TEXT,
                         font=("Courier New", 14, "bold"), anchor="center")
    minute_label.pack(fill="both", expand=True, padx=8, pady=4)
    
    status_box = tk.Frame(info_row, bg="#1a1a1a", relief="ridge", borderwidth=2)
    status_box.pack(side="left", expand=True, fill="both", padx=(4, 4))
    status_label = tk.Label(status_box, text="NS", bg="#1a1a1a", fg=DIGITAL_YELLOW,
                         font=("Courier New", 14, "bold"), anchor="center")
    status_label.pack(fill="both", expand=True, padx=8, pady=4)
    
    edge_box = tk.Frame(info_row, bg="#1a1a1a", relief="ridge", borderwidth=2)
    edge_box.pack(side="left", expand=True, fill="both", padx=(4, 25))
    edge_label = tk.Label(edge_box, text="+0.0", bg="#1a1a1a", fg=DIGITAL_TEXT,
                       font=("Courier New", 12, "bold"), anchor="center")
    edge_label.pack(fill="both", expand=True, padx=8, pady=4)
    
    # 2. STATS COMPARISON PANEL
    stats_frame = tk.Frame(parent, bg="#2d2d2d", relief="ridge", borderwidth=3)
    stats_frame.pack(fill="x", pady=(0, 15))
    
    stats_inner = tk.Frame(stats_frame, bg="#1a1a1a", relief="sunken", borderwidth=2)
    stats_inner.pack(fill="x", padx=3, pady=3)
    
    # Create centered stat rows
    create_centered_stat_row(stats_inner, "Possession", 60, 40, DIGITAL_BLUE, DIGITAL_RED)
    create_centered_stat_row(stats_inner, "Corners", 7, 2, DIGITAL_BLUE, DIGITAL_RED)
    create_centered_stat_row(stats_inner, "Shots OT", 5, 3, DIGITAL_BLUE, DIGITAL_RED)
    create_centered_stat_row(stats_inner, "Red Cards", 0, 1, DIGITAL_BLUE, DIGITAL_RED)
    create_centered_stat_row(stats_inner, "Pressure Bias", 1, -1, DIGITAL_BLUE, DIGITAL_RED)
    
    # 3. TABS ROW
    tabs_frame = tk.Frame(parent, bg="#2d2d2d", relief="ridge", borderwidth=3)
    tabs_frame.pack(fill="x", pady=(0, 15))
    
    tab_buttons_frame = tk.Frame(tabs_frame, bg="#2d2d2d")
    tab_buttons_frame.pack(fill="x", padx=3, pady=(3, 0))
    
    stats_tab = tk.Button(tab_buttons_frame, text="Stats", bg="#3366cc", fg="white",
                         font=("Courier New", 12, "bold"), relief="raised", borderwidth=2)
    stats_tab.pack(side="left", padx=2, pady=2)
    
    info_tab = tk.Button(tab_buttons_frame, text="Info", bg="#1a1a1a", fg="white",
                        font=("Courier New", 12, "bold"), relief="flat", borderwidth=1)
    info_tab.pack(side="left", padx=2, pady=2)
    
    h2h_tab = tk.Button(tab_buttons_frame, text="H2H", bg="#1a1a1a", fg="white",
                       font=("Courier New", 12, "bold"), relief="flat", borderwidth=1)
    h2h_tab.pack(side="left", padx=2, pady=2)
    
    # 4. TAB CONTENT AREA
    tab_content = tk.Frame(tabs_frame, bg="#1a1a1a", relief="sunken", borderwidth=2)
    tab_content.pack(fill="both", expand=True, padx=3, pady=(0, 3))
    
    # Stats tab content (default)
    stats_content = tk.Frame(tab_content, bg="#1a1a1a")
    stats_content.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Info tab content (placeholder)
    info_content = tk.Frame(tab_content, bg="#1a1a1a")
    info_content.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Info content
    tk.Label(info_content, text="Date:", bg="#1a1a1a", fg="#ffffff",
             font=("Courier New", 11, "bold"), anchor="w").pack(fill="x", padx=5, pady=2)
    tk.Label(info_content, text="Old Trafford, Manchester", bg="#1a1a1a", fg=TEXT,
             font=("Courier New", 10), anchor="w").pack(fill="x", padx=5, pady=2)
    
    tk.Label(info_content, text="Stadium:", bg="#1a1a1a", fg="#ffffff",
             font=("Courier New", 11, "bold"), anchor="w").pack(fill="x", padx=5, pady=(10, 2))
    tk.Label(info_content, text="Premier League", bg="#1a1a1a", fg=TEXT,
             font=("Courier New", 10), anchor="w").pack(fill="x", padx=5, pady=2)
    
    tk.Label(info_content, text="Referee:", bg="#1a1a1a", fg="#ffffff",
             font=("Courier New", 11, "bold"), anchor="w").pack(fill="x", padx=5, pady=(10, 2))
    tk.Label(info_content, text="Michael Oliver", bg="#1a1a1a", fg=TEXT,
             font=("Courier New", 10), anchor="w").pack(fill="x", padx=5, pady=2)
    
    tk.Label(info_content, text="Competition:", bg="#1a1a1a", fg="#ffffff",
             font=("Courier New", 11, "bold"), anchor="w").pack(fill="x", padx=5, pady=(10, 2))
    tk.Label(info_content, text="Premier League 2024/25", bg="#1a1a1a", fg=TEXT,
             font=("Courier New", 10), anchor="w").pack(fill="x", padx=5, pady=2)
    
    # 5. ACTION BUTTONS ROW
    action_buttons_frame = tk.Frame(parent, bg="#2d2d2d")
    action_buttons_frame.pack(fill="x", pady=(0, 15))
    
    analyze_btn = tk.Button(action_buttons_frame, text="Analyze", bg=CYAN, fg="#001018",
                        font=("Segoe UI", 11, "bold"), relief="flat", padx=12, pady=8)
    analyze_btn.pack(side="left", padx=2, pady=2)
    
    add_watch_btn = tk.Button(action_buttons_frame, text="Add to Watchlist", bg=PURPLE, fg="white",
                        font=("Segoe UI", 10, "bold"), relief="flat", padx=12, pady=8)
    add_watch_btn.pack(side="left", padx=2, pady=2)
    
    live_start_btn = tk.Button(action_buttons_frame, text="Start Live Tracker", bg=GREEN, fg="#06110a",
                            font=("Segoe UI", 10, "bold"), relief="flat", padx=12, pady=8)
    live_start_btn.pack(side="left", padx=2, pady=2)
    
    live_stop_btn = tk.Button(action_buttons_frame, text="Stop Live Tracker", bg=RED, fg="#1a0a0a",
                           font=("Segoe UI", 10, "bold"), relief="flat", padx=12, pady=8)
    live_stop_btn.pack(side="left", padx=2, pady=2)
    
    # Store references for updating
    return {
        'home_team': home_team_label, 'away_team': away_team_label,
        'home_score': center_score_label, 'away_score': center_score_label,
        'minute': minute_label, 'status': status_label, 'edge': edge_label
    }

def create_centered_stat_row(parent, stat_name, home_val, away_val, home_color, away_color):
    """Create a centered stats comparison row."""
    row_frame = tk.Frame(parent, bg="#1a1a1a")
    row_frame.pack(fill="x", padx=15, pady=4)
    
    # Home value (left)
    home_label = tk.Label(row_frame, text=str(home_val), bg="#1a1a1a", fg=home_color,
                         font=("Courier New", 12, "bold"), width=6, anchor="e")
    home_label.pack(side="left", padx=(0, 10))
    
    # Stat name (center)
    name_label = tk.Label(row_frame, text=stat_name, bg="#1a1a1a", fg="#ffffff",
                          font=("Courier New", 12, "bold"), width=15, anchor="center")
    name_label.pack(side="left", padx=10)
    
    # Centered comparison bar
    bar_container = tk.Frame(row_frame, bg="#1a1a1a")
    bar_container.pack(side="left", padx=10)
    
    total = home_val + away_val
    if total > 0:
        home_width = int((home_val / total) * 150)  # Max width 150
        away_width = 150 - home_width
        
        # Create centered bar frame
        bar_frame = tk.Frame(bar_container, bg="#1a1a1a", width=150, height=12)
        bar_frame.pack_propagate(False)
        
        # Home bar (left side)
        home_bar = tk.Frame(bar_frame, bg=home_color, height=12)
        home_bar.place(x=0, y=0, width=home_width, height=12)
        
        # Away bar (right side)
        away_bar = tk.Frame(bar_frame, bg=away_color, height=12)
        away_bar.place(x=home_width, y=0, width=away_width, height=12)
    
    # Away value (right)
    away_label = tk.Label(row_frame, text=str(away_val), bg="#1a1a1a", fg=away_color,
                         font=("Courier New", 12, "bold"), width=6, anchor="w")
    away_label.pack(side="left", padx=(10, 0))


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
    scoreboard['minute'].config(text=f"{minute.zfill(2)}'")
    
    # Update status based on minute
    if int(minute) >= 90:
        scoreboard['status'].config(text="FT", fg=DIGITAL_RED)
    elif int(minute) >= 45:
        scoreboard['status'].config(text="LIVE", fg=DIGITAL_YELLOW)
    elif int(minute) > 0:
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
current_country = tk.StringVar(value="ALL")
current_league = tk.StringVar(value="ALL")
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
matches_listbox.bind("<KeyRelease-plus>", on_match_add_to_watchlist)
matches_listbox.bind("<KeyRelease-s>", toggle_watchlist_star)  # 's' key to toggle star
matches_listbox.bind("<KeyRelease-g>", simulate_live_goal)  # 'g' key to simulate goal

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

# CENTER COLUMN - UNIFIED MATCH ANALYSIS PANEL
_, center_body = make_card(center_col, "MATCH ANALYSIS")

# Create hidden Entry widgets for data binding (needed for match loading)
home_team = tk.Entry(center_body, width=1, bg="#1a1a1a", fg="#1a1a1a", 
                     font=("Courier New", 1), relief="flat", borderwidth=0)
away_team = tk.Entry(center_body, width=1, bg="#1a1a1a", fg="#1a1a1a", 
                     font=("Courier New", 1), relief="flat", borderwidth=0)
minute = tk.Entry(center_body, width=1, bg="#1a1a1a", fg="#1a1a1a", 
                 font=("Courier New", 1), relief="flat", borderwidth=0)
home_goals = tk.Entry(center_body, width=1, bg="#1a1a1a", fg="#1a1a1a", 
                     font=("Courier New", 1), relief="flat", borderwidth=0)
away_goals = tk.Entry(center_body, width=1, bg="#1a1a1a", fg="#1a1a1a", 
                     font=("Courier New", 1), relief="flat", borderwidth=0)

# Set initial values
set_entry(home_team, "")
set_entry(away_team, "")
set_entry(minute, "75")
set_entry(home_goals, "0")
set_entry(away_goals, "0")

# Create unified match analysis panel
scoreboard = create_unified_match_panel(center_body)



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
watch_listbox.bind("<Double-Button-1>", on_watchlist_select)

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
