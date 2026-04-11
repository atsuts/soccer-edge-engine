#!/usr/bin/env python3
"""
# =============================================================================
# SOCCER EDGE ENGINE - WORKING VERSION
# =============================================================================
# This is a working version of Soccer Edge Engine project.
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


def write_analysis_to_panels(state, market, scored_rows, best_label, best_edge, confidence, engine):
    summary_color = GREEN if best_edge > 0 else RED
    set_summary(best_label, confidence, f"{best_edge:+.1f}c", summary_color)
    update_alert_panel(best_label, best_edge, confidence)

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
                "best_edge": best_edge,
                "confidence": confidence,
            }
        )

    write_analysis_to_panels(state, market, scored_rows, best_label, best_edge, confidence, engine)


def run_analysis():
    try:
        calculate_analysis(log_to_history=True)
        tracker_status.config(text="Analysis complete. Check results and alerts.", fg=GREEN)
    except Exception as e:
        tracker_status.config(text=f"Analysis error: {e}", fg=RED)


def add_current_match():
    try:
        add_match(
            {
                "home_team": home_team.get(),
                "away_team": away_team.get(),
                "minute": minute.get(),
                "home_goals": home_goals.get(),
                "away_goals": away_goals.get(),
                "stoppage": stoppage_minutes.get(),
                "home_reds": home_red_cards.get(),
                "away_reds": away_red_cards.get(),
                "pressure": pressure_bias.get(),
                "draw_price": draw_price.get(),
                "under_price": under_price.get(),
                "over_price": over_price.get(),
            }
        )
        tracker_status.config(text="Added to watchlist.", fg=GREEN)
    except Exception as e:
        tracker_status.config(text=f"Watchlist error: {e}", fg=RED)


def settle_selected():
    try:
        idx = int(settle_index.get())
        settle_match_by_index(idx)
        refresh_history_panel()
        refresh_accuracy_panel()
        tracker_status.config(text=f"Settled match #{idx}.", fg=GREEN)
    except Exception as e:
        tracker_status.config(text=f"Settle error: {e}", fg=RED)


def start_live_tracker():
    global live_job, live_running

    if live_running:
        tracker_status.config(text="Live tracker already running.", fg=MUTED)
        return

    live_running = True
    tracker_status.config(text="Live tracker started.", fg=GREEN)
    live_job = root.after(live_interval_ms, live_tick)


def live_tick():
    global live_job, live_running

    if not live_running:
        return

    try:
        minute_val = int(minute.get())
        if minute_val < 90:
            minute.set(minute_val + 1)
    except Exception as e:
        tracker_status.config(text=f"Tracker error: {e}", fg=RED)

    if live_running:
        live_job = root.after(live_interval_ms, live_tick)


def stop_live_tracker():
    global live_job, live_running

    live_running = False
    if live_job is not None:
        root.after_cancel(live_job)
        live_job = None

    tracker_status.config(text="Live tracker stopped.", fg=MUTED)


def create_input(parent, label):
    frame = tk.Frame(parent, bg=CARD)
    frame.pack(fill="x", padx=10, pady=(0, 5))

    tk.Label(frame, text=label, bg=CARD, fg=TEXT, font=("Segoe UI", 9)).pack(anchor="w")

    entry = tk.Entry(frame, bg=CARD2, fg=TEXT, insertbackground=TEXT, font=("Segoe UI", 10), relief="flat")
    entry.pack(fill="x", pady=(2, 0))

    return entry


def make_card(parent, title):
    frame = tk.Frame(parent, bg=BG)
    frame.pack(fill="both", expand=True, padx=6, pady=6)

    header = tk.Frame(frame, bg=CARD)
    header.pack(fill="x")

    tk.Label(header, text=title, bg=CARD, fg=CYAN, font=("Segoe UI", 12, "bold")).pack(pady=(10, 5))

    body = tk.Frame(frame, bg=CARD)
    body.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    return frame, body


def create_digital_scoreboard(parent):
    """Create a realistic digital scoreboard display."""
    # Main scoreboard frame with realistic styling
    scoreboard_frame = tk.Frame(parent, bg="#2d2d2d", relief="ridge", borderwidth=3)
    scoreboard_frame.pack(fill="x", padx=10, pady=(0, 15))
    
    # Inner frame for depth effect
    inner_frame = tk.Frame(scoreboard_frame, bg="#1a1a1a", relief="sunken", borderwidth=2)
    inner_frame.pack(fill="x", padx=3, pady=3)
    
    # Top row - Team Names with realistic styling
    teams_frame = tk.Frame(inner_frame, bg="#1a1a1a")
    teams_frame.pack(fill="x", pady=(12, 3))
    
    home_team_label = tk.Label(
        teams_frame,
        text="HOME",
        bg="#1a1a1a",
        fg="#3366cc",
        font=("Courier New", 22, "bold"),
        width=12,
        anchor="e",
        relief="flat"
    )
    home_team_label.pack(side="left", expand=True, padx=(25, 8))
    
    vs_label = tk.Label(
        teams_frame,
        text="VS",
        bg="#1a1a1a",
        fg="#ffaa00",
        font=("Courier New", 18, "bold"),
        width=4
    )
    vs_label.pack(side="left", padx=8)
    
    away_team_label = tk.Label(
        teams_frame,
        text="AWAY",
        bg="#1a1a1a",
        fg="#cc3333",
        font=("Courier New", 22, "bold"),
        width=12,
        anchor="w",
        relief="flat"
    )
    away_team_label.pack(side="left", expand=True, padx=(8, 25))
    
    # Score row with larger, more prominent numbers
    score_frame = tk.Frame(inner_frame, bg="#1a1a1a")
    score_frame.pack(fill="x", pady=3)
    
    home_score_label = tk.Label(
        score_frame,
        text="0",
        bg="#0a0a0a",
        fg="#3366cc",
        font=("Courier New", 68, "bold"),
        width=3,
        relief="sunken",
        borderwidth=2
    )
    home_score_label.pack(side="left", expand=True, padx=(25, 8))
    
    dash_label = tk.Label(
        score_frame,
        text="-",
        bg="#1a1a1a",
        fg="#ff6b35",
        font=("Courier New", 44, "bold"),
        width=2
    )
    dash_label.pack(side="left", padx=8)
    
    away_score_label = tk.Label(
        score_frame,
        text="0",
        bg="#0a0a0a",
        fg="#cc3333",
        font=("Courier New", 68, "bold"),
        width=3,
        relief="sunken",
        borderwidth=2
    )
    away_score_label.pack(side="left", expand=True, padx=(8, 25))
    
    # Bottom row - Match info with compact layout
    info_frame = tk.Frame(inner_frame, bg="#1a1a1a")
    info_frame.pack(fill="x", pady=(3, 12))
    
    minute_label = tk.Label(
        info_frame,
        text="00'",
        bg="#1a1a1a",
        fg="#ff6b35",
        font=("Courier New", 16, "bold"),
        width=4,
        relief="flat"
    )
    minute_label.pack(side="left", padx=(25, 8))
    
    status_label = tk.Label(
        info_frame,
        text="NS",
        bg="#1a1a1a",
        fg="#ffaa00",
        font=("Courier New", 14, "bold"),
        width=4,
        relief="flat"
    )
    status_label.pack(side="left", padx=8)
    
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
    """Update digital scoreboard with current match data."""
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
        scoreboard['status'].config(text="FT", fg="#cc3333")
    elif int(minute_val) >= 45:
        scoreboard['status'].config(text="LIVE", fg="#ffaa00")
    elif int(minute_val) > 0:
        scoreboard['status'].config(text="1H", fg="#ff6b35")
    else:
        scoreboard['status'].config(text="NS", fg="#ff6b35")


def main():
    """Main entry point for Soccer Edge Engine GUI."""
    try:
        # Basic GUI setup
        load_watchlist()
        refresh_history_panel()
        refresh_accuracy_panel()
        update_alert_panel()
        update_digital_scoreboard()
        set_summary()
        root.mainloop()
    except Exception as e:
        print(f"Error starting Soccer Edge Engine: {e}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()
