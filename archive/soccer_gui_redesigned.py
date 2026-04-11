#!/usr/bin/env python3
"""
# =============================================================================
# SOCCER EDGE ENGINE - OLD REDESIGNED VERSION
# =============================================================================
# This is an OLD redesigned version of Soccer Edge Engine project.
# Use soccer_gui.py as the main launcher instead.
# =============================================================================

import csv
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk
from soccer_phase1_engine import SoccerEdgeEngine, MatchState, MarketInput
from history_logger import log_analysis, settle_match_by_index, summarize_accuracy
from watchlist import add_match, get_watchlist, get_match_by_index
import json
from datetime import datetime, timedelta

HISTORY_FILE = Path(__file__).with_name("analysis_history.csv")
TEAM_DATA_FILE = Path(__file__).with_name("team_data.json")

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
BLUE = "#3b82f6"
ORANGE = "#f97316"
BORDER = "#374151"

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


def load_history_rows(limit: int = 50):
    if not HISTORY_FILE.exists():
        return []

    with open(HISTORY_FILE, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    return rows[-limit:]


def load_team_data():
    """Load comprehensive team data from JSON file."""
    if not TEAM_DATA_FILE.exists():
        # Create default team data structure
        default_data = {
            "teams": {},
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(TEAM_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=2)
        return default_data
    
    with open(TEAM_DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_team_data(data):
    """Save team data to JSON file."""
    data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(TEAM_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_team_comprehensive_data(team_name: str):
    """Get comprehensive data for a team including form, injuries, etc."""
    data = load_team_data()
    teams = data.get("teams", {})
    
    if team_name not in teams:
        # Create default team entry
        teams[team_name] = {
            "current_form": [],
            "injuries": [],
            "suspensions": [],
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "home_form": {"played": 0, "won": 0, "draw": 0, "lost": 0, "goals_for": 0, "goals_against": 0},
            "away_form": {"played": 0, "won": 0, "draw": 0, "lost": 0, "goals_for": 0, "goals_against": 0},
            "media_sentiment": "neutral",
            "weather_impact": "unknown"
        }
        save_team_data(data)
    
    return teams[team_name]


def update_team_form(team_name: str, result: str, goals_for: int, goals_against: int, is_home: bool):
    """Update team form after a match."""
    data = load_team_data()
    teams = data.get("teams", {})
    
    if team_name not in teams:
        get_team_comprehensive_data(team_name)
        teams = data.get("teams", {})
    
    team_data = teams[team_name]
    
    # Update current form (keep last 5)
    form_entry = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "result": result,  # "W", "D", "L"
        "goals_for": goals_for,
        "goals_against": goals_against,
        "is_home": is_home
    }
    
    team_data["current_form"].append(form_entry)
    if len(team_data["current_form"]) > 5:
        team_data["current_form"].pop(0)
    
    # Update home/away form
    form_key = "home_form" if is_home else "away_form"
    form_stats = team_data[form_key]
    form_stats["played"] += 1
    form_stats["goals_for"] += goals_for
    form_stats["goals_against"] += goals_against
    
    if result == "W":
        form_stats["won"] += 1
    elif result == "D":
        form_stats["draw"] += 1
    else:
        form_stats["lost"] += 1
    
    team_data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    save_team_data(data)


def refresh_statistics_panel():
    """Refresh the left statistics panel."""
    stats_box.config(state="normal")
    stats_box.delete("1.0", tk.END)
    
    # Overall accuracy
    accuracy_stats = summarize_accuracy()
    
    stats_box.insert(tk.END, "📊 OVERALL STATISTICS\n", "header")
    stats_box.insert(tk.END, "=" * 30 + "\n", "header")
    stats_box.insert(tk.END, f"Total Analyses: {accuracy_stats['total_settled']}\n", "white")
    stats_box.insert(tk.END, f"Hit Rate: {accuracy_stats['recommended_hit_rate']:.1f}%\n", 
                   "green" if accuracy_stats['recommended_hit_rate'] >= 50 else "red")
    stats_box.insert(tk.END, f"Draw Rate: {accuracy_stats['draw_hit_rate']:.1f}%\n", "white")
    stats_box.insert(tk.END, f"Under Rate: {accuracy_stats['under_hit_rate']:.1f}%\n", "white")
    stats_box.insert(tk.END, f"Over Rate: {accuracy_stats['over_hit_rate']:.1f}%\n", "white")
    
    stats_box.insert(tk.END, "\n", "white")
    
    # Edge distribution
    rows = load_history_rows(limit=100)
    if rows:
        edges = []
        for row in rows:
            try:
                edge_str = row.get("best_edge", "0")
                edge_val = float(edge_str.replace("+", "").replace("c", ""))
                edges.append(edge_val)
            except:
                continue
        
        if edges:
            high_value = sum(1 for e in edges if e >= 25)
            value = sum(1 for e in edges if 8 <= e < 25)
            small = sum(1 for e in edges if 0 < e < 8)
            negative = sum(1 for e in edges if e <= 0)
            
            stats_box.insert(tk.END, "🎯 EDGE DISTRIBUTION\n", "header")
            stats_box.insert(tk.END, "=" * 30 + "\n", "header")
            stats_box.insert(tk.END, f"High Value (≥25c): {high_value}\n", "green")
            stats_box.insert(tk.END, f"Value (8-24c): {value}\n", "cyan")
            stats_box.insert(tk.END, f"Small (0-7c): {small}\n", "yellow")
            stats_box.insert(tk.END, f"Negative/Avoid: {negative}\n", "red")
    
    stats_box.insert(tk.END, "\n", "white")
    
    # Recent performance
    recent_rows = [r for r in rows if r.get("settled", "0") == "1"][-10:]
    if recent_rows:
        recent_hits = sum(1 for r in recent_rows if r.get("recommended_hit") == "1")
        recent_rate = (recent_hits / len(recent_rows)) * 100
        
        stats_box.insert(tk.END, "📈 RECENT PERFORMANCE\n", "header")
        stats_box.insert(tk.END, "=" * 30 + "\n", "header")
        stats_box.insert(tk.END, f"Last 10 Hit Rate: {recent_rate:.1f}%\n", 
                       "green" if recent_rate >= 50 else "red")
        
        # Best performing market
        draw_hits = sum(1 for r in recent_rows if r.get("actual_draw") == "1")
        under_hits = sum(1 for r in recent_rows if r.get("actual_under_2_5") == "1")
        over_hits = sum(1 for r in recent_rows if r.get("actual_over_2_5") == "1")
        
        best_market = max([("Draw", draw_hits), ("Under", under_hits), ("Over", over_hits)], 
                          key=lambda x: x[1])
        
        stats_box.insert(tk.END, f"Best Market: {best_market[0]} ({best_market[1]}/10)\n", "gold")
    
    stats_box.config(state="disabled")


def refresh_match_intelligence_panel():
    """Refresh the middle match intelligence panel."""
    intelligence_box.config(state="normal")
    intelligence_box.delete("1.0", tk.END)
    
    home = home_team.get().strip()
    away = away_team.get().strip()
    
    if not home or not away:
        intelligence_box.insert(tk.END, "⚽ MATCH INTELLIGENCE CENTER\n", "header")
        intelligence_box.insert(tk.END, "=" * 40 + "\n", "header")
        intelligence_box.insert(tk.END, "Enter team names to see match intelligence...\n", "muted")
        intelligence_box.config(state="disabled")
        return
    
    intelligence_box.insert(tk.END, "⚽ MATCH INTELLIGENCE CENTER\n", "header")
    intelligence_box.insert(tk.END, "=" * 40 + "\n", "header")
    
    # Current match state
    minute_val = minute.get() or "0"
    home_goals_val = home_goals.get() or "0"
    away_goals_val = away_goals.get() or "0"
    
    intelligence_box.insert(tk.END, f"\n🏆 CURRENT MATCH STATE\n", "subheader")
    intelligence_box.insert(tk.END, "-" * 25 + "\n", "subheader")
    intelligence_box.insert(tk.END, f"{home} {home_goals_val} - {away_goals_val} {away}\n", "white")
    intelligence_box.insert(tk.END, f"Minute: {minute_val}\n", "white")
    
    # Team data for both teams
    home_data = get_team_comprehensive_data(home)
    away_data = get_team_comprehensive_data(away)
    
    # Team form analysis
    intelligence_box.insert(tk.END, f"\n📊 TEAM FORM ANALYSIS\n", "subheader")
    intelligence_box.insert(tk.END, "-" * 25 + "\n", "subheader")
    
    # Home team form
    home_form = home_data.get("current_form", [])
    if home_form:
        home_recent = "".join([f["result"] for f in home_form[-5:]])
        home_points = sum(3 if f["result"] == "W" else 1 if f["result"] == "D" else 0 for f in home_form[-5:])
        intelligence_box.insert(tk.END, f"{home} (Last 5): {home_recent} ({home_points} pts)\n", "white")
    else:
        intelligence_box.insert(tk.END, f"{home}: No recent form data\n", "muted")
    
    # Away team form
    away_form = away_data.get("current_form", [])
    if away_form:
        away_recent = "".join([f["result"] for f in away_form[-5:]])
        away_points = sum(3 if f["result"] == "W" else 1 if f["result"] == "D" else 0 for f in away_form[-5:])
        intelligence_box.insert(tk.END, f"{away} (Last 5): {away_recent} ({away_points} pts)\n", "white")
    else:
        intelligence_box.insert(tk.END, f"{away}: No recent form data\n", "muted")
    
    # Head-to-head (simplified - would need separate H2H database)
    intelligence_box.insert(tk.END, f"\n⚔️ HEAD-TO-HEAD\n", "subheader")
    intelligence_box.insert(tk.END, "-" * 25 + "\n", "subheader")
    intelligence_box.insert(tk.END, "H2H data not available yet\n", "muted")
    
    # Team status
    intelligence_box.insert(tk.END, f"\n🏥 TEAM STATUS\n", "subheader")
    intelligence_box.insert(tk.END, "-" * 25 + "\n", "subheader")
    
    home_injuries = home_data.get("injuries", [])
    away_injuries = away_data.get("injuries", [])
    
    intelligence_box.insert(tk.END, f"{home} Injuries: {len(home_injuries)} players\n", 
                   "red" if home_injuries else "green")
    intelligence_box.insert(tk.END, f"{away} Injuries: {len(away_injuries)} players\n", 
                   "red" if away_injuries else "green")
    
    # Environmental factors
    intelligence_box.insert(tk.END, f"\n🌍 ENVIRONMENTAL FACTORS\n", "subheader")
    intelligence_box.insert(tk.END, "-" * 25 + "\n", "subheader")
    intelligence_box.insert(tk.END, f"Venue: {home} (Home advantage)\n", "white")
    intelligence_box.insert(tk.END, f"Weather: {home_data.get('weather_impact', 'Unknown')}\n", "muted")
    intelligence_box.insert(tk.END, f"Media Sentiment: {home_data.get('media_sentiment', 'Neutral')}\n", "muted")
    
    intelligence_box.config(state="disabled")


def refresh_prediction_panel():
    """Refresh the right prediction panel."""
    prediction_box.config(state="normal")
    prediction_box.delete("1.0", tk.END)
    
    prediction_box.insert(tk.END, "🎯 PREDICTION ENGINE\n", "header")
    prediction_box.insert(tk.END, "=" * 30 + "\n", "header")
    
    # Get current analysis if available
    try:
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
        
        engine = SoccerEdgeEngine()
        results = engine.full_analysis(state, market)
        
        # Display predictions
        prediction_box.insert(tk.END, f"\n📈 MODEL PREDICTIONS\n", "subheader")
        prediction_box.insert(tk.END, "-" * 25 + "\n", "subheader")
        prediction_box.insert(tk.END, f"Draw Probability: {results['draw_prob']:.1%}\n", "white")
        prediction_box.insert(tk.END, f"Under 2.5: {results['under_prob']:.1%}\n", "white")
        prediction_box.insert(tk.END, f"Over 2.5: {results['over_prob']:.1%}\n", "white")
        
        # Market comparison
        prediction_box.insert(tk.END, f"\n💰 MARKET COMPARISON\n", "subheader")
        prediction_box.insert(tk.END, "-" * 25 + "\n", "subheader")
        
        markets = [
            ("Draw", results["draw_prob"], market.draw_cents),
            ("Under 2.5", results["under_prob"], market.under_cents),
            ("Over 2.5", results["over_prob"], market.over_cents),
        ]
        
        best_edge = -999
        best_market = ""
        
        for label, prob, price in markets:
            model_cents = engine.fair_cents(prob)
            edge = model_cents - price
            signal = classify_edge(edge)
            
            color = "green" if edge > 0 else "red"
            prediction_box.insert(tk.END, f"{label}: {edge:+.1f}c ({signal})\n", color)
            
            if edge > best_edge:
                best_edge = edge
                best_market = label
        
        # Recommendation
        prediction_box.insert(tk.END, f"\n🎯 RECOMMENDATION\n", "subheader")
        prediction_box.insert(tk.END, "-" * 25 + "\n", "subheader")
        prediction_box.insert(tk.END, f"Best: {best_market}\n", "gold")
        prediction_box.insert(tk.END, f"Edge: {best_edge:+.1f}c\n", "gold")
        
        confidence = "HIGH" if best_edge >= 25 else "MEDIUM" if best_edge >= 8 else "LOW"
        conf_color = "green" if confidence == "HIGH" else "yellow" if confidence == "MEDIUM" else "red"
        prediction_box.insert(tk.END, f"Confidence: {confidence}\n", conf_color)
        
        # Factor analysis
        prediction_box.insert(tk.END, f"\n🔍 FACTOR ANALYSIS\n", "subheader")
        prediction_box.insert(tk.END, "-" * 25 + "\n", "subheader")
        
        # Team strength factors
        home_profile = engine.get_team_profile(state.home_team)
        away_profile = engine.get_team_profile(state.away_team)
        
        prediction_box.insert(tk.END, f"Home Attack: {home_profile['attack']:.2f}\n", "white")
        prediction_box.insert(tk.END, f"Away Defense: {away_profile['defense']:.2f}\n", "white")
        prediction_box.insert(tk.END, f"Draw Bias: {(home_profile['draw'] + away_profile['draw'])/2:.2f}\n", "white")
        
        # Match context
        prediction_box.insert(tk.END, f"\n📊 MATCH CONTEXT\n", "subheader")
        prediction_box.insert(tk.END, "-" * 25 + "\n", "subheader")
        prediction_box.insert(tk.END, f"Minute: {state.minute} (", "white")
        
        if state.minute < 45:
            prediction_box.insert(tk.END, "Early", "cyan")
        elif state.minute < 75:
            prediction_box.insert(tk.END, "Mid", "yellow")
        else:
            prediction_box.insert(tk.END, "Late", "red")
        
        prediction_box.insert(tk.END, ")\n", "white")
        
        red_cards = state.home_red_cards + state.away_red_cards
        if red_cards > 0:
            prediction_box.insert(tk.END, f"Red Cards: {red_cards} (Impact!)\n", "red")
        else:
            prediction_box.insert(tk.END, f"Red Cards: None\n", "green")
        
        prediction_box.insert(tk.END, f"Pressure: {state.pressure_bias:+d}\n", "white")
        
    except Exception as e:
        prediction_box.insert(tk.END, f"\n❌ Analysis Error\n", "subheader")
        prediction_box.insert(tk.END, "-" * 25 + "\n", "subheader")
        prediction_box.insert(tk.END, f"Error: {str(e)}\n", "red")
        prediction_box.insert(tk.END, "Check input values and try again\n", "muted")
    
    prediction_box.config(state="disabled")


def set_entry(entry_widget, value):
    entry_widget.delete(0, tk.END)
    entry_widget.insert(0, str(value))


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

    # Update all panels
    refresh_statistics_panel()
    refresh_match_intelligence_panel()
    refresh_prediction_panel()


def run_analysis():
    try:
        calculate_analysis(log_to_history=True)
        status_label.config(text="Analysis complete!", fg=GREEN)
    except Exception as e:
        status_label.config(text=f"Analysis error: {e}", fg=RED)


def live_tick():
    global live_job, live_running

    if not live_running:
        return

    try:
        current_minute = int(minute.get() or 0)
        if current_minute < 120:
            set_entry(minute, current_minute + 1)

        calculate_analysis(log_to_history=False)
        status_label.config(
            text=f"Live tracking - Minute {minute.get()}",
            fg=GREEN,
        )
    except Exception as e:
        status_label.config(text=f"Live tracker error: {e}", fg=RED)
        live_running = False
        return

    live_job = root.after(live_interval_ms, live_tick)


def start_live_tracker():
    global live_job, live_running

    if live_running:
        status_label.config(text="Live tracker already running", fg=MUTED)
        return

    live_running = True
    status_label.config(text="Live tracker started", fg=GREEN)
    live_tick()


def stop_live_tracker():
    global live_job, live_running

    live_running = False
    if live_job is not None:
        root.after_cancel(live_job)
        live_job = None

    status_label.config(text="Live tracker stopped", fg=MUTED)


def settle_selected():
    try:
        idx = int(settle_index.get())
        fh = int(final_home_goals.get() or 0)
        fa = int(final_away_goals.get() or 0)

        ok = settle_match_by_index(idx, fh, fa)
        if ok:
            status_label.config(text=f"Settled row {idx}", fg=GREEN)
            # Update team forms based on result
            rows = load_history_rows()
            if idx < len(rows):
                row = rows[idx]
                home = row.get("home_team", "")
                away = row.get("away_team", "")
                
                # Determine results
                if fh > fa:
                    home_result, away_result = "W", "L"
                elif fh == fa:
                    home_result, away_result = "D", "D"
                else:
                    home_result, away_result = "L", "W"
                
                # Update team forms
                update_team_form(home, home_result, fh, fa, True)
                update_team_form(away, away_result, fa, fh, False)
        else:
            status_label.config(text="Invalid index or no history", fg=RED)

        refresh_statistics_panel()
        refresh_match_intelligence_panel()
        refresh_prediction_panel()

    except Exception as e:
        status_label.config(text=f"Settle error: {e}", fg=RED)


def create_input(parent, label_text):
    frame = tk.Frame(parent, bg=CARD)
    frame.pack(fill="x", pady=4)

    label = tk.Label(
        frame,
        text=label_text,
        width=20,
        anchor="w",
        bg=CARD,
        fg=TEXT,
        font=("Segoe UI", 10),
    )
    label.pack(side="left")

    entry = tk.Entry(
        frame,
        width=15,
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
    outer.pack(fill="both", expand=False, padx=8, pady=6)

    title_label = tk.Label(
        outer,
        text=title,
        bg=BG,
        fg=CYAN,
        font=("Segoe UI", 12, "bold"),
        anchor="w",
    )
    title_label.pack(fill="x", padx=8, pady=(8, 4))

    body = tk.Frame(outer, bg=CARD)
    body.pack(fill="both", expand=True, padx=6, pady=(0, 6))

    return outer, body


# Main Window
root = tk.Tk()
root.title("Soccer Edge Engine — Comprehensive Intelligence System")
root.geometry("1400x900")
root.configure(bg=BG)

# Top Bar
topbar = tk.Frame(root, bg=BG)
topbar.pack(fill="x", padx=12, pady=(12, 8))

title = tk.Label(
    topbar,
    text="⚽ SOCCER EDGE ENGINE — INTELLIGENCE SYSTEM",
    font=("Segoe UI", 18, "bold"),
    bg=BG,
    fg=TEXT,
)
title.pack(side="left")

status_label = tk.Label(
    topbar,
    text="Ready",
    bg=BG,
    fg=MUTED,
    font=("Segoe UI", 10),
)
status_label.pack(side="right", padx=20)

# Main Container
main_container = tk.Frame(root, bg=BG)
main_container.pack(fill="both", expand=True, padx=12, pady=8)

# Three Panel Layout
# LEFT PANEL - Statistics
left_panel = tk.Frame(main_container, bg=BG)
left_panel.pack(side="left", fill="both", expand=True, padx=(0, 6))

_, stats_body = make_card(left_panel, "📊 STATISTICS HUB")
stats_box = tk.Text(
    stats_body,
    width=35,
    height=40,
    bg=CARD2,
    fg=TEXT,
    insertbackground=TEXT,
    font=("Consolas", 9),
    relief="flat",
    wrap="word",
)
stats_box.pack(fill="both", expand=True, padx=6, pady=6)

stats_box.tag_configure("header", foreground=CYAN, font=("Consolas", 10, "bold"))
stats_box.tag_configure("subheader", foreground=GOLD, font=("Consolas", 9, "bold"))
stats_box.tag_configure("white", foreground=TEXT)
stats_box.tag_configure("green", foreground=GREEN)
stats_box.tag_configure("red", foreground=RED)
stats_box.tag_configure("cyan", foreground=CYAN)
stats_box.tag_configure("yellow", foreground=GOLD)
stats_box.tag_configure("muted", foreground=MUTED)
stats_box.config(state="disabled")

# MIDDLE PANEL - Match Intelligence
middle_panel = tk.Frame(main_container, bg=BG)
middle_panel.pack(side="left", fill="both", expand=True, padx=6)

# Match Input Section
_, input_body = make_card(middle_panel, "🎮 MATCH INPUT")

# Create two columns for inputs
input_grid = tk.Frame(input_body, bg=CARD)
input_grid.pack(fill="x", padx=10, pady=8)

# Left column
left_inputs = tk.Frame(input_grid, bg=CARD)
left_inputs.pack(side="left", fill="both", expand=True, padx=(0, 10))

home_team = create_input(left_inputs, "Home Team")
away_team = create_input(left_inputs, "Away Team")
minute = create_input(left_inputs, "Minute")
home_goals = create_input(left_inputs, "Home Goals")
away_goals = create_input(left_inputs, "Away Goals")

# Right column
right_inputs = tk.Frame(input_grid, bg=CARD)
right_inputs.pack(side="right", fill="both", expand=True)

stoppage_minutes = create_input(right_inputs, "Stoppage")
home_red_cards = create_input(right_inputs, "Home Reds")
away_red_cards = create_input(right_inputs, "Away Reds")
pressure_bias = create_input(right_inputs, "Pressure")
draw_price = create_input(right_inputs, "Draw Price")

# Market prices row
market_row = tk.Frame(input_body, bg=CARD)
market_row.pack(fill="x", padx=10, pady=(0, 8))

under_price = create_input(market_row, "Under Price")
over_price = create_input(market_row, "Over Price")

# Set default values
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

# Buttons
button_frame = tk.Frame(input_body, bg=CARD)
button_frame.pack(fill="x", padx=10, pady=(0, 8))

analyze_btn = tk.Button(
    button_frame,
    text="🔍 Analyze Match",
    command=run_analysis,
    bg=CYAN,
    fg="#001018",
    font=("Segoe UI", 11, "bold"),
    relief="flat",
    padx=15,
    pady=8,
)
analyze_btn.pack(side="left", padx=(0, 5))

live_start_btn = tk.Button(
    button_frame,
    text="▶️ Live",
    command=start_live_tracker,
    bg=GREEN,
    fg="white",
    font=("Segoe UI", 10, "bold"),
    relief="flat",
    padx=10,
    pady=8,
)
live_start_btn.pack(side="left", padx=5)

live_stop_btn = tk.Button(
    button_frame,
    text="⏹️ Stop",
    command=stop_live_tracker,
    bg=RED,
    fg="white",
    font=("Segoe UI", 10, "bold"),
    relief="flat",
    padx=10,
    pady=8,
)
live_stop_btn.pack(side="left", padx=5)

# Match Intelligence Display
_, intelligence_body = make_card(middle_panel, "🧠 MATCH INTELLIGENCE CENTER")
intelligence_box = tk.Text(
    intelligence_body,
    width=50,
    height=20,
    bg=CARD2,
    fg=TEXT,
    insertbackground=TEXT,
    font=("Consolas", 9),
    relief="flat",
    wrap="word",
)
intelligence_box.pack(fill="both", expand=True, padx=6, pady=6)

intelligence_box.tag_configure("header", foreground=CYAN, font=("Consolas", 10, "bold"))
intelligence_box.tag_configure("subheader", foreground=GOLD, font=("Consolas", 9, "bold"))
intelligence_box.tag_configure("white", foreground=TEXT)
intelligence_box.tag_configure("green", foreground=GREEN)
intelligence_box.tag_configure("red", foreground=RED)
intelligence_box.tag_configure("muted", foreground=MUTED)
intelligence_box.config(state="disabled")

# Settlement Section
_, settle_body = make_card(middle_panel, "⚖️ SETTLEMENT")
settle_frame = tk.Frame(settle_body, bg=CARD)
settle_frame.pack(fill="x", padx=6, pady=6)

settle_inputs = tk.Frame(settle_frame, bg=CARD)
settle_inputs.pack(fill="x", pady=(0, 5))

settle_index = create_input(settle_inputs, "Row Index")
final_home_goals = create_input(settle_inputs, "Final Home")
final_away_goals = create_input(settle_inputs, "Final Away")

settle_btn_frame = tk.Frame(settle_frame, bg=CARD)
settle_btn_frame.pack(fill="x")

settle_btn = tk.Button(
    settle_btn_frame,
    text="⚡ Settle Match",
    command=settle_selected,
    bg=GOLD,
    fg="#1a1a1a",
    font=("Segoe UI", 10, "bold"),
    relief="flat",
    padx=15,
    pady=6,
)
settle_btn.pack(side="left")

# RIGHT PANEL - Prediction Engine
right_panel = tk.Frame(main_container, bg=BG)
right_panel.pack(side="right", fill="both", expand=True, padx=(6, 0))

_, prediction_body = make_card(right_panel, "🎯 PREDICTION ENGINE")
prediction_box = tk.Text(
    prediction_body,
    width=40,
    height=35,
    bg=CARD2,
    fg=TEXT,
    insertbackground=TEXT,
    font=("Consolas", 9),
    relief="flat",
    wrap="word",
)
prediction_box.pack(fill="both", expand=True, padx=6, pady=6)

prediction_box.tag_configure("header", foreground=CYAN, font=("Consolas", 10, "bold"))
prediction_box.tag_configure("subheader", foreground=GOLD, font=("Consolas", 9, "bold"))
prediction_box.tag_configure("white", foreground=TEXT)
prediction_box.tag_configure("green", foreground=GREEN)
prediction_box.tag_configure("red", foreground=RED)
prediction_box.tag_configure("yellow", foreground=GOLD)
prediction_box.tag_configure("cyan", foreground=CYAN)
prediction_box.config(state="disabled")

# Initialize panels
refresh_statistics_panel()
refresh_match_intelligence_panel()
refresh_prediction_panel()

root.mainloop()
