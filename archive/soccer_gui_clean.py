#!/usr/bin/env python3
"""
# =============================================================================
# SOCCER EDGE ENGINE - BACKUP CLEAN VERSION
# =============================================================================
# This is a BACKUP clean version of Soccer Edge Engine project.
# Use soccer_gui.py as the main launcher instead.
# =============================================================================

import csv
from pathlib import Path
import tkinter as tk

from soccer_phase1_engine import SoccerEdgeEngine, MatchState, MarketInput
from history_logger import log_analysis, settle_match_by_index, summarize_accuracy
from watchlist import (
    add_match,
    get_watchlist,
    get_match_by_index,
    remove_match_by_index,
    clear_watchlist,
    load_watchlist,
)
from live_data import fetch_live_matches, fetch_matches_by_date, today_str, shift_date_str

HISTORY_FILE = Path(__file__).with_name("analysis_history.csv")

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

live_job = None
live_running = False
live_interval_ms = 5000

live_matches_job = None
live_matches_auto_running = False
live_matches_refresh_ms = 60000

live_matches_cache = []
match_visible_indices = []
watch_visible_indices = []

COUNTRY_ORDER = [
    "ALL",
    "England",
    "Spain",
    "Italy",
    "Germany",
    "France",
    "Portugal",
    "Netherlands",
    "Turkey",
    "Belgium",
]

TOP_LEAGUES = [
    "Premier League",
    "La Liga",
    "Serie A",
    "Bundesliga",
    "Ligue 1",
    "Primeira Liga",
    "Eredivisie",
    "Championship",
    "Belgian Pro League",
    "Süper Lig",
]

COUNTRY_TO_LEAGUES = {
    "England": [
        "Premier League",
        "Championship",
        "League One",
        "FA Cup",
        "EFL Cup",
    ],
    "Spain": [
        "La Liga",
        "Segunda División",
        "Copa del Rey",
    ],
    "Italy": [
        "Serie A",
        "Serie B",
        "Coppa Italia",
    ],
    "Germany": [
        "Bundesliga",
        "2. Bundesliga",
        "DFB Pokal",
    ],
    "France": [
        "Ligue 1",
        "Ligue 2",
        "Coupe de France",
    ],
    "Portugal": [
        "Primeira Liga",
        "Taça de Portugal",
        "League Cup",
    ],
    "Netherlands": [
        "Eredivisie",
        "Eerste Divisie",
        "KNVB Beker",
    ],
    "Turkey": [
        "Süper Lig",
        "1. Lig",
        "Turkish Cup",
    ],
    "Belgium": [
        "Belgian Pro League",
        "Challenger Pro League",
        "Belgian Cup",
    ],
}


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


def get_selected_country():
    sel = countries_listbox.curselection()
    if sel:
        return countries_listbox.get(sel[0])
    return "ALL"


def get_selected_league():
    sel = leagues_listbox.curselection()
    if sel:
        return leagues_listbox.get(sel[0])
    return "ALL"


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
        elif edge.startswith("+"):
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
    minute_val = minute.get() or "0"
    
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


def refresh_watchlist_panel():
    global watch_visible_indices

    watch_listbox.delete(0, tk.END)
    watch_visible_indices = []

    data = get_watchlist()
    query = watch_search_var.get().strip().lower()

    filtered = []
    for idx, m in enumerate(data):
        hay = f"{m['home']} {m['away']}".lower()
        if query and query not in hay:
            continue
        filtered.append((idx, m))

    if not filtered:
        watch_listbox.insert(tk.END, "No matches in watchlist.")
        return

    for idx, m in filtered:
        match = f"{m['home']} vs {m['away']}"
        score = f"{m['home_goals']}-{m['away_goals']}"
        line = f"{idx} | {match} | {m['minute']}' | {score}"
        watch_visible_indices.append(idx)
        watch_listbox.insert(tk.END, line)


def refresh_country_panel():
    countries_listbox.delete(0, tk.END)
    for name in COUNTRY_ORDER:
        countries_listbox.insert(tk.END, name)

    if countries_listbox.size() > 0:
        countries_listbox.selection_clear(0, tk.END)
        countries_listbox.selection_set(0)
        countries_listbox.activate(0)


def refresh_league_panel():
    leagues_listbox.delete(0, tk.END)

    selected_country = get_selected_country()

    if selected_country == "ALL":
        leagues = ["ALL"] + TOP_LEAGUES
    else:
        leagues = ["ALL"] + COUNTRY_TO_LEAGUES.get(selected_country, [])

    for lg in leagues:
        leagues_listbox.insert(tk.END, lg)

    if leagues_listbox.size() > 0:
        leagues_listbox.selection_clear(0, tk.END)
        leagues_listbox.selection_set(0)
        leagues_listbox.activate(0)


def refresh_matches_panel():
    global match_visible_indices

    matches_listbox.delete(0, tk.END)
    match_visible_indices = []

    query = match_search_var.get().strip().lower()
    selected_country = get_selected_country()
    selected_league = get_selected_league()

    filtered = []
    for idx, m in enumerate(live_matches_cache):
        league_name = (m.get("league") or "")
        home = (m.get("home") or "")
        away = (m.get("away") or "")
        hay = f"{home} {away} {league_name}".lower()

        if query and query not in hay:
            continue

        if selected_league != "ALL" and league_name != selected_league:
            continue

        if selected_country != "ALL":
            allowed = COUNTRY_TO_LEAGUES.get(selected_country, [])
            if league_name not in allowed:
                continue

        filtered.append((idx, m))

    if not filtered:
        matches_listbox.insert(tk.END, "No matches loaded.")
        return

    for idx, m in filtered:
        line = (
            f"{idx} | {m['home']} vs {m['away']} | "
            f"{m['minute']}' | {m['home_goals']}-{m['away_goals']} | "
            f"{m['league']}"
        )
        match_visible_indices.append(idx)
        matches_listbox.insert(tk.END, line)


def on_match_search_change(*args):
    refresh_matches_panel()


def on_watch_search_change(*args):
    refresh_watchlist_panel()


def on_country_select(event):
    sel = countries_listbox.curselection()
    if not sel:
        return

    refresh_league_panel()
    refresh_matches_panel()
    tracker_status.config(text=f"Country selected: {get_selected_country()}", fg=MUTED)


def on_league_select(event):
    refresh_matches_panel()
    tracker_status.config(text=f"League selected: {get_selected_league()}", fg=MUTED)


def set_summary(rec_text="—", conf_text="—", edge_text="—", color=MUTED):
    rec_value.config(text=rec_text, fg=color)
    conf_value.config(text=conf_text, fg=color)
    edge_value.config(text=edge_text, fg=color)


def set_entry(entry_widget, value):
    entry_widget.delete(0, tk.END)
    entry_widget.insert(0, str(value))


def update_alert_panel(best_label=None, best_edge=None, confidence=None):
    alert_box.config(state="normal")
    alert_box.delete("1.0", tk.END)

    if best_label is None:
        alert_box.insert(tk.END, "No alerts yet. Analyze a match to check signals.", "muted")
        alert_box.config(state="disabled")
        return

    if best_edge >= 25:
        alert_box.insert(tk.END, "HIGH VALUE ALERT\n", "alert")
        alert_box.insert(
            tk.END,
            f"Recommendation: {best_label}\nConfidence: {confidence}\nBest Edge: {best_edge:+.1f}c\n",
            "white",
        )
    elif best_edge >= 8:
        alert_box.insert(tk.END, "VALUE ALERT\n", "header")
        alert_box.insert(
            tk.END,
            f"Recommendation: {best_label}\nConfidence: {confidence}\nBest Edge: {best_edge:+.1f}c\n",
            "white",
        )
    elif best_edge > 0:
        alert_box.insert(tk.END, "SMALL EDGE\n", "header")
        alert_box.insert(
            tk.END,
            f"Recommendation: {best_label}\nConfidence: {confidence}\nBest Edge: {best_edge:+.1f}c\n",
            "white",
        )
    else:
        alert_box.insert(tk.END, "NO ACTION\n", "red")
        alert_box.insert(
            tk.END,
            f"Recommendation: {best_label}\nConfidence: {confidence}\nBest Edge: {best_edge:+.1f}c\n",
            "white",
        )

    alert_box.config(state="disabled")


def on_watchlist_select(event):
    try:
        selection = watch_listbox.curselection()
        if not selection:
            return

        display_idx = selection[0]
        if display_idx >= len(watch_visible_indices):
            return

        actual_idx = watch_visible_indices[display_idx]
        m = get_match_by_index(actual_idx)
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

        tracker_status.config(text=f"Loaded watchlist match #{actual_idx}.", fg=GREEN)
        update_digital_scoreboard()

    except Exception as e:
        tracker_status.config(text=f"Watchlist load error: {e}", fg=RED)


def on_match_select(event):
    try:
        selection = matches_listbox.curselection()
        if not selection:
            return

        display_idx = selection[0]
        if display_idx >= len(match_visible_indices):
            return

        actual_idx = match_visible_indices[display_idx]
        m = live_matches_cache[actual_idx]

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

        tracker_status.config(text=f"Match selected: {m['home']} vs {m['away']}.", fg=GREEN)
        update_digital_scoreboard()

    except Exception as e:
        tracker_status.config(text=f"Match selection error: {e}", fg=RED)


def add_current_match():
    try:
        m = {
            "home": home_team.get().strip(),
            "away": away_team.get().strip(),
            "minute": int(minute.get() or 0),
            "home_goals": int(home_goals.get() or 0),
            "away_goals": int(away_goals.get() or 0),
            "stoppage": int(stoppage_minutes.get() or 0),
            "home_reds": int(home_red_cards.get() or 0),
            "away_reds": int(away_red_cards.get() or 0),
            "pressure": float(pressure_bias.get() or 0),
            "draw_price": float(draw_price.get() or 40),
            "under_price": float(under_price.get() or 45),
            "over_price": float(over_price.get() or 60),
        }

        if not m["home"] or not m["away"]:
            tracker_status.config(text="Both team names required.", fg=RED)
            return

        add_match(m)
        refresh_watchlist_panel()
        tracker_status.config(text="Match added to watchlist.", fg=GREEN)

    except Exception as e:
        tracker_status.config(text=f"Add to watchlist error: {e}", fg=RED)


def remove_selected_watchlist_match():
    try:
        selection = watch_listbox.curselection()
        if not selection:
            tracker_status.config(text="No match selected in watchlist.", fg=RED)
            return

        display_idx = selection[0]
        if display_idx >= len(watch_visible_indices):
            tracker_status.config(text="Invalid watchlist selection.", fg=RED)
            return

        actual_idx = watch_visible_indices[display_idx]
        remove_match_by_index(actual_idx)
        refresh_watchlist_panel()
        tracker_status.config(text=f"Removed match #{actual_idx} from watchlist.", fg=GREEN)

    except Exception as e:
        tracker_status.config(text=f"Remove watchlist error: {e}", fg=RED)


def clear_all_watchlist():
    try:
        clear_watchlist()
        refresh_watchlist_panel()
        tracker_status.config(text="Watchlist cleared.", fg=GREEN)

    except Exception as e:
        tracker_status.config(text=f"Clear watchlist error: {e}", fg=RED)


def load_live_matches():
    try:
        data = fetch_live_matches()
        if not data:
            tracker_status.config(text="No live matches available.", fg=MUTED)
            return

        live_matches_cache.clear()
        live_matches_cache.extend(data)
        refresh_matches_panel()
        tracker_status.config(text=f"Loaded {len(data)} live matches.", fg=GREEN)

    except Exception as e:
        tracker_status.config(text=f"Load matches error: {e}", fg=RED)


def start_live_matches_auto_refresh():
    global live_matches_job, live_matches_auto_running

    if live_matches_auto_running:
        tracker_status.config(text="Auto-refresh already running.", fg=MUTED)
        return

    live_matches_auto_running = True
    load_live_matches()
    live_auto_status.config(text="Match list auto-refresh ON", fg=GREEN)
    live_matches_auto_refresh_tick()


def stop_live_matches_auto_refresh():
    global live_matches_job, live_matches_auto_running

    live_matches_auto_running = False
    if live_matches_job:
        root.after_cancel(live_matches_job)
        live_matches_job = None

    live_auto_status.config(text="Match list auto-refresh OFF", fg=MUTED)


def live_matches_auto_refresh_tick():
    global live_matches_job, live_matches_auto_running

    if not live_matches_auto_running:
        return

    try:
        load_live_matches()
        live_matches_job = root.after(live_matches_refresh_ms, live_matches_auto_refresh_tick)

    except Exception as e:
        tracker_status.config(text=f"Auto-refresh error: {e}", fg=RED)
        stop_live_matches_auto_refresh()


def calculate_analysis(log_to_history=True):
    try:
        state = MatchState(
            home_team=home_team.get().strip(),
            away_team=away_team.get().strip(),
            minute=int(minute.get() or 0),
            home_goals=int(home_goals.get() or 0),
            away_goals=int(away_goals.get() or 0),
            stoppage=int(stoppage_minutes.get() or 0),
            home_reds=int(home_red_cards.get() or 0),
            away_reds=int(away_red_cards.get() or 0),
            pressure=float(pressure_bias.get() or 0),
        )

        market = MarketInput(
            draw_price=float(draw_price.get() or 40),
            under_price=float(under_price.get() or 45),
            over_price=float(over_price.get() or 60),
        )

        engine = SoccerEdgeEngine()
        result = engine.analyze(state, market)

        best_label = result.recommendation
        best_edge = result.best_edge
        confidence = result.confidence
        scored_rows = result.scored_rows

        if log_to_history:
            log_analysis(state, market, result)

        write_analysis_to_panels(state, market, scored_rows, best_label, best_edge, confidence, engine)
        update_digital_scoreboard()
        refresh_history_panel()
        refresh_accuracy_panel()
        update_alert_panel()

    except Exception as e:
        tracker_status.config(text=f"Analysis error: {e}", fg=RED)


def run_analysis():
    tracker_status.config(text="Analyzing match...", fg=MUTED)
    calculate_analysis(log_to_history=True)


def live_tick():
    global live_job, live_running

    if not live_running:
        return

    try:
        current_minute = int(minute.get() or 0)
        if current_minute < 120:
            set_entry(minute, current_minute + 1)

        calculate_analysis(log_to_history=False)
        update_digital_scoreboard()
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
    global live_running

    if live_running:
        tracker_status.config(text="Live tracker already running.", fg=MUTED)
        return

    live_running = True
    live_tick()
    tracker_status.config(text="Live tracker started.", fg=GREEN)


def stop_live_tracker():
    global live_job, live_running

    live_running = False
    if live_job:
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


def write_analysis_to_panels(state, market, scored_rows, best_label, best_edge, confidence, engine):
    model_box.config(state="normal")
    model_box.delete("1.0", tk.END)

    model_box.insert(tk.END, "MATCH ANALYSIS REPORT\n", "header")
    model_box.insert(tk.END, "=" * 50 + "\n", "header")

    model_box.insert(tk.END, f"Match: {state.home_team} vs {state.away_team}\n", "white")
    model_box.insert(tk.END, f"Minute: {state.minute}' | Score: {state.home_goals}-{state.away_goals}\n", "white")
    model_box.insert(tk.END, f"Pressure Bias: {state.pressure:+.1f}\n", "white")
    model_box.insert(tk.END, "\n", "white")

    model_box.insert(tk.END, "MARKET PRICES\n", "header")
    model_box.insert(tk.END, "-" * 20 + "\n", "header")
    model_box.insert(tk.END, f"Draw: {market.draw_price:.1f}c\n", "white")
    model_box.insert(tk.END, f"Under 2.5: {market.under_price:.1f}c\n", "white")
    model_box.insert(tk.END, f"Over 2.5: {market.over_price:.1f}c\n", "white")
    model_box.insert(tk.END, "\n", "white")

    model_box.insert(tk.END, "PROBABILITY MODEL\n", "header")
    model_box.insert(tk.END, "-" * 20 + "\n", "header")
    
    for row in scored_rows:
        outcome = row["outcome"]
        prob = row["probability"]
        edge = row["edge"]
        color = "green" if edge > 0 else "red"
        
        model_box.insert(tk.END, f"{outcome}: {prob:.1f}% | Edge: {edge:+.1f}c\n", color)
    
    model_box.insert(tk.END, "\n", "white")
    model_box.insert(tk.END, "RECOMMENDATION\n", "header")
    model_box.insert(tk.END, "-" * 20 + "\n", "header")
    
    rec_color = "green" if best_edge > 0 else "red"
    model_box.insert(tk.END, f"Bet: {best_label}\n", rec_color)
    model_box.insert(tk.END, f"Confidence: {confidence}%\n", rec_color)
    model_box.insert(tk.END, f"Best Edge: {best_edge:+.1f}c\n", rec_color)
    
    model_box.insert(tk.END, "\n", "white")
    model_box.insert(tk.END, "EDGE CLASSIFICATION\n", "header")
    model_box.insert(tk.END, "-" * 20 + "\n", "header")
    model_box.insert(tk.END, f"{classify_edge(best_edge)}\n", "white")

    model_box.config(state="disabled")


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
    outer.pack(fill="both", expand=False, padx=8, pady=8)

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


root = tk.Tk()
root.title("Soccer Edge Engine — Dynamic Country/League")
root.geometry("1450x1040")
root.configure(bg=BG)

match_search_var = tk.StringVar()
watch_search_var = tk.StringVar()
match_search_var.trace_add("write", on_match_search_change)
watch_search_var.trace_add("write", on_watch_search_change)

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

main = tk.Frame(root, bg=BG)
main.pack(fill="both", expand=True, padx=12, pady=6)

for i in range(3):
    main.grid_columnconfigure(i, weight=1, uniform="cols")
main.grid_rowconfigure(0, weight=1)

left_col = tk.Frame(main, bg=BG)
left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

center_col = tk.Frame(main, bg=BG)
center_col.grid(row=0, column=1, sticky="nsew", padx=6)

right_col = tk.Frame(main, bg=BG)
right_col.grid(row=0, column=2, sticky="nsew", padx=(6, 0))

# LEFT COLUMN
_, countries_body = make_card(left_col, "COUNTRIES")
countries_listbox = tk.Listbox(
    countries_body,
    height=6,
    width=36,
    bg=CARD2,
    fg=TEXT,
    font=("Consolas", 10),
    relief="flat",
    highlightthickness=0,
    selectbackground=PURPLE_HOVER,
    selectforeground="white",
)
countries_listbox.pack(fill="both", expand=True, padx=10, pady=10)
countries_listbox.bind("<<ListboxSelect>>", on_country_select)

_, leagues_body = make_card(left_col, "LEAGUES")
leagues_listbox = tk.Listbox(
    leagues_body,
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
leagues_listbox.pack(fill="both", expand=True, padx=10, pady=10)
leagues_listbox.bind("<<ListboxSelect>>", on_league_select)

_, matches_body = make_card(left_col, "MATCHES")

match_search_frame = tk.Frame(matches_body, bg=CARD)
match_search_frame.pack(fill="x", padx=10, pady=(8, 0))

tk.Label(
    match_search_frame,
    text="Search Matches:",
    bg=CARD,
    fg=TEXT,
    font=("Segoe UI", 10),
).pack(side="left")

match_search_entry = tk.Entry(
    match_search_frame,
    textvariable=match_search_var,
    bg=CARD2,
    fg=TEXT,
    insertbackground=TEXT,
    relief="flat",
    font=("Segoe UI", 10),
)
match_search_entry.pack(side="left", fill="x", expand=True, padx=(8, 0), ipady=4)

matches_listbox = tk.Listbox(
    matches_body,
    height=16,
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
matches_listbox.bind("<<ListboxSelect>>", on_match_select)

_, watch_body = make_card(left_col, "WATCHLIST")

watch_search_frame = tk.Frame(watch_body, bg=CARD)
watch_search_frame.pack(fill="x", padx=10, pady=(8, 0))

tk.Label(
    watch_search_frame,
    text="Search Watchlist:",
    bg=CARD,
    fg=TEXT,
    font=("Segoe UI", 10),
).pack(side="left")

watch_search_entry = tk.Entry(
    watch_search_frame,
    textvariable=watch_search_var,
    bg=CARD2,
    fg=TEXT,
    insertbackground=TEXT,
    relief="flat",
    font=("Segoe UI", 10),
)
watch_search_entry.pack(side="left", fill="x", expand=True, padx=(8, 0), ipady=4)

watch_listbox = tk.Listbox(
    watch_body,
    height=10,
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
watch_listbox.bind("<<ListboxSelect>>", on_watchlist_select)

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

button_row_1 = tk.Frame(input_body, bg=CARD)
button_row_1.pack(fill="x", padx=10, pady=(12, 4))

button_row_2 = tk.Frame(input_body, bg=CARD)
button_row_2.pack(fill="x", padx=10, pady=4)

button_row_3 = tk.Frame(input_body, bg=CARD)
button_row_3.pack(fill="x", padx=10, pady=4)

analyze_btn = tk.Button(
    button_row_1,
    text="Analyze",
    command=run_analysis,
    bg=CYAN,
    fg="#001018",
    font=("Segoe UI", 10, "bold"),
    relief="flat",
    padx=10,
    pady=8,
)
analyze_btn.pack(side="left", fill="x", expand=True, padx=4)

add_watch_btn = tk.Button(
    button_row_1,
    text="Add to Watchlist",
    command=add_current_match,
    bg=PURPLE,
    fg="white",
    font=("Segoe UI", 10, "bold"),
    relief="flat",
    padx=10,
    pady=8,
)
add_watch_btn.pack(side="left", fill="x", expand=True, padx=4)

remove_watch_btn = tk.Button(
    button_row_1,
    text="Remove Selected",
    command=remove_selected_watchlist_match,
    bg=GOLD,
    fg="#1a1a1a",
    font=("Segoe UI", 10, "bold"),
    relief="flat",
    padx=10,
    pady=8,
)
remove_watch_btn.pack(side="left", fill="x", expand=True, padx=4)

clear_watch_btn = tk.Button(
    button_row_2,
    text="Clear Watchlist",
    command=clear_all_watchlist,
    bg="#475569",
    fg="white",
    font=("Segoe UI", 10, "bold"),
    relief="flat",
    padx=10,
    pady=8,
)
clear_watch_btn.pack(side="left", fill="x", expand=True, padx=4)

load_live_btn = tk.Button(
    button_row_2,
    text="Load Matches",
    command=load_live_matches,
    bg=GOLD,
    fg="#1a1a1a",
    font=("Segoe UI", 10, "bold"),
    relief="flat",
    padx=10,
    pady=8,
)
load_live_btn.pack(side="left", fill="x", expand=True, padx=4)

start_live_list_btn = tk.Button(
    button_row_2,
    text="Start Match Refresh",
    command=start_live_matches_auto_refresh,
    bg=PURPLE,
    fg="white",
    font=("Segoe UI", 10, "bold"),
    relief="flat",
    padx=10,
    pady=8,
)
start_live_list_btn.pack(side="left", fill="x", expand=True, padx=4)

stop_live_list_btn = tk.Button(
    button_row_3,
    text="Stop Match Refresh",
    command=stop_live_matches_auto_refresh,
    bg="#475569",
    fg="white",
    font=("Segoe UI", 10, "bold"),
    relief="flat",
    padx=10,
    pady=8,
)
stop_live_list_btn.pack(side="left", fill="x", expand=True, padx=4)

live_start_btn = tk.Button(
    button_row_3,
    text="Start Match Tracker",
    command=start_live_tracker,
    bg=GREEN,
    fg="#06110a",
    font=("Segoe UI", 10, "bold"),
    relief="flat",
    padx=10,
    pady=8,
)
live_start_btn.pack(side="left", fill="x", expand=True, padx=4)

live_stop_btn = tk.Button(
    button_row_3,
    text="Stop Match Tracker",
    command=stop_live_tracker,
    bg=RED,
    fg="#1a0a0a",
    font=("Segoe UI", 10, "bold"),
    relief="flat",
    padx=10,
    pady=8,
)
live_stop_btn.pack(side="left", fill="x", expand=True, padx=4)

live_auto_status = tk.Label(
    input_body,
    text="Match list auto-refresh OFF",
    bg=CARD,
    fg=MUTED,
    font=("Segoe UI", 9),
    anchor="w",
)
live_auto_status.pack(fill="x", padx=10, pady=(6, 2))

tracker_status = tk.Label(
    input_body,
    text="Use left navigation to select a match.",
    bg=CARD,
    fg=MUTED,
    font=("Segoe UI", 9),
    anchor="w",
)
tracker_status.pack(fill="x", padx=10, pady=(2, 12))

_, settle_body = make_card(center_col, "SETTLE SELECTED MATCH")
settle_index = create_input(settle_body, "History Row Index")
final_home_goals = create_input(settle_body, "Final Home Goals")
final_away_goals = create_input(settle_body, "Final Away Goals")

settle_btn = tk.Button(
    settle_body,
    text="Settle Selected Match",
    command=settle_selected,
    bg=GOLD,
    fg="#1a1a1a",
    font=("Segoe UI", 10, "bold"),
    relief="flat",
    padx=12,
    pady=10,
)
settle_btn.pack(fill="x", padx=10, pady=10)

settle_status = tk.Label(
    settle_body,
    text="Enter row index from history below.",
    bg=CARD,
    fg=MUTED,
    font=("Segoe UI", 9),
    anchor="w",
)
settle_status.pack(fill="x", padx=10, pady=(0, 10))

# RIGHT COLUMN
_, alert_body = make_card(right_col, "PREDICTION / ALERTS")
alert_box = tk.Text(
    alert_body,
    height=7,
    width=36,
    bg=CARD2,
    fg=TEXT,
    insertbackground=TEXT,
    font=("Consolas", 10),
    relief="flat",
    wrap=tk.WORD,
)
alert_box.pack(fill="x", padx=10, pady=10)

alert_box.tag_config("header", foreground=CYAN, font=("Consolas", 10, "bold"))
alert_box.tag_config("alert", foreground=RED, font=("Consolas", 10, "bold"))
alert_box.tag_config("white", foreground=TEXT)
alert_box.tag_config("muted", foreground=MUTED)
alert_box.config(state="disabled")

_, result_body = make_card(right_col, "MATCH CENTER")

model_frame = tk.Frame(result_body, bg=CARD)
model_frame.pack(fill="both", expand=True, padx=10, pady=10)

model_box = tk.Text(
    model_frame,
    height=25,
    width=36,
    bg=CARD2,
    fg=TEXT,
    insertbackground=TEXT,
    font=("Consolas", 9),
    relief="flat",
    wrap=tk.WORD,
)
model_box.pack(fill="both", expand=True)

model_box.tag_config("header", foreground=CYAN, font=("Consolas", 9, "bold"))
model_box.tag_config("white", foreground=TEXT)
model_box.tag_config("green", foreground=GREEN)
model_box.tag_config("red", foreground=RED)
model_box.tag_config("muted", foreground=MUTED)

_, history_body = make_card(right_col, "HISTORY")
history_box = tk.Text(
    history_body,
    height=10,
    width=36,
    bg=CARD2,
    fg=TEXT,
    insertbackground=TEXT,
    font=("Consolas", 9),
    relief="flat",
    wrap=tk.WORD,
)
history_box.pack(fill="x", padx=10, pady=10)

history_box.tag_config("header", foreground=CYAN, font=("Consolas", 9, "bold"))
history_box.tag_config("white", foreground=TEXT)
history_box.tag_config("green", foreground=GREEN)
history_box.tag_config("red", foreground=RED)
history_box.tag_config("muted", foreground=MUTED)
history_box.config(state="disabled")

_, accuracy_body = make_card(right_col, "ACCURACY")
accuracy_box = tk.Text(
    accuracy_body,
    height=8,
    width=36,
    bg=CARD2,
    fg=TEXT,
    insertbackground=TEXT,
    font=("Consolas", 9),
    relief="flat",
    wrap=tk.WORD,
)
accuracy_box.pack(fill="x", padx=10, pady=10)

accuracy_box.tag_config("header", foreground=CYAN, font=("Consolas", 9, "bold"))
accuracy_box.tag_config("white", foreground=TEXT)
accuracy_box.config(state="disabled")

# Initialize panels
load_watchlist()
refresh_country_panel()
refresh_league_panel()
refresh_watchlist_panel()
refresh_history_panel()
refresh_accuracy_panel()
update_alert_panel()
update_digital_scoreboard()
set_summary()

root.mainloop()
