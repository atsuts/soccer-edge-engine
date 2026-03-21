import csv
from pathlib import Path
import tkinter as tk
from soccer_phase1_engine import SoccerEdgeEngine, MatchState, MarketInput
from history_logger import log_analysis, settle_match_by_index, summarize_accuracy
from watchlist import add_match, get_watchlist, get_match_by_index


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

main = tk.Frame(root, bg=BG)
main.pack(fill="both", expand=True, padx=12, pady=6)

left = tk.Frame(main, bg=BG)
left.pack(side="left", fill="y", padx=(0, 8))

right = tk.Frame(main, bg=BG)
right.pack(side="right", fill="both", expand=True)

_, input_body = make_card(left, "MATCH INPUTS")

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

_, settle_body = make_card(left, "SETTLE SELECTED MATCH")
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

_, result_body = make_card(right, "MODEL OUTPUT")
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

_, profile_body = make_card(right, "TEAM PROFILES")
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

_, watch_body = make_card(right, "WATCHLIST")
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

_, history_body = make_card(right, "RECENT HISTORY")
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

_, accuracy_body = make_card(right, "ACCURACY DASHBOARD")
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