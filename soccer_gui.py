import csv
import re
from pathlib import Path
import tkinter as tk
from tkinter import ttk

from soccer_phase1_engine import SoccerEdgeEngine, MatchState, MarketInput
from history_logger import log_analysis, summarize_accuracy
from watchlist import add_match


APP_DIR = Path(__file__).resolve().parent
HISTORY_FILE = APP_DIR / "analysis_history.csv"

BG = "#0b1120"
TOP = "#111827"
PANEL = "#1e293b"
PANEL_DARK = "#0f172a"
ROW = "#141d30"
ROW_ALT = "#192437"
BORDER = "#334155"
TEXT = "#f8fafc"
MUTED = "#94a3b8"
CYAN = "#22d3ee"
CYAN_DARK = "#0891b2"
GREEN = "#22c55e"
GREEN_DARK = "#16a34a"
RED = "#ef4444"
RED_DARK = "#dc2626"
ORANGE = "#f97316"
PURPLE = "#6366f1"
GRAY_BTN = "#475569"
YELLOW = "#facc15"

FONT_UI = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_MONO = ("Consolas", 10)
FONT_MONO_SMALL = ("Consolas", 9)


MATCHES = [
    {
        "id": 1,
        "country": "England",
        "league": "Premier League",
        "tournament": "Premier League",
        "status": "LIVE",
        "minute": 67,
        "home": "Man City",
        "away": "Liverpool",
        "home_score": 1,
        "away_score": 1,
        "edge": -0.2,
        "odds": (1.94, 6.50, 4.50),
        "pred": (30, 25, 45),
        "date": "Saturday, 11 April 2026",
        "venue": "Etihad Stadium",
        "referee": "Michael Oliver",
        "home_form": ["W", "W", "L", "D", "W"],
        "away_form": ["W", "L", "W", "W", "D"],
        "home_avg": 2.1,
        "away_avg": 1.8,
        "draw_price": 40.0,
        "under_price": 45.0,
        "over_price": 60.0,
    },
    {
        "id": 2,
        "country": "England",
        "league": "Premier League",
        "tournament": "Premier League",
        "status": "LIVE",
        "minute": 45,
        "home": "Arsenal",
        "away": "Chelsea",
        "home_score": 1,
        "away_score": 0,
        "edge": 5.7,
        "odds": (1.80, 3.30, 6.00),
        "pred": (29, 31, 40),
        "date": "Saturday, 11 April 2026",
        "venue": "Emirates Stadium",
        "referee": "Anthony Taylor",
        "home_form": ["W", "D", "W", "W", "L"],
        "away_form": ["L", "W", "D", "W", "W"],
        "home_avg": 1.9,
        "away_avg": 1.4,
        "draw_price": 36.0,
        "under_price": 52.0,
        "over_price": 49.0,
    },
    {
        "id": 3,
        "country": "England",
        "league": "Premier League",
        "tournament": "Premier League",
        "status": "UP",
        "minute": 0,
        "home": "Man United",
        "away": "Newcastle",
        "home_score": 0,
        "away_score": 0,
        "edge": 2.8,
        "odds": (4.70, 3.90, 4.00),
        "pred": (25, 30, 20),
        "date": "Saturday, 11 April 2026",
        "venue": "Old Trafford",
        "referee": "Paul Tierney",
        "home_form": ["D", "W", "L", "W", "D"],
        "away_form": ["W", "W", "D", "L", "W"],
        "home_avg": 1.6,
        "away_avg": 1.5,
        "draw_price": 39.0,
        "under_price": 55.0,
        "over_price": 44.0,
    },
    {
        "id": 4,
        "country": "Spain",
        "league": "La Liga",
        "tournament": "La Liga",
        "status": "UP",
        "minute": 0,
        "home": "Real Madrid",
        "away": "Barcelona",
        "home_score": 0,
        "away_score": 0,
        "edge": -3.1,
        "odds": (2.80, 4.60, 5.80),
        "pred": (28, 32, 20),
        "date": "Saturday, 11 April 2026",
        "venue": "Santiago Bernabeu",
        "referee": "Jose Sanchez",
        "home_form": ["W", "W", "W", "D", "L"],
        "away_form": ["W", "L", "W", "W", "W"],
        "home_avg": 2.3,
        "away_avg": 2.0,
        "draw_price": 42.0,
        "under_price": 48.0,
        "over_price": 54.0,
    },
    {
        "id": 5,
        "country": "Spain",
        "league": "La Liga",
        "tournament": "La Liga",
        "status": "UP",
        "minute": 0,
        "home": "Atletico M",
        "away": "Sevilla",
        "home_score": 0,
        "away_score": 0,
        "edge": 3.9,
        "odds": (1.40, 5.00, 5.80),
        "pred": (24, 30, 18),
        "date": "Saturday, 11 April 2026",
        "venue": "Metropolitano",
        "referee": "Alejandro Hernandez",
        "home_form": ["W", "D", "W", "L", "W"],
        "away_form": ["D", "L", "W", "D", "L"],
        "home_avg": 1.7,
        "away_avg": 1.1,
        "draw_price": 38.0,
        "under_price": 58.0,
        "over_price": 42.0,
    },
    {
        "id": 6,
        "country": "Italy",
        "league": "Serie A",
        "tournament": "Serie A",
        "status": "UP",
        "minute": 0,
        "home": "Juventus",
        "away": "AC Milan",
        "home_score": 0,
        "away_score": 0,
        "edge": 6.8,
        "odds": (2.00, 3.90, 7.20),
        "pred": (18, 30, 20),
        "date": "Saturday, 11 April 2026",
        "venue": "Allianz Stadium",
        "referee": "Daniele Orsato",
        "home_form": ["W", "W", "D", "W", "W"],
        "away_form": ["L", "W", "D", "W", "D"],
        "home_avg": 1.8,
        "away_avg": 1.3,
        "draw_price": 35.0,
        "under_price": 60.0,
        "over_price": 40.0,
    },
    {
        "id": 7,
        "country": "Italy",
        "league": "Serie A",
        "tournament": "Serie A",
        "status": "UP",
        "minute": 0,
        "home": "Inter Milan",
        "away": "Napoli",
        "home_score": 0,
        "away_score": 0,
        "edge": 8.7,
        "odds": (1.70, 4.60, 7.80),
        "pred": (14, 18, 8),
        "date": "Saturday, 11 April 2026",
        "venue": "San Siro",
        "referee": "Marco Guida",
        "home_form": ["W", "W", "W", "D", "W"],
        "away_form": ["W", "D", "L", "W", "L"],
        "home_avg": 2.2,
        "away_avg": 1.4,
        "draw_price": 37.0,
        "under_price": 50.0,
        "over_price": 51.0,
    },
    {
        "id": 8,
        "country": "Germany",
        "league": "Bundesliga",
        "tournament": "Bundesliga",
        "status": "UP",
        "minute": 0,
        "home": "Bayern Mun",
        "away": "Dortmund",
        "home_score": 0,
        "away_score": 0,
        "edge": -3.5,
        "odds": (1.75, 5.40, 6.50),
        "pred": (20, 15, 34),
        "date": "Saturday, 11 April 2026",
        "venue": "Allianz Arena",
        "referee": "Felix Zwayer",
        "home_form": ["W", "W", "L", "W", "W"],
        "away_form": ["D", "W", "W", "L", "W"],
        "home_avg": 2.6,
        "away_avg": 1.9,
        "draw_price": 34.0,
        "under_price": 44.0,
        "over_price": 62.0,
    },
]

HISTORY_SAMPLE = [
    ("19", "08:14:15", "Home vs Away", "UNDER 2.5", 5.3, "NO"),
    ("8", "19:26:32", "Junior vs Bucaramanga", "UNDER 2.5", 6.7, "NO"),
    ("7", "19:19:15", "Guayaquil City FC vs L", "UNDER 2.5", 6.7, "NO"),
    ("6", "18:18:46", "Home vs Away", "DRAW", 5.3, "NO"),
    ("5", "03:13:59", "Home vs Away", "UNDER 2.5", 5.3, "NO"),
]


TOP_COUNTRIES = ["England", "Spain", "Italy", "Germany", "France"]
ALL_COUNTRIES = [
    "Argentina",
    "Australia",
    "Austria",
    "Belgium",
    "Brazil",
    "Chile",
    "Colombia",
    "Croatia",
    "Denmark",
    "England",
    "France",
    "Germany",
    "Greece",
    "Italy",
    "Japan",
    "Mexico",
    "Netherlands",
    "Norway",
    "Poland",
    "Portugal",
    "Saudi Arabia",
    "Scotland",
    "Spain",
    "Sweden",
    "Switzerland",
    "Turkey",
    "United States",
    "Uruguay",
]

TOP_LEAGUES = [
    "Premier League",
    "La Liga",
    "Serie A",
    "Bundesliga",
    "Ligue 1",
    "Champions League",
    "Europa League",
    "Eredivisie",
    "Primeira Liga",
    "MLS",
]
ALL_LEAGUES = [
    "2. Bundesliga",
    "A-League",
    "Allsvenskan",
    "Belgian Pro League",
    "Brasileirao",
    "Bundesliga",
    "Championship",
    "Champions League",
    "EFL League One",
    "Eredivisie",
    "Europa League",
    "J1 League",
    "La Liga",
    "Liga MX",
    "Ligue 1",
    "MLS",
    "Premier League",
    "Primeira Liga",
    "Saudi Pro League",
    "Scottish Premiership",
    "Serie A",
    "Super Lig",
    "Swiss Super League",
]

COUNTRY_LEAGUES = {
    "England": [
        "Premier League",
        "Championship",
        "EFL League One",
        "EFL League Two",
        "FA Cup",
        "EFL Cup",
        "National League",
    ],
    "Germany": [
        "Bundesliga",
        "2. Bundesliga",
        "3. Liga",
        "DFB Pokal",
        "Regionalliga",
    ],
    "Spain": [
        "La Liga",
        "Segunda Division",
        "Copa del Rey",
        "Primera Federacion",
    ],
    "Italy": [
        "Serie A",
        "Serie B",
        "Serie C",
        "Coppa Italia",
    ],
    "France": [
        "Ligue 1",
        "Ligue 2",
        "Coupe de France",
        "National",
    ],
    "United States": [
        "MLS",
        "USL Championship",
        "US Open Cup",
        "NWSL",
    ],
}

MAIN_TOURNAMENTS = [
    "Premier League",
    "Champions League",
    "Europa League",
    "FA Cup",
    "Copa del Rey",
    "Coppa Italia",
    "DFB Pokal",
    "Copa Libertadores",
    "World Cup Qualifiers",
]

DATE_FILTERS = ["All", "Live", "Today", "Tomorrow", "This Week", "Weekend", "Upcoming"]


def preferred_order(top_items, all_items):
    ordered = ["All"]
    seen = set(ordered)
    for item in top_items:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    for item in sorted(all_items):
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered


class SoccerEdgeApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SOCCER EDGE ENGINE")
        self.root.geometry("1500x780")
        self.root.minsize(1200, 680)
        self.root.configure(bg=BG)

        self.engine = SoccerEdgeEngine()
        self.current_match = MATCHES[0]
        self.watchlist_ids = set()
        self.tracker_job = None
        self.tracker_running = False
        self.tab_name = tk.StringVar(value="Stats Replay")

        self.filters = {
            "country": tk.StringVar(value="All"),
            "league": tk.StringVar(value="All"),
            "tournament": tk.StringVar(value="All"),
            "date": tk.StringVar(value="Today"),
        }

        self.score_labels = {}
        self.meta_labels = {}
        self.watch_body = None
        self.accuracy_body = None
        self.odds_body = None
        self.predictions_body = None
        self.selected_odds_book = None
        self.selected_prediction_source = None
        self.selected_player_detail = None
        self.replay_minute = None
        self.replay_job = None
        self.replay_running = False
        self.replay_start_minute = None
        self.replay_slider = None
        self.replay_refresh = None
        self.replay_max_minute = 0
        self.quick_query = tk.StringVar(value="")
        self.chat_message = tk.StringVar(value="")
        self.guest_handle = tk.StringVar(value="Guest001")
        self.guest_market = tk.StringVar(value="1X2")
        self.guest_pick = tk.StringVar(value="")
        self.match_chats = {}
        self.match_chat_room = {}
        self.match_challenges = {}
        self.challenge_history = []
        self.center_split = None
        self.center_split_initialized = False
        self.recommendation_body = None
        self.quality_body = None
        self.source_body = None
        self.chat_preview_body = None
        self.filter_combos = {}
        self.matches_frame = None
        self.matches_canvas = None
        self.watchlist_frame = None
        self.watchlist_canvas = None
        self.status_label = None
        self.tracker_status = None

        self.configure_styles()
        self.build_ui()
        self.challenge_history = self.seed_challenge_history()
        self.select_match(self.current_match, refresh=False)

    def configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Dark.TCombobox",
            fieldbackground=PANEL_DARK,
            background=PANEL_DARK,
            foreground=TEXT,
            arrowcolor=TEXT,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
            padding=3,
        )
        style.map(
            "Dark.TCombobox",
            fieldbackground=[("readonly", PANEL_DARK)],
            foreground=[("readonly", TEXT)],
        )

    def build_ui(self):
        topbar = tk.Frame(self.root, bg=TOP, height=62)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        tk.Label(
            topbar,
            text="SOCCER EDGE ENGINE",
            bg=TOP,
            fg="#7dd3fc",
            font=("Consolas", 18, "bold"),
            anchor="w",
        ).pack(side="left", padx=8)

        tk.Button(
            topbar,
            text="Test Speed",
            bg="#334155",
            fg=TEXT,
            activebackground="#475569",
            activeforeground=TEXT,
            relief="flat",
            font=FONT_SMALL,
            padx=12,
            command=self.test_speed,
        ).pack(side="right", padx=14)

        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True)
        main.grid_columnconfigure(0, weight=35, uniform="dash")
        main.grid_columnconfigure(1, weight=40, uniform="dash")
        main.grid_columnconfigure(2, weight=25, uniform="dash")
        main.grid_rowconfigure(0, weight=1)

        left = tk.Frame(main, bg=BG)
        center = tk.Frame(main, bg=BG)
        right = tk.Frame(main, bg=BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        center.grid(row=0, column=1, sticky="nsew", padx=4)
        right.grid(row=0, column=2, sticky="nsew", padx=(6, 0))

        self.build_left(left)
        self.build_center(center)
        self.build_right(right)

    def build_left(self, parent):
        parent.grid_rowconfigure(3, weight=7)
        parent.grid_rowconfigure(4, weight=3)
        parent.grid_columnconfigure(0, weight=1)

        self.status_label = tk.Label(
            parent,
            text="Last Load: --  |  Matches: --",
            bg=PANEL,
            fg=MUTED,
            font=FONT_MONO_SMALL,
            anchor="w",
            padx=8,
        )
        self.status_label.grid(row=0, column=0, sticky="ew", pady=(8, 6))

        filters = tk.Frame(parent, bg=PANEL)
        filters.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        for col in range(4):
            filters.grid_columnconfigure(col, weight=1)

        self.add_filter(filters, "COUNTRY", "country", preferred_order(TOP_COUNTRIES, ALL_COUNTRIES), height=18)
        self.add_filter(filters, "LEAGUE", "league", self.league_options_for_country("All"), height=18)
        self.add_filter(filters, "TOURNAMENT", "tournament", preferred_order(MAIN_TOURNAMENTS, MAIN_TOURNAMENTS), height=12)
        self.add_filter(filters, "DATE", "date", DATE_FILTERS, height=8)

        tk.Button(
            parent,
            text="Switch to Live API",
            bg="#5fa8d3",
            fg=TEXT,
            activebackground="#72b8df",
            activeforeground=TEXT,
            relief="flat",
            font=FONT_BOLD,
            pady=5,
            command=self.switch_live_api,
        ).grid(row=2, column=0, sticky="ew", pady=(0, 8))

        matches_outer, matches_body = self.panel(parent, "MATCHES")
        matches_outer.grid(row=3, column=0, sticky="nsew", pady=(0, 8))
        matches_body.grid_rowconfigure(0, weight=1)
        matches_body.grid_columnconfigure(0, weight=1)
        self.create_matches_scroller(matches_body)

        watch_outer, self.watch_body = self.panel(parent, "WATCHLIST")
        watch_outer.grid(row=4, column=0, sticky="nsew", pady=(0, 10))
        self.watch_body.grid_rowconfigure(0, weight=1)
        self.watch_body.grid_columnconfigure(0, weight=1)
        self.create_watchlist_scroller(self.watch_body)
        self.render_watchlist()
        self.render_matches()

    def add_filter(self, parent, title, key, values, height=8):
        index = len(parent.grid_slaves())
        frame = tk.Frame(parent, bg=PANEL)
        frame.grid(row=0, column=index, sticky="ew", padx=6, pady=6)
        tk.Label(frame, text=title, bg=PANEL, fg=CYAN, font=FONT_SMALL, anchor="w").pack(fill="x")
        combo = ttk.Combobox(
            frame,
            textvariable=self.filters[key],
            values=values,
            state="readonly",
            style="Dark.TCombobox",
            height=height,
            font=FONT_SMALL,
        )
        combo.pack(fill="x", pady=(2, 0))
        combo.bind("<<ComboboxSelected>>", lambda _event, item=key: self.on_filter_change(item))
        self.filter_combos[key] = combo

    def on_filter_change(self, key):
        if key == "country":
            self.update_league_options()
        self.render_matches()

    def league_options_for_country(self, country):
        if country == "All":
            return preferred_order(TOP_LEAGUES, ALL_LEAGUES)
        return ["All"] + COUNTRY_LEAGUES.get(country, [])

    def update_league_options(self):
        country = self.filters["country"].get()
        values = self.league_options_for_country(country)
        league_combo = self.filter_combos.get("league")
        if league_combo is not None:
            league_combo.configure(values=values)
        if self.filters["league"].get() not in values:
            self.filters["league"].set("All")

    def create_matches_scroller(self, parent):
        self.matches_canvas = tk.Canvas(parent, bg=PANEL_DARK, highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=self.matches_canvas.yview)
        self.matches_canvas.configure(yscrollcommand=scrollbar.set)
        self.matches_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.matches_frame = tk.Frame(self.matches_canvas, bg=PANEL_DARK)
        window_id = self.matches_canvas.create_window((0, 0), window=self.matches_frame, anchor="nw")

        def on_frame_configure(_event):
            self.matches_canvas.configure(scrollregion=self.matches_canvas.bbox("all"))

        def on_canvas_configure(event):
            self.matches_canvas.itemconfigure(window_id, width=event.width)

        self.matches_frame.bind("<Configure>", on_frame_configure)
        self.matches_canvas.bind("<Configure>", on_canvas_configure)
        self.matches_canvas.bind_all("<MouseWheel>", self.on_mousewheel)

    def create_watchlist_scroller(self, parent):
        self.watchlist_canvas = tk.Canvas(parent, bg=PANEL_DARK, highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=self.watchlist_canvas.yview)
        self.watchlist_canvas.configure(yscrollcommand=scrollbar.set)
        self.watchlist_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.watchlist_frame = tk.Frame(self.watchlist_canvas, bg=PANEL_DARK)
        window_id = self.watchlist_canvas.create_window((0, 0), window=self.watchlist_frame, anchor="nw")

        def on_frame_configure(_event):
            self.watchlist_canvas.configure(scrollregion=self.watchlist_canvas.bbox("all"))

        def on_canvas_configure(event):
            self.watchlist_canvas.itemconfigure(window_id, width=event.width)

        self.watchlist_frame.bind("<Configure>", on_frame_configure)
        self.watchlist_canvas.bind("<Configure>", on_canvas_configure)

    def build_center(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        tk.Label(
            parent,
            text="MATCH ANALYSIS",
            bg=BG,
            fg=CYAN,
            font=FONT_BOLD,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", pady=(8, 6))

        self.center_split = tk.PanedWindow(
            parent,
            orient="vertical",
            bg=BG,
            sashwidth=8,
            sashrelief="raised",
            showhandle=True,
            opaqueresize=True,
        )
        self.center_split.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        self.center_split.bind("<Configure>", self.on_center_split_configure)

        top_wrap = tk.Frame(self.center_split, bg=BG)
        bottom_wrap = tk.Frame(self.center_split, bg=BG)
        self.center_split.add(top_wrap, minsize=360, stretch="always")
        self.center_split.add(bottom_wrap, minsize=220, stretch="always")

        body = tk.Frame(top_wrap, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(3, weight=1)

        self.build_scoreboard(body)
        self.build_match_meta(body)
        self.build_tabs(body)

        self.tab_content = tk.Frame(body, bg=PANEL)
        self.tab_content.grid(row=3, column=0, sticky="nsew", padx=8)

        self.build_action_bar(body)
        self.build_market_sections(bottom_wrap)
        self.render_tab()
        self.render_market_sections()

    def build_market_sections(self, parent):
        market = tk.Frame(parent, bg=BG)
        market.pack(fill="both", expand=True)
        market.grid_columnconfigure(0, weight=1, uniform="market")
        market.grid_columnconfigure(1, weight=1, uniform="market")
        market.grid_rowconfigure(0, weight=1)

        odds_outer, self.odds_body = self.panel(market, "ODDS BOARD")
        odds_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        pred_outer, self.predictions_body = self.panel(market, "PREDICTION FEED")
        pred_outer.grid(row=0, column=1, sticky="nsew", padx=(4, 0))

    def build_scoreboard(self, parent):
        score = tk.Frame(parent, bg=PANEL)
        score.grid(row=0, column=0, sticky="ew", padx=8, pady=(10, 8))
        score.grid_columnconfigure(0, weight=1)
        score.grid_columnconfigure(1, weight=0)
        score.grid_columnconfigure(2, weight=1)

        home_box = tk.Frame(score, bg=PANEL)
        home_box.grid(row=0, column=0, sticky="nsew")
        tk.Label(home_box, text="HOME", bg=PANEL, fg=CYAN, font=FONT_SMALL).pack()
        self.score_labels["home_badge"] = tk.Label(
            home_box,
            text="",
            bg="#facc15",
            fg="#111827",
            font=("Segoe UI", 12, "bold"),
            width=4,
            pady=5,
        )
        self.score_labels["home_badge"].pack(pady=(0, 4))
        self.score_labels["home"] = tk.Label(home_box, text="", bg=PANEL, fg=TEXT, font=("Segoe UI", 12, "bold"))
        self.score_labels["home"].pack()
        self.score_labels["home_form"] = tk.Label(home_box, text="", bg=PANEL, fg=MUTED, font=FONT_SMALL)
        self.score_labels["home_form"].pack()
        self.score_labels["home_goals"] = tk.Label(home_box, text="", bg=PANEL, fg=MUTED, font=FONT_SMALL)
        self.score_labels["home_goals"].pack()

        center = tk.Frame(score, bg=PANEL)
        center.grid(row=0, column=1, sticky="n", padx=50)
        line = tk.Frame(center, bg=PANEL)
        line.pack()
        self.score_labels["home_score"] = tk.Label(line, text="0", bg=PANEL, fg=ORANGE, font=("Consolas", 22, "bold"))
        self.score_labels["home_score"].pack(side="left", padx=8)
        tk.Label(line, text="-", bg=PANEL, fg=ORANGE, font=("Consolas", 22, "bold")).pack(side="left")
        self.score_labels["away_score"] = tk.Label(line, text="0", bg=PANEL, fg=ORANGE, font=("Consolas", 22, "bold"))
        self.score_labels["away_score"].pack(side="left", padx=8)
        self.score_labels["minute"] = tk.Label(center, text="00'", bg=PANEL, fg=CYAN, font=FONT_MONO_SMALL)
        self.score_labels["minute"].pack()
        self.score_labels["status"] = tk.Label(center, text="LIVE", bg=PANEL, fg=GREEN, font=FONT_SMALL)
        self.score_labels["status"].pack()
        self.score_labels["edge"] = tk.Label(center, text="+0.0", bg=PANEL_DARK, fg=TEXT, font=FONT_MONO_SMALL, padx=10, pady=3)
        self.score_labels["edge"].pack(pady=(5, 0))
        self.score_labels["replay_state"] = tk.Label(center, text="", bg=PANEL, fg=MUTED, font=FONT_SMALL)
        self.score_labels["replay_state"].pack(pady=(4, 0))

        away_box = tk.Frame(score, bg=PANEL)
        away_box.grid(row=0, column=2, sticky="nsew")
        tk.Label(away_box, text="AWAY", bg=PANEL, fg=RED, font=FONT_SMALL).pack()
        self.score_labels["away_badge"] = tk.Label(
            away_box,
            text="",
            bg="#ef4444",
            fg=TEXT,
            font=("Segoe UI", 12, "bold"),
            width=4,
            pady=5,
        )
        self.score_labels["away_badge"].pack(pady=(0, 4))
        self.score_labels["away"] = tk.Label(away_box, text="", bg=PANEL, fg=TEXT, font=("Segoe UI", 12, "bold"))
        self.score_labels["away"].pack()
        self.score_labels["away_form"] = tk.Label(away_box, text="", bg=PANEL, fg=MUTED, font=FONT_SMALL)
        self.score_labels["away_form"].pack()
        self.score_labels["away_goals"] = tk.Label(away_box, text="", bg=PANEL, fg=MUTED, font=FONT_SMALL)
        self.score_labels["away_goals"].pack()

    def build_match_meta(self, parent):
        meta = tk.Frame(parent, bg=PANEL_DARK)
        meta.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        for col in range(3):
            meta.grid_columnconfigure(col, weight=1)

        self.meta_labels["date"] = self.meta_pair(meta, 0, "Date")
        self.meta_labels["venue"] = self.meta_pair(meta, 1, "Venue")
        self.meta_labels["referee"] = self.meta_pair(meta, 2, "Referee")

    def meta_pair(self, parent, col, title):
        frame = tk.Frame(parent, bg=PANEL_DARK)
        frame.grid(row=0, column=col, sticky="ew", padx=8, pady=7)
        tk.Label(frame, text=f"{title}:", bg=PANEL_DARK, fg=CYAN, font=FONT_SMALL, anchor="w").pack(side="left")
        label = tk.Label(frame, text="", bg=PANEL_DARK, fg=MUTED, font=FONT_SMALL, anchor="w")
        label.pack(side="left", padx=(4, 0))
        return label

    def build_tabs(self, parent):
        tabs = tk.Frame(parent, bg=PANEL)
        tabs.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 8))
        for idx, name in enumerate(self.center_tabs()):
            tabs.grid_columnconfigure(idx, weight=1)
            active = name == self.tab_name.get()
            btn = tk.Button(
                tabs,
                text=name,
                bg=BG if not active else PANEL_DARK,
                fg=MUTED if not active else ORANGE,
                activebackground=PANEL_DARK,
                activeforeground=ORANGE,
                relief="flat",
                font=FONT_BOLD,
                pady=6,
                command=lambda value=name: self.set_tab(value),
            )
            btn.grid(row=0, column=idx, sticky="ew")

    def center_tabs(self):
        return ["Overview", "Stats Replay", "Attack", "Control", "Defense", "Line-ups", "Chat", "Table", "H2H"]

    def on_center_split_configure(self, _event=None):
        if self.center_split_initialized or self.center_split is None:
            return
        height = self.center_split.winfo_height()
        if height <= 1:
            return
        self.center_split.sash_place(0, 0, int(height * 0.7))
        self.center_split_initialized = True

    def rebuild_tabs(self):
        parent = self.tab_content.master
        for child in parent.grid_slaves(row=2):
            child.destroy()
        self.build_tabs(parent)

    def build_action_bar(self, parent):
        actions = tk.Frame(parent, bg=BG)
        actions.grid(row=4, column=0, sticky="ew", padx=8, pady=(8, 10))
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=2)
        actions.grid_columnconfigure(2, weight=1)

        left = tk.Frame(actions, bg=BG)
        left.grid(row=0, column=0, sticky="w")
        self.button(left, "+ Add Watchlist", PURPLE, self.add_current_to_watchlist).pack(side="left", padx=(0, 6))
        self.button(left, "X Remove", GRAY_BTN, self.remove_current_from_watchlist).pack(side="left")

        center = tk.Frame(actions, bg=BG)
        center.grid(row=0, column=1, sticky="ew", padx=10)
        center.grid_columnconfigure(0, weight=1)
        ask_wrap = tk.Frame(center, bg="#243244", highlightbackground=BORDER, highlightthickness=1)
        ask_wrap.grid(row=0, column=0, sticky="ew")
        tk.Label(
            ask_wrap,
            text="Quick Find",
            bg="#243244",
            fg=CYAN,
            font=FONT_BOLD,
            padx=10,
        ).pack(side="left")
        entry = tk.Entry(
            ask_wrap,
            textvariable=self.quick_query,
            bg="#0f172a",
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=FONT_SMALL,
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 6), pady=7)
        entry.bind("<Return>", lambda _event: self.quick_find())
        self.button(ask_wrap, "Go", CYAN_DARK, self.quick_find, width=8, pady=7).pack(side="left", padx=(0, 6), pady=4)
        self.button(ask_wrap, "Live", ORANGE, self.reset_replay_to_live, width=8, pady=7).pack(side="left", padx=(0, 6), pady=4)
        tk.Label(
            center,
            text="Try: 35 minute shots, lineups, possession, table, h2h",
            bg=BG,
            fg=MUTED,
            font=FONT_SMALL,
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", pady=(4, 0))

        right = tk.Frame(actions, bg=BG)
        right.grid(row=0, column=2, sticky="e")
        self.button(right, "Start Tracker", GREEN_DARK, self.start_tracker).pack(side="left", padx=(0, 6))
        self.button(right, "Stop Tracker", GRAY_BTN, self.stop_tracker).pack(side="left")

        self.tracker_status = tk.Label(parent, text="", bg=PANEL, fg=MUTED, font=FONT_SMALL, anchor="w")
        self.tracker_status.grid(row=5, column=0, sticky="ew", padx=10, pady=(0, 8))

    def build_right(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=3)
        parent.grid_rowconfigure(1, weight=2)
        parent.grid_rowconfigure(2, weight=1)
        parent.grid_rowconfigure(3, weight=2)
        parent.grid_rowconfigure(4, weight=2)
        parent.grid_rowconfigure(5, weight=2)

        model_outer, self.recommendation_body = self.panel(parent, "DECISION ENGINE")
        model_outer.grid(row=0, column=0, sticky="nsew", pady=(8, 8))

        team_outer, self.quality_body = self.panel(parent, "DATA QUALITY")
        team_outer.grid(row=1, column=0, sticky="nsew", pady=(0, 8))

        watch_outer, body = self.panel(parent, "WATCHLIST")
        watch_outer.grid(row=2, column=0, sticky="nsew", pady=(0, 8))
        self.sidebar_watch_body = body

        chat_outer, self.chat_preview_body = self.panel(parent, "CHAT PREVIEW")
        chat_outer.grid(row=3, column=0, sticky="nsew", pady=(0, 8))

        history_outer, self.source_body = self.panel(parent, "SOURCE MONITOR")
        history_outer.grid(row=4, column=0, sticky="nsew", pady=(0, 8))

        acc_outer, self.accuracy_body = self.panel(parent, "ACCURACY DASHBOARD")
        acc_outer.grid(row=5, column=0, sticky="nsew", pady=(0, 10))

        self.render_decision_engine()
        self.render_data_quality()
        self.render_sidebar_watchlist()
        self.render_chat_preview()
        self.render_source_monitor()
        self.render_accuracy()

    def panel(self, parent, title):
        outer = tk.Frame(parent, bg=BG, highlightbackground=BORDER, highlightthickness=1)
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(1, weight=1)
        tk.Label(
            outer,
            text=title,
            bg=BG,
            fg=CYAN,
            font=FONT_BOLD,
            anchor="w",
            padx=8,
            pady=5,
        ).grid(row=0, column=0, sticky="ew")
        body = tk.Frame(outer, bg=PANEL)
        body.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))
        return outer, body

    def button(self, parent, text, bg, command, width=None, pady=6):
        return tk.Button(
            parent,
            text=text,
            bg=bg,
            fg=TEXT,
            activebackground=bg,
            activeforeground=TEXT,
            relief="flat",
            borderwidth=0,
            font=FONT_BOLD,
            padx=10,
            pady=pady,
            width=width,
            command=command,
        )

    def filtered_matches(self):
        country = self.filters["country"].get()
        league = self.filters["league"].get()
        tournament = self.filters["tournament"].get()
        date_filter = self.filters["date"].get()
        items = []
        for match in MATCHES:
            if country != "All" and match["country"] != country:
                continue
            if league != "All" and match["league"] != league:
                continue
            if tournament != "All" and match["tournament"] != tournament:
                continue
            if date_filter == "Live" and match["status"] != "LIVE":
                continue
            if date_filter == "Upcoming" and match["status"] == "LIVE":
                continue
            items.append(match)
        return items

    def render_matches(self):
        for child in self.matches_frame.winfo_children():
            child.destroy()

        matches = self.filtered_matches()
        self.status_label.config(text=f"Last Load: local mock  |  Matches: {len(matches)}")

        grouped = {}
        for match in matches:
            grouped.setdefault(match["league"], []).append(match)

        if not matches:
            tk.Label(
                self.matches_frame,
                text="No matches for selected filters.",
                bg=PANEL_DARK,
                fg=MUTED,
                font=FONT_MONO,
                pady=20,
            ).pack(fill="x")
            return

        for league, league_matches in grouped.items():
            tk.Label(
                self.matches_frame,
                text=f"--- {league.upper()} ---",
                bg="#111827",
                fg=TEXT,
                font=FONT_MONO_SMALL,
                pady=3,
            ).pack(fill="x", padx=4, pady=(4, 1))
            for match in league_matches:
                self.match_row(self.matches_frame, match)

    def match_row(self, parent, match):
        self.compact_match_row(parent, match, selected=self.current_match and match["id"] == self.current_match["id"])

    def compact_match_row(self, parent, match, selected=False):
        selected = self.current_match and match["id"] == self.current_match["id"]
        row_bg = "#1f2937" if selected else ROW
        row = tk.Frame(parent, bg=row_bg, height=32)
        row.pack(fill="x", padx=4, pady=1)
        row.grid_columnconfigure(2, weight=1)
        row.grid_columnconfigure(4, weight=1)

        status_color = GREEN if match["status"] == "LIVE" else YELLOW
        edge_color = GREEN if match["edge"] >= 0 else RED
        score = f"{match['home_score']}-{match['away_score']}"
        odds = f"{match['odds'][0]:.1f}/{match['odds'][1]:.1f}/{match['odds'][2]:.1f}"
        pred = f"{match['pred'][0]:>2}/{match['pred'][1]:>2}/{match['pred'][2]:>2}"
        is_starred = match["id"] in self.watchlist_ids
        star = "★" if is_starred else "☆"

        values = [
            (match["status"], 0, 4, status_color, "w"),
            (str(match["minute"]) if match["minute"] else "--", 1, 4, "#60a5fa", "center"),
            (match["home"], 2, 13, TEXT, "e"),
            (score, 3, 5, ORANGE, "center"),
            (match["away"], 4, 13, TEXT, "w"),
            (f"{match['edge']:+.1f}", 5, 6, edge_color, "center"),
            (odds, 6, 13, MUTED, "center"),
            (pred, 7, 9, MUTED, "center"),
        ]
        for text, col, width, color, anchor in values:
            label = tk.Label(row, text=text, bg=row_bg, fg=color, font=FONT_MONO_SMALL, width=width, anchor=anchor)
            label.grid(row=0, column=col, sticky="ew", padx=1, pady=5)
            label.bind("<Button-1>", lambda _event, item=match: self.select_match(item))

        star_btn = tk.Button(
            row,
            text=star,
            bg=row_bg,
            fg=YELLOW if is_starred else MUTED,
            activebackground=row_bg,
            activeforeground=YELLOW,
            relief="flat",
            width=2,
            font=("Segoe UI Symbol", 11, "bold"),
            command=lambda item=match: self.toggle_watchlist(item),
        )
        star_btn.grid(row=0, column=8, padx=(2, 5))
        row.bind("<Button-1>", lambda _event, item=match: self.select_match(item))

    def select_match(self, match, refresh=True):
        self.stop_replay(reset_to_current=False)
        self.current_match = match
        if self.match_finished(match):
            self.settle_match_challenges(match)
        self.selected_odds_book = None
        self.selected_prediction_source = None
        self.selected_player_detail = None
        self.replay_minute = self.stats_reference_minute(match)
        self.score_labels["home_badge"].config(text=self.team_initials(match["home"]))
        self.score_labels["away_badge"].config(text=self.team_initials(match["away"]))
        self.score_labels["home"].config(text=match["home"])
        self.score_labels["away"].config(text=match["away"])
        self.score_labels["home_score"].config(text=str(match["home_score"]))
        self.score_labels["away_score"].config(text=str(match["away_score"]))
        self.score_labels["minute"].config(text=f"{match['minute']:02d}'")
        self.score_labels["status"].config(text=match["status"], fg=GREEN if match["status"] == "LIVE" else YELLOW)
        self.score_labels["edge"].config(text=f"{match['edge']:+.1f}", fg=GREEN if match["edge"] >= 0 else RED)
        self.score_labels["home_form"].config(text="Form: " + "-".join(match["home_form"]))
        self.score_labels["away_form"].config(text="Form: " + "-".join(match["away_form"]))
        self.score_labels["home_goals"].config(text=f"Goals: {match['home_avg']}/game")
        self.score_labels["away_goals"].config(text=f"Goals: {match['away_avg']}/game")

        self.meta_labels["date"].config(text=match["date"])
        self.meta_labels["venue"].config(text=match["venue"])
        self.meta_labels["referee"].config(text=match["referee"])
        self.update_replay_header()
        self.render_tab()
        self.render_decision_engine()
        self.render_data_quality()
        self.render_chat_preview()
        self.render_source_monitor()
        self.render_market_sections()
        self.render_accuracy()
        if refresh:
            self.render_matches()

    def team_initials(self, team):
        words = [part for part in team.replace("-", " ").split() if part]
        if not words:
            return "FC"
        if len(words) == 1:
            return words[0][:3].upper()
        return "".join(word[0] for word in words[:3]).upper()

    def set_tab(self, name):
        if name != "Stats Replay":
            self.pause_replay()
        self.tab_name.set(name)
        self.rebuild_tabs()
        self.render_tab()
        self.update_replay_header()

    def render_tab(self):
        for child in self.tab_content.winfo_children():
            child.destroy()

        match = self.current_match
        body = self.tab_body()
        tab = self.tab_name.get()
        if tab == "Overview":
            self.render_overview_tab(body, match)
        elif tab == "Stats Replay":
            self.render_stats_tab(body, match)
        elif tab == "Attack":
            self.render_attack_tab(body, match)
        elif tab == "Control":
            self.render_control_tab(body, match)
        elif tab == "Defense":
            self.render_defense_tab(body, match)
        elif tab == "Line-ups":
            self.render_lineups_tab(body, match)
        elif tab == "Chat":
            self.render_chat_tab(body, match)
        elif tab == "Table":
            self.render_table_tab(body, match)
        elif tab == "H2H":
            self.render_h2h_tab(body, match)

    def tab_body(self):
        canvas = tk.Canvas(self.tab_content, bg=PANEL, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.tab_content, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        body = tk.Frame(canvas, bg=PANEL)
        window_id = canvas.create_window((0, 0), window=body, anchor="nw")

        def on_body_configure(_event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_configure(event):
            canvas.itemconfigure(window_id, width=event.width)

        body.bind("<Configure>", on_body_configure)
        canvas.bind("<Configure>", on_canvas_configure)
        return body

    def section_title(self, parent, text):
        tk.Label(
            parent,
            text=text,
            bg=PANEL,
            fg=CYAN,
            font=FONT_BOLD,
            anchor="w",
            pady=6,
        ).pack(fill="x")

    def info_card(self, parent):
        card = tk.Frame(parent, bg=PANEL_DARK, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", pady=6)
        return card

    def render_stat_summary_row(self, parent, summaries):
        card = self.info_card(parent)
        card.pack(fill="x", pady=(0, 8))
        row = tk.Frame(card, bg=PANEL_DARK)
        row.pack(fill="x", padx=10, pady=8)
        for label, home_pct, away_pct in summaries:
            box = tk.Frame(row, bg="#243244")
            box.pack(side="left", expand=True, fill="x", padx=3)
            tk.Label(box, text=label, bg="#243244", fg=MUTED, font=FONT_SMALL).pack(pady=(6, 2))
            tk.Label(box, text=f"{home_pct}% / {away_pct}%", bg="#243244", fg=TEXT, font=FONT_BOLD).pack(pady=(0, 2))
            strip = tk.Frame(box, bg="#1a2435", height=6)
            strip.pack(fill="x", padx=10, pady=(2, 8))
            left = max(1, int(home_pct))
            right = max(1, int(away_pct))
            strip.grid_columnconfigure(0, weight=left)
            strip.grid_columnconfigure(1, weight=right)
            tk.Frame(strip, bg=CYAN, height=6).grid(row=0, column=0, sticky="ew")
            tk.Frame(strip, bg=ORANGE, height=6).grid(row=0, column=1, sticky="ew")
        return card

    def render_replay_state_note(self, parent, minute, max_minute):
        tk.Label(
            parent,
            text=f"Viewing replay state at {minute:02d}' of {max_minute}'",
            bg=PANEL,
            fg=MUTED,
            font=FONT_SMALL,
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

    def update_replay_header(self):
        minute = self.current_replay_minute(self.current_match)
        match_minute = self.stats_reference_minute(self.current_match)
        text = f"Viewing {minute:02d}' replay"
        if minute == match_minute:
            text = f"Viewing current state {minute:02d}'"
        if self.replay_running:
            text = f"Playing replay from {self.replay_start_minute:02d}'  |  now {minute:02d}'"
        self.score_labels["replay_state"].config(text=text)

    def quick_find(self):
        query = self.quick_query.get().strip()
        if not query:
            self.tracker_status.config(
                text="Try a quick jump like: 35 minute shots, lineups, table, h2h, or possession.",
                fg=MUTED,
            )
            return

        lower = query.lower()
        minute = None
        minute_match = re.search(r"(\d{1,3})", lower)
        if minute_match:
            minute = min(int(minute_match.group(1)), self.stats_max_minute(self.current_match))
            self.set_replay_minute(minute)

        tab, label = self.resolve_quick_find_target(lower)
        if tab:
            self.set_tab(tab)

        minute_text = f" at {self.current_replay_minute(self.current_match):02d}'" if minute is not None else ""
        message = f"Quick Find: opened {label}{minute_text}."
        self.tracker_status.config(text=message, fg=CYAN)

    def resolve_quick_find_target(self, query):
        mappings = [
            (("chat", "room", "debate", "talk"), "Chat", "match chat"),
            (("lineup", "line-ups", "formation", "player"), "Line-ups", "Line-ups"),
            (("table", "standings", "rank"), "Table", "league table"),
            (("h2h", "head to head", "previous"), "H2H", "head-to-head"),
            (("attack", "shot", "shots", "xg", "chance", "goal"), "Attack", "attack profile"),
            (("possession", "pass", "control", "territory", "corner", "cross"), "Control", "control profile"),
            (("defense", "defence", "foul", "card", "save", "offside", "duel"), "Defense", "defense profile"),
            (("replay", "timeline", "minute", "live"), "Stats Replay", "stats replay"),
            (("overview", "summary", "info"), "Overview", "overview"),
        ]
        for terms, tab, label in mappings:
            if any(term in query for term in terms):
                return tab, label
        return "Overview", "overview"

    def reset_replay_to_live(self):
        target = self.stats_reference_minute(self.current_match)
        self.set_replay_minute(target)
        self.tracker_status.config(text=f"Replay reset to current minute {target:02d}'.", fg=GREEN)

    def draw_timeline_markers(self, canvas, match, max_minute):
        canvas.delete("all")
        width = max(canvas.winfo_width(), 10)
        left_pad = 6
        right_pad = 6
        line_y = 11
        canvas.create_line(left_pad, line_y, width - right_pad, line_y, fill=BORDER, width=2)

        events = self.timeline_events(match, max_minute)
        for idx, event in enumerate(events):
            x = left_pad + ((width - left_pad - right_pad) * event["minute"] / max(max_minute, 1))
            color = self.event_color(event["event"])
            tag = f"marker_{idx}"
            canvas.create_line(x, 4, x, 18, fill=color, width=2, tags=(tag,))
            canvas.create_oval(x - 3, line_y - 3, x + 3, line_y + 3, fill=color, outline=color, tags=(tag,))
            canvas.create_text(x, 23, text=event["minute_text"], fill=MUTED, font=FONT_SMALL, tags=(tag,))
            canvas.tag_bind(tag, "<Button-1>", lambda _event, minute=event["minute"]: self.jump_to_replay_minute(minute))

    def event_color(self, event_name):
        color_map = {
            "GOAL": ORANGE,
            "CARD": YELLOW,
            "SUB": CYAN,
            "SHOT": CYAN,
            "SAVE": CYAN,
            "PRESS": GREEN,
            "VAR": PURPLE,
            "PEN": RED,
            "SCORE": MUTED,
        }
        return color_map.get(event_name, CYAN)

    def render_player_panels(self, parent, context, left_title, left_rows, right_title, right_rows, accent):
        wrap = tk.Frame(parent, bg=PANEL)
        wrap.pack(fill="x", pady=(0, 6))
        left = self.info_card(wrap)
        right = self.info_card(wrap)
        left.pack_forget()
        right.pack_forget()
        left.grid(in_=wrap, row=0, column=0, sticky="nsew", padx=(0, 4))
        right.grid(in_=wrap, row=0, column=1, sticky="nsew", padx=(4, 0))
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_columnconfigure(1, weight=1)
        self.render_player_panel(left, context, left_title, left_rows, accent)
        self.render_player_panel(right, context, right_title, right_rows, accent)
        self.render_selected_player_detail(parent, context)

    def render_player_panel(self, parent, context, title, rows, accent):
        header = tk.Frame(parent, bg=PANEL_DARK)
        header.pack(fill="x", padx=10, pady=(8, 4))
        tk.Label(header, text=title, bg=PANEL_DARK, fg=TEXT, font=FONT_BOLD, anchor="w").pack(side="left")
        tk.Frame(header, bg=accent, width=26, height=4).pack(side="right", pady=6)

        for detail in rows:
            name = detail["name"]
            stat_line = detail["summary"]
            row = tk.Frame(parent, bg=PANEL_DARK)
            row.pack(fill="x", padx=10, pady=3)
            badge = tk.Label(row, text=self.team_initials(name)[:2], bg="#243244", fg=TEXT, font=FONT_MONO_SMALL, width=4, pady=4)
            badge.pack(side="left")
            text_wrap = tk.Frame(row, bg=PANEL_DARK)
            text_wrap.pack(side="left", fill="x", expand=True, padx=(8, 0))
            name_label = tk.Label(text_wrap, text=name, bg=PANEL_DARK, fg=TEXT, font=FONT_SMALL, anchor="w", cursor="hand2")
            name_label.pack(fill="x")
            stat_label = tk.Label(text_wrap, text=stat_line, bg=PANEL_DARK, fg=MUTED, font=FONT_SMALL, anchor="w", cursor="hand2")
            stat_label.pack(fill="x")
            arrow = tk.Label(row, text=">", bg=PANEL_DARK, fg=accent, font=FONT_BOLD, width=2, cursor="hand2")
            arrow.pack(side="right")
            for widget in (row, badge, text_wrap, name_label, stat_label, arrow):
                widget.bind(
                    "<Button-1>",
                    lambda _event, payload=detail, section=context: self.open_player_detail(section, payload),
                )

    def render_selected_player_detail(self, parent, context):
        detail = self.selected_player_detail
        if not detail or detail["context"] != context:
            hint = tk.Label(
                parent,
                text="Click a player row to open a deeper performance card.",
                bg=PANEL,
                fg=MUTED,
                font=FONT_SMALL,
                anchor="w",
            )
            hint.pack(fill="x", pady=(0, 6))
            return

        card = self.info_card(parent)
        top = tk.Frame(card, bg=PANEL_DARK)
        top.pack(fill="x", padx=10, pady=(8, 4))
        tk.Label(top, text=f"{detail['name']}  |  {detail['team']}", bg=PANEL_DARK, fg=TEXT, font=FONT_BOLD, anchor="w").pack(side="left")
        tk.Button(
            top,
            text="Close",
            bg="#243244",
            fg=TEXT,
            activebackground="#334155",
            activeforeground=TEXT,
            relief="flat",
            font=FONT_SMALL,
            command=self.close_player_detail,
        ).pack(side="right")

        tk.Label(
            card,
            text=detail["headline"],
            bg=PANEL_DARK,
            fg=MUTED,
            font=FONT_SMALL,
            anchor="w",
            padx=10,
            pady=2,
        ).pack(fill="x")

        metrics = tk.Frame(card, bg=PANEL_DARK)
        metrics.pack(fill="x", padx=10, pady=(4, 8))
        for idx, (label, value) in enumerate(detail["metrics"]):
            box = tk.Frame(metrics, bg="#243244")
            box.grid(row=0, column=idx, sticky="ew", padx=3)
            metrics.grid_columnconfigure(idx, weight=1)
            tk.Label(box, text=label, bg="#243244", fg=MUTED, font=FONT_SMALL).pack(pady=(6, 2))
            tk.Label(box, text=value, bg="#243244", fg=TEXT, font=FONT_BOLD).pack(pady=(0, 6))

        notes = tk.Frame(card, bg=PANEL_DARK)
        notes.pack(fill="x", padx=10, pady=(0, 10))
        tk.Label(notes, text="Why it matters", bg=PANEL_DARK, fg=CYAN, font=FONT_BOLD, anchor="w").pack(fill="x", pady=(0, 4))
        for line in detail["notes"]:
            tk.Label(notes, text=f"+ {line}", bg=PANEL_DARK, fg=MUTED, font=FONT_SMALL, anchor="w", justify="left").pack(fill="x", pady=1)

    def open_player_detail(self, context, payload):
        self.selected_player_detail = {"context": context, **payload}
        self.render_tab()

    def close_player_detail(self):
        self.selected_player_detail = None
        self.render_tab()

    def jump_to_replay_minute(self, minute):
        self.pause_replay()
        self.set_replay_minute(minute)

    def play_replay(self):
        if self.replay_slider is None or self.tab_name.get() != "Stats Replay":
            self.set_tab("Stats Replay")
        if self.replay_slider is None:
            return
        if self.replay_running:
            return
        self.replay_running = True
        self.replay_start_minute = self.current_replay_minute(self.current_match)
        self.update_replay_header()
        self.replay_tick()

    def replay_tick(self):
        if not self.replay_running or self.replay_slider is None:
            return
        current = self.current_replay_minute(self.current_match)
        if current >= self.replay_max_minute:
            self.pause_replay()
            return
        next_minute = current + 1
        self.set_replay_minute(next_minute)
        self.replay_job = self.root.after(380, self.replay_tick)

    def pause_replay(self):
        self.replay_running = False
        if self.replay_job is not None:
            self.root.after_cancel(self.replay_job)
            self.replay_job = None
        self.update_replay_header()

    def stop_replay(self, reset_to_current=True):
        self.pause_replay()
        target = self.replay_start_minute
        if target is None:
            target = self.stats_reference_minute(self.current_match) if reset_to_current else self.current_replay_minute(self.current_match)
        self.replay_start_minute = None
        self.set_replay_minute(target)

    def set_replay_minute(self, minute):
        minute = max(0, min(int(minute), self.stats_max_minute(self.current_match)))
        self.replay_minute = minute
        if self.replay_slider is not None and self.tab_name.get() == "Stats Replay":
            self.replay_slider.set(minute)
            if self.replay_refresh is not None:
                self.replay_refresh(str(minute))
        else:
            self.update_replay_header()
            self.render_tab()

    def render_info_rows(self, parent, rows):
        for label, home, away in rows:
            row = tk.Frame(parent, bg=PANEL)
            row.pack(fill="x", pady=5)
            tk.Label(row, text=label, bg=PANEL, fg=CYAN, font=FONT_BOLD, width=18, anchor="w").pack(side="left")
            tk.Label(row, text=home, bg=PANEL, fg=TEXT, font=FONT_UI, anchor="w").pack(side="left", padx=(6, 20))
            if away:
                tk.Label(row, text=away, bg=PANEL, fg=MUTED, font=FONT_UI, anchor="w").pack(side="left")

    def render_info_tab(self, parent, match):
        self.section_title(parent, "MATCH INFO")
        card = self.info_card(parent)
        details = [
            ("Date", match["date"]),
            ("Competition", match["tournament"]),
            ("Venue", match["venue"]),
            ("Referee", match["referee"]),
            ("Status", match["status"]),
            ("Minute", f"{match['minute']}'" if match["minute"] else "Pre-match"),
        ]
        for idx, (label, value) in enumerate(details):
            row = tk.Frame(card, bg=PANEL_DARK)
            row.grid(row=idx // 2, column=idx % 2, sticky="ew", padx=12, pady=8)
            card.grid_columnconfigure(idx % 2, weight=1)
            tk.Label(row, text=label, bg=PANEL_DARK, fg=MUTED, font=FONT_SMALL, anchor="w").pack(fill="x")
            tk.Label(row, text=value, bg=PANEL_DARK, fg=TEXT, font=FONT_BOLD, anchor="w").pack(fill="x")

        self.section_title(parent, "WHO WILL WIN")
        poll = self.info_card(parent)
        home_pct, draw_pct, away_pct = match["pred"]
        for label, pct, color in [
            (match["home"], home_pct, CYAN),
            ("Draw", draw_pct, MUTED),
            (match["away"], away_pct, ORANGE),
        ]:
            row = tk.Frame(poll, bg=PANEL_DARK)
            row.pack(fill="x", padx=12, pady=5)
            tk.Label(row, text=label, bg=PANEL_DARK, fg=TEXT, font=FONT_SMALL, width=18, anchor="w").pack(side="left")
            self.mini_bar(row, pct, color)
            tk.Label(row, text=f"{pct}%", bg=PANEL_DARK, fg=TEXT, font=FONT_SMALL, width=6, anchor="e").pack(side="right")

    def render_overview_tab(self, parent, match):
        minute = self.current_replay_minute(match)
        max_minute = self.stats_max_minute(match)

        self.section_title(parent, "MATCH OVERVIEW")
        self.render_replay_state_note(parent, minute, max_minute)
        self.render_stat_summary_row(parent, self.stats_summary_percentages(match, minute, max_minute))

        self.section_title(parent, "MATCH DETAILS")
        details = self.info_card(parent)
        values = [
            ("Competition", match["tournament"]),
            ("Status", match["status"]),
            ("Venue", match["venue"]),
            ("Minute", f"{minute:02d}'" if minute else "Pre-match"),
            ("Referee", match["referee"]),
            ("League Angle", f"{match['league']} form + market context"),
        ]
        for idx, (label, value) in enumerate(values):
            row = tk.Frame(details, bg=PANEL_DARK)
            row.grid(row=idx // 2, column=idx % 2, sticky="ew", padx=12, pady=8)
            details.grid_columnconfigure(idx % 2, weight=1)
            tk.Label(row, text=label, bg=PANEL_DARK, fg=MUTED, font=FONT_SMALL, anchor="w").pack(fill="x")
            tk.Label(row, text=value, bg=PANEL_DARK, fg=TEXT, font=FONT_BOLD, anchor="w").pack(fill="x")

        self.section_title(parent, "MATCH FLOW")
        for minute_text, team, event, detail in self.match_events(match):
            row = self.info_card(parent)
            row.configure(highlightthickness=0)
            tk.Label(row, text=minute_text, bg=PANEL_DARK, fg=MUTED, font=FONT_MONO_SMALL, width=8, anchor="w").pack(side="left", padx=10, pady=8)
            tk.Label(row, text=event, bg=PANEL_DARK, fg=ORANGE if event == "GOAL" else YELLOW if event == "CARD" else CYAN, font=FONT_BOLD, width=10).pack(side="left")
            tk.Label(row, text=team or "Match", bg=PANEL_DARK, fg=TEXT, font=FONT_BOLD, width=16, anchor="w").pack(side="left")
            tk.Label(row, text=detail, bg=PANEL_DARK, fg=MUTED, font=FONT_SMALL, anchor="w").pack(side="left", fill="x", expand=True)

        self.section_title(parent, "KEY EDGE SNAPSHOT")
        highlight_stats = self.match_stats_at_minute(match, minute, max_minute)[:6]
        snapshot = self.info_card(parent)
        snapshot.pack(fill="x", pady=(0, 4))
        for label, home, away in highlight_stats:
            self.stat_bar(snapshot, label, home, away)

    def render_market_sections(self):
        if self.odds_body is None or self.predictions_body is None:
            return

        self.clear(self.odds_body)
        self.clear(self.predictions_body)
        match = self.current_match

        if self.selected_odds_book:
            self.render_odds_detail(match, self.selected_odds_book)
        else:
            self.render_odds_board(match)

        if self.selected_prediction_source:
            self.render_prediction_detail(match, self.selected_prediction_source)
        else:
            self.render_prediction_feed(match)

    def render_odds_board(self, match):
        header = tk.Frame(self.odds_body, bg=PANEL_DARK)
        header.pack(fill="x", padx=6, pady=(6, 2))
        for text, width in [("BOOK", 14), ("HOME", 7), ("DRAW", 7), ("AWAY", 7), ("EDGE", 7)]:
            tk.Label(header, text=text, bg=PANEL_DARK, fg=ORANGE, font=FONT_MONO_SMALL, width=width, anchor="w").pack(side="left")

        for book, home, draw, away, edge in self.odds_rows(match):
            row_bg = ROW_ALT if edge >= 0 else ROW
            row = tk.Frame(self.odds_body, bg=row_bg)
            row.pack(fill="x", padx=6, pady=1)
            values = [
                (book, 14, TEXT),
                (f"{home:.2f}", 7, CYAN),
                (f"{draw:.2f}", 7, MUTED),
                (f"{away:.2f}", 7, ORANGE),
                (f"{edge:+.1f}", 7, GREEN if edge >= 0 else RED),
            ]
            for value, width, color in values:
                label = tk.Label(row, text=value, bg=row_bg, fg=color, font=FONT_MONO_SMALL, width=width, anchor="w")
                label.pack(side="left", pady=4)
                label.bind("<Button-1>", lambda _event, book_name=book: self.open_odds_detail(book_name))
            row.bind("<Button-1>", lambda _event, book_name=book: self.open_odds_detail(book_name))

        footer = tk.Frame(self.odds_body, bg=PANEL)
        footer.pack(fill="x", padx=6, pady=(5, 4))
        best = max(self.odds_rows(match), key=lambda item: item[4])
        tk.Label(
            footer,
            text=f"Best value: {best[0]}  edge {best[4]:+.1f}",
            bg=PANEL,
            fg=GREEN if best[4] >= 0 else RED,
            font=FONT_SMALL,
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            self.odds_body,
            text="Click a bookmaker row for full market detail. Use the top button to return.",
            bg=PANEL,
            fg=MUTED,
            font=FONT_SMALL,
            anchor="w",
        ).pack(fill="x", padx=6, pady=(0, 4))

    def render_prediction_feed(self, match):
        header = tk.Frame(self.predictions_body, bg=PANEL_DARK)
        header.pack(fill="x", padx=6, pady=(6, 2))
        for text, width in [("SOURCE", 14), ("HOME", 7), ("DRAW", 7), ("AWAY", 7), ("PICK", 10)]:
            tk.Label(header, text=text, bg=PANEL_DARK, fg=ORANGE, font=FONT_MONO_SMALL, width=width, anchor="w").pack(side="left")

        for source, home, draw, away, pick in self.prediction_rows(match):
            row = tk.Frame(self.predictions_body, bg=ROW)
            row.pack(fill="x", padx=6, pady=1)
            pick_color = CYAN if pick == match["home"] else ORANGE if pick == match["away"] else MUTED
            values = [
                (source, 14, TEXT),
                (f"{home}%", 7, CYAN),
                (f"{draw}%", 7, MUTED),
                (f"{away}%", 7, ORANGE),
                (pick[:10], 10, pick_color),
            ]
            for value, width, color in values:
                label = tk.Label(row, text=value, bg=ROW, fg=color, font=FONT_MONO_SMALL, width=width, anchor="w")
                label.pack(side="left", pady=4)
                label.bind("<Button-1>", lambda _event, source_name=source: self.open_prediction_detail(source_name))
            row.bind("<Button-1>", lambda _event, source_name=source: self.open_prediction_detail(source_name))

        consensus = self.consensus_prediction(match)
        summary = self.info_card(self.predictions_body)
        tk.Label(summary, text="CONSENSUS", bg=PANEL_DARK, fg=CYAN, font=FONT_BOLD, anchor="w").pack(fill="x", padx=8, pady=(6, 2))
        tk.Label(
            summary,
            text=f"{consensus['pick']}  |  confidence {consensus['confidence']}%  |  avg home/draw/away {consensus['home']} / {consensus['draw']} / {consensus['away']}",
            bg=PANEL_DARK,
            fg=TEXT,
            font=FONT_SMALL,
            anchor="w",
            padx=8,
            pady=7,
        ).pack(fill="x")
        tk.Label(
            self.predictions_body,
            text="Click a prediction source row for full source detail. Use the top button to return.",
            bg=PANEL,
            fg=MUTED,
            font=FONT_SMALL,
            anchor="w",
        ).pack(fill="x", padx=6, pady=(0, 4))

    def render_odds_detail(self, match, book_name):
        top = tk.Frame(self.odds_body, bg=PANEL_DARK)
        top.pack(fill="x", padx=6, pady=(6, 6))
        tk.Button(
            top,
            text="< Back to books",
            bg="#243244",
            fg=TEXT,
            activebackground="#334155",
            activeforeground=TEXT,
            relief="flat",
            font=FONT_SMALL,
            command=self.close_odds_detail,
        ).pack(side="left")
        tk.Label(top, text=f"{book_name} detailed markets", bg=PANEL_DARK, fg=ORANGE, font=FONT_BOLD).pack(side="left", padx=10)

        headline = self.info_card(self.odds_body)
        headline.pack(fill="x", padx=6, pady=(0, 6))
        tk.Label(
            headline,
            text=f"{match['home']} vs {match['away']}  |  {match['league']}  |  {book_name}",
            bg=PANEL_DARK,
            fg=TEXT,
            font=FONT_BOLD,
            anchor="w",
        ).pack(fill="x", padx=10, pady=(8, 4))
        tk.Label(
            headline,
            text="Double Chance, Totals, BTTS, cards, corners, and live derivative prices for this bookmaker.",
            bg=PANEL_DARK,
            fg=MUTED,
            font=FONT_SMALL,
            anchor="w",
        ).pack(fill="x", padx=10, pady=(0, 8))

        header = tk.Frame(self.odds_body, bg=PANEL_DARK)
        header.pack(fill="x", padx=6, pady=(0, 2))
        for text, width in [("MARKET", 20), ("HOME/YES", 10), ("DRAW", 10), ("AWAY/NO", 10), ("NOTE", 18)]:
            tk.Label(header, text=text, bg=PANEL_DARK, fg=ORANGE, font=FONT_MONO_SMALL, width=width, anchor="w").pack(side="left")

        for market, left, middle, right, note in self.odds_detail_rows(match, book_name):
            row = tk.Frame(self.odds_body, bg=ROW)
            row.pack(fill="x", padx=6, pady=1)
            for value, width, color in [
                (market, 20, TEXT),
                (left, 10, CYAN),
                (middle, 10, MUTED),
                (right, 10, ORANGE),
                (note, 18, GREEN if "value" in note.lower() else MUTED),
            ]:
                tk.Label(row, text=value, bg=ROW, fg=color, font=FONT_MONO_SMALL, width=width, anchor="w").pack(side="left", pady=4)

    def render_prediction_detail(self, match, source_name):
        top = tk.Frame(self.predictions_body, bg=PANEL_DARK)
        top.pack(fill="x", padx=6, pady=(6, 6))
        tk.Button(
            top,
            text="< Back to sources",
            bg="#243244",
            fg=TEXT,
            activebackground="#334155",
            activeforeground=TEXT,
            relief="flat",
            font=FONT_SMALL,
            command=self.close_prediction_detail,
        ).pack(side="left")
        tk.Label(top, text=f"{source_name} prediction detail", bg=PANEL_DARK, fg=ORANGE, font=FONT_BOLD).pack(side="left", padx=10)

        summary = self.info_card(self.predictions_body)
        summary.pack(fill="x", padx=6, pady=(0, 6))
        detail = self.prediction_detail_snapshot(match, source_name)
        tk.Label(summary, text=detail["headline"], bg=PANEL_DARK, fg=TEXT, font=FONT_BOLD, anchor="w").pack(fill="x", padx=10, pady=(8, 3))
        tk.Label(summary, text=f"Confidence {detail['confidence']}%  |  model family {detail['model_family']}  |  update {detail['updated']}", bg=PANEL_DARK, fg=MUTED, font=FONT_SMALL, anchor="w").pack(fill="x", padx=10, pady=(0, 8))

        self.section_title(self.predictions_body, "SOURCE MARKETS")
        markets = self.info_card(self.predictions_body)
        markets.pack(fill="x", padx=6, pady=(0, 4))
        for label, value in detail["markets"]:
            row = tk.Frame(markets, bg=PANEL_DARK)
            row.pack(fill="x", padx=10, pady=2)
            tk.Label(row, text=label, bg=PANEL_DARK, fg=CYAN, font=FONT_SMALL, width=18, anchor="w").pack(side="left")
            tk.Label(row, text=value, bg=PANEL_DARK, fg=TEXT, font=FONT_SMALL, anchor="w").pack(side="left")

        self.section_title(self.predictions_body, "WHY THIS SOURCE LEANS HERE")
        reasons = self.info_card(self.predictions_body)
        reasons.pack(fill="x", padx=6, pady=(0, 4))
        for reason in detail["reasons"]:
            tk.Label(reasons, text=f"+ {reason}", bg=PANEL_DARK, fg=GREEN, font=FONT_SMALL, anchor="w", justify="left").pack(fill="x", padx=10, pady=2)

        self.section_title(self.predictions_body, "SOURCE WARNING FLAGS")
        flags = self.info_card(self.predictions_body)
        flags.pack(fill="x", padx=6, pady=(0, 4))
        for flag in detail["flags"]:
            tk.Label(flags, text=f"- {flag}", bg=PANEL_DARK, fg=RED, font=FONT_SMALL, anchor="w", justify="left").pack(fill="x", padx=10, pady=2)

    def open_odds_detail(self, book_name):
        self.selected_odds_book = book_name
        self.render_market_sections()

    def close_odds_detail(self):
        self.selected_odds_book = None
        self.render_market_sections()

    def open_prediction_detail(self, source_name):
        self.selected_prediction_source = source_name
        self.render_market_sections()

    def close_prediction_detail(self):
        self.selected_prediction_source = None
        self.render_market_sections()

    def render_summary_tab(self, parent, match):
        self.section_title(parent, "EVENTS")
        events = self.match_events(match)
        for minute, team, event, detail in events:
            row = self.info_card(parent)
            row.configure(highlightthickness=0)
            tk.Label(row, text=minute, bg=PANEL_DARK, fg=MUTED, font=FONT_MONO_SMALL, width=8, anchor="w").pack(side="left", padx=10, pady=9)
            tk.Label(row, text=event, bg=PANEL_DARK, fg=ORANGE if event == "GOAL" else YELLOW, font=FONT_BOLD, width=10).pack(side="left")
            tk.Label(row, text=team, bg=PANEL_DARK, fg=TEXT, font=FONT_BOLD, width=16, anchor="w").pack(side="left")
            tk.Label(row, text=detail, bg=PANEL_DARK, fg=MUTED, font=FONT_SMALL, anchor="w").pack(side="left", fill="x", expand=True)

        self.section_title(parent, "MATCH TRACKER")
        tracker = self.info_card(parent)
        tk.Label(
            tracker,
            text="Momentum: home pressure early, away response after the break. Tracker will accept live and historical event feeds.",
            bg=PANEL_DARK,
            fg=MUTED,
            font=FONT_UI,
            wraplength=620,
            justify="left",
            padx=12,
            pady=12,
        ).pack(fill="x")

    def render_stats_tab(self, parent, match):
        max_minute = self.stats_max_minute(match)

        self.section_title(parent, "MATCH STATS TIMELINE")

        summary = self.render_stat_summary_row(parent, self.stats_summary_percentages(match, max_minute))
        summary_labels = {}
        for box in summary.winfo_children()[0].winfo_children():
            labels = [child for child in box.winfo_children() if isinstance(child, tk.Label)]
            if len(labels) >= 2:
                summary_labels[labels[0].cget("text")] = labels[1]

        slider_card = self.info_card(parent)
        slider_card.pack(fill="x", pady=(0, 8))
        top = tk.Frame(slider_card, bg=PANEL_DARK)
        top.pack(fill="x", padx=10, pady=(8, 2))
        tk.Label(top, text="MATCH REPLAY", bg=PANEL_DARK, fg=CYAN, font=FONT_BOLD, anchor="w").pack(side="left")
        minute_label = tk.Label(top, text="", bg=PANEL_DARK, fg=ORANGE, font=FONT_BOLD, anchor="e")
        minute_label.pack(side="right")

        scale_wrap = tk.Frame(slider_card, bg=PANEL_DARK)
        scale_wrap.pack(fill="x", padx=10, pady=(0, 8))
        tk.Label(scale_wrap, text="0'", bg=PANEL_DARK, fg=MUTED, font=FONT_SMALL).pack(side="left")
        slider = tk.Scale(
            scale_wrap,
            from_=0,
            to=max_minute,
            orient="horizontal",
            showvalue=False,
            resolution=1,
            bg=PANEL_DARK,
            fg=TEXT,
            troughcolor="#243244",
            highlightthickness=0,
            activebackground=ORANGE,
            length=520,
        )
        slider.pack(side="left", fill="x", expand=True, padx=8)
        tk.Label(scale_wrap, text=f"{max_minute}'", bg=PANEL_DARK, fg=MUTED, font=FONT_SMALL).pack(side="right")

        helper = tk.Label(
            slider_card,
            text="Slide across the match to replay how the stat balance changed minute by minute.",
            bg=PANEL_DARK,
            fg=MUTED,
            font=FONT_SMALL,
            anchor="w",
        )
        helper.pack(fill="x", padx=10, pady=(0, 8))

        markers = tk.Canvas(slider_card, bg=PANEL_DARK, height=26, highlightthickness=0)
        markers.pack(fill="x", padx=10, pady=(0, 8))

        controls = tk.Frame(slider_card, bg=PANEL_DARK)
        controls.pack(fill="x", padx=10, pady=(0, 8))
        self.button(controls, "Play", CYAN_DARK, self.play_replay, width=10, pady=7).pack(side="left", padx=(0, 6))
        self.button(controls, "Pause", GRAY_BTN, self.pause_replay, width=10, pady=7).pack(side="left", padx=(0, 6))
        self.button(controls, "Stop", RED_DARK, self.stop_replay, width=10, pady=7).pack(side="left")
        tk.Label(
            controls,
            text="Play runs forward from the selected minute. Stop returns to where that replay started.",
            bg=PANEL_DARK,
            fg=MUTED,
            font=FONT_SMALL,
            anchor="w",
        ).pack(side="left", fill="x", expand=True, padx=(12, 0))

        stats_frame = tk.Frame(parent, bg=PANEL)
        stats_frame.pack(fill="x")
        events_frame = self.info_card(parent)
        events_frame.pack(fill="x", pady=(8, 4))

        def refresh_stats(value):
            minute = int(float(value))
            self.replay_minute = minute
            minute_label.config(text=f"{minute:02d}'")
            for label, home_pct, away_pct in self.stats_summary_percentages(match, minute, max_minute):
                if label in summary_labels:
                    summary_labels[label].config(text=f"{home_pct}% / {away_pct}%")
            self.clear(stats_frame)
            for label, home, away in self.match_stats_at_minute(match, minute, max_minute):
                self.stat_bar(stats_frame, label, home, away)
            self.render_replay_events(events_frame, match, minute, max_minute)

        slider.configure(command=refresh_stats)
        self.draw_timeline_markers(markers, match, max_minute)
        markers.bind("<Configure>", lambda _event: self.draw_timeline_markers(markers, match, max_minute))
        self.replay_slider = slider
        self.replay_refresh = refresh_stats
        self.replay_max_minute = max_minute
        slider.set(self.current_replay_minute(match))
        refresh_stats(slider.get())

    def render_attack_tab(self, parent, match):
        minute = self.current_replay_minute(match)
        max_minute = self.stats_max_minute(match)
        self.section_title(parent, "ATTACK PROFILE")
        self.render_replay_state_note(parent, minute, max_minute)

        self.render_stat_summary_row(parent, self.attack_summary_percentages(match, minute, max_minute))

        self.section_title(parent, "ATTACKING OUTPUT")
        attack_card = self.info_card(parent)
        attack_card.pack(fill="x", pady=(0, 4))
        for label, home, away in self.attack_stats(match, minute, max_minute):
            self.stat_bar(attack_card, label, home, away)

        self.section_title(parent, "ATTACK LEADERS")
        self.render_player_panels(
            parent,
            "attack",
            match["home"],
            self.attack_players(match, match["home"], minute, max_minute),
            match["away"],
            self.attack_players(match, match["away"], minute, max_minute),
            ORANGE,
        )

    def render_control_tab(self, parent, match):
        minute = self.current_replay_minute(match)
        max_minute = self.stats_max_minute(match)
        self.section_title(parent, "CONTROL & TERRITORY")
        self.render_replay_state_note(parent, minute, max_minute)

        self.render_stat_summary_row(parent, self.control_summary_percentages(match, minute, max_minute))

        self.section_title(parent, "CONTROL STATS")
        control_card = self.info_card(parent)
        control_card.pack(fill="x", pady=(0, 4))
        for label, home, away in self.control_stats(match, minute, max_minute):
            self.stat_bar(control_card, label, home, away)

    def render_defense_tab(self, parent, match):
        minute = self.current_replay_minute(match)
        max_minute = self.stats_max_minute(match)
        self.section_title(parent, "DEFENSE & DISCIPLINE")
        self.render_replay_state_note(parent, minute, max_minute)

        self.render_stat_summary_row(parent, self.defense_summary_percentages(match, minute, max_minute))

        self.section_title(parent, "DEFENSIVE STATS")
        defense_card = self.info_card(parent)
        defense_card.pack(fill="x", pady=(0, 4))
        for label, home, away in self.defense_stats(match, minute, max_minute):
            self.stat_bar(defense_card, label, home, away)

        self.section_title(parent, "DEFENSIVE LEADERS")
        self.render_player_panels(
            parent,
            "defense",
            match["home"],
            self.defense_players(match, match["home"], minute, max_minute),
            match["away"],
            self.defense_players(match, match["away"], minute, max_minute),
            CYAN,
        )

    def render_replay_events(self, parent, match, minute, max_minute):
        self.clear(parent)
        self.section_title(parent, "KEY MOMENTS TO THIS MINUTE")
        shown = [event for event in self.timeline_events(match, max_minute) if event["minute"] <= minute]
        if not shown:
            tk.Label(
                parent,
                text="No tracked moments yet at this point in the replay.",
                bg=PANEL_DARK,
                fg=MUTED,
                font=FONT_SMALL,
                anchor="w",
                padx=10,
                pady=10,
            ).pack(fill="x")
            return

        for event in shown[-5:]:
            row = tk.Frame(parent, bg=PANEL_DARK)
            row.pack(fill="x", padx=10, pady=3)
            pill = tk.Label(
                row,
                text=event["minute_text"],
                bg="#243244",
                fg=TEXT,
                font=FONT_MONO_SMALL,
                width=6,
                pady=4,
            )
            pill.pack(side="left")
            event_tag = tk.Label(
                row,
                text=event["event"],
                bg=PANEL_DARK,
                fg=self.event_color(event["event"]),
                font=FONT_BOLD,
                width=8,
                anchor="w",
            )
            event_tag.pack(side="left", padx=(8, 10))
            team = tk.Label(row, text=event["team"], bg=PANEL_DARK, fg=TEXT, font=FONT_BOLD, width=16, anchor="w")
            team.pack(side="left")
            detail = tk.Label(row, text=event["detail"], bg=PANEL_DARK, fg=MUTED, font=FONT_SMALL, anchor="w")
            detail.pack(side="left", fill="x", expand=True)

    def render_lineups_tab(self, parent, match):
        minute = self.current_replay_minute(match)
        max_minute = self.stats_max_minute(match)
        self.section_title(parent, "LINE-UPS & SHAPE")
        self.render_replay_state_note(parent, minute, max_minute)

        summary = self.info_card(parent)
        summary_row = tk.Frame(summary, bg=PANEL_DARK)
        summary_row.pack(fill="x", padx=10, pady=8)
        for label, value in [
            (match["home"], self.lineup_formation(match, "home", minute)),
            ("Replay", f"{minute:02d}'"),
            (match["away"], self.lineup_formation(match, "away", minute)),
        ]:
            box = tk.Frame(summary_row, bg="#243244")
            box.pack(side="left", expand=True, fill="x", padx=3)
            tk.Label(box, text=label, bg="#243244", fg=MUTED, font=FONT_SMALL).pack(pady=(6, 2))
            tk.Label(box, text=value, bg="#243244", fg=TEXT, font=FONT_BOLD).pack(pady=(0, 6))

        pitch_card = self.info_card(parent)
        pitch = tk.Canvas(pitch_card, bg="#56761b", height=560, highlightthickness=0)
        pitch.pack(fill="both", expand=True, padx=8, pady=8)
        self.draw_side_pitch(pitch, match, minute)

        notes = self.info_card(parent)
        notes.pack(fill="x", pady=(0, 4))
        tk.Label(notes, text="LINE-UP NOTES", bg=PANEL_DARK, fg=CYAN, font=FONT_BOLD, anchor="w").pack(fill="x", padx=10, pady=(8, 4))
        for line in self.lineup_notes(match, minute):
            tk.Label(notes, text=f"+ {line}", bg=PANEL_DARK, fg=MUTED, font=FONT_SMALL, anchor="w", justify="left").pack(fill="x", padx=10, pady=2)

    def render_chat_tab(self, parent, match):
        self.section_title(parent, "MATCH CHAT")
        minute = self.current_replay_minute(match)
        active_room = self.active_chat_room(match)
        room = self.info_card(parent)
        top = tk.Frame(room, bg=PANEL_DARK)
        top.pack(fill="x", padx=10, pady=(8, 4))
        tk.Label(
            top,
            text=f"{match['home']} vs {match['away']}  |  dedicated room",
            bg=PANEL_DARK,
            fg=TEXT,
            font=FONT_BOLD,
            anchor="w",
        ).pack(side="left")
        tk.Label(
            top,
            text=f"Replay {minute:02d}'",
            bg=PANEL_DARK,
            fg=ORANGE,
            font=FONT_BOLD,
            anchor="e",
        ).pack(side="right")
        tk.Label(
            room,
            text="This thread follows the match before, during, and after. Open takes, live reactions, and agent notes all stay attached to this match.",
            bg=PANEL_DARK,
            fg=MUTED,
            font=FONT_SMALL,
            anchor="w",
            justify="left",
            padx=10,
            pady=2,
        ).pack(fill="x", pady=(0, 8))

        rooms = tk.Frame(parent, bg=PANEL)
        rooms.pack(fill="x", pady=(0, 6))
        for text in self.chat_rooms():
            active = text == active_room
            count = self.chat_room_count(match, text)
            badge = self.chat_room_badge(match, text)
            btn = tk.Button(
                rooms,
                text=f"{text} {count} {badge}".strip(),
                bg=TEXT if active else PANEL_DARK,
                fg=BG if active else MUTED,
                activebackground=TEXT if active else "#243244",
                activeforeground=BG if active else TEXT,
                font=FONT_BOLD,
                padx=14,
                pady=6,
                relief="flat",
                command=lambda room_name=text, current=match: self.set_chat_room(current, room_name),
            )
            btn.pack(side="left", padx=(0, 8))

        self.section_title(parent, "PREDICTION CHALLENGE")
        self.render_prediction_challenge(parent, match)

        self.section_title(parent, "COMMUNITY PROFILES")
        self.render_profile_board(parent)

        self.section_title(parent, "PLATFORM VS COMMUNITY")
        self.render_platform_community_board(parent)

        feed = self.info_card(parent)
        feed.pack(fill="both", expand=True, pady=(0, 6))
        chat_canvas = tk.Canvas(feed, bg=PANEL_DARK, height=360, highlightthickness=0)
        chat_scroll = tk.Scrollbar(feed, orient="vertical", command=chat_canvas.yview)
        chat_canvas.configure(yscrollcommand=chat_scroll.set)
        chat_canvas.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        chat_scroll.pack(side="right", fill="y", padx=(0, 8), pady=8)

        feed_body = tk.Frame(chat_canvas, bg=PANEL_DARK)
        window_id = chat_canvas.create_window((0, 0), window=feed_body, anchor="nw")

        def on_feed_configure(_event):
            chat_canvas.configure(scrollregion=chat_canvas.bbox("all"))

        def on_canvas_configure(event):
            chat_canvas.itemconfigure(window_id, width=event.width)

        feed_body.bind("<Configure>", on_feed_configure)
        chat_canvas.bind("<Configure>", on_canvas_configure)

        for item in self.chat_thread(match):
            self.render_chat_message(feed_body, item)

        compose = self.info_card(parent)
        compose.pack(fill="x", pady=(0, 4))
        row = tk.Frame(compose, bg=PANEL_DARK)
        row.pack(fill="x", padx=10, pady=10)
        entry = tk.Entry(
            row,
            textvariable=self.chat_message,
            bg="#0f172a",
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=FONT_SMALL,
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=7)
        entry.bind("<Return>", lambda _event, current=match: self.post_chat_message(current))
        self.button(row, "Post", CYAN_DARK, lambda current=match: self.post_chat_message(current), width=10, pady=7).pack(side="left", padx=(0, 6))
        self.button(row, "Agent Note", ORANGE, lambda current=match: self.add_agent_note(current), width=12, pady=7).pack(side="left")

    def render_table_tab(self, parent, match):
        self.section_title(parent, f"{match['league']} TABLE")
        table = self.info_card(parent)
        header = tk.Frame(table, bg=PANEL_DARK)
        header.pack(fill="x", padx=8, pady=(8, 4))
        for text, width in [("#", 4), ("Team", 22), ("P", 5), ("GD", 6), ("PTS", 6), ("W", 5)]:
            tk.Label(header, text=text, bg=PANEL_DARK, fg=MUTED, font=FONT_SMALL, width=width, anchor="w").pack(side="left")
        for pos, team, played, gd, pts, wins in self.table_rows(match):
            active = team in (match["home"], match["away"])
            row = tk.Frame(table, bg="#263244" if active else PANEL_DARK)
            row.pack(fill="x", padx=8, pady=1)
            color = ORANGE if active else TEXT
            for text, width, fg in [
                (str(pos), 4, MUTED),
                (team, 22, color),
                (str(played), 5, MUTED),
                (f"{gd:+}", 6, MUTED),
                (str(pts), 6, TEXT),
                (str(wins), 5, MUTED),
            ]:
                tk.Label(row, text=text, bg=row.cget("bg"), fg=fg, font=FONT_BOLD if active else FONT_SMALL, width=width, anchor="w").pack(side="left", pady=5)

    def render_h2h_tab(self, parent, match):
        self.section_title(parent, "HEAD TO HEAD")
        filters = tk.Frame(parent, bg=PANEL)
        filters.pack(fill="x", pady=(0, 8))
        for text, active in [("H2H", True), (match["home"], False), (match["away"], False)]:
            tk.Label(
                filters,
                text=text,
                bg=TEXT if active else PANEL_DARK,
                fg=BG if active else MUTED,
                font=FONT_BOLD,
                padx=14,
                pady=6,
            ).pack(side="left", padx=(0, 8))

        for season, home, away, home_score, away_score in self.h2h_rows(match):
            card = self.info_card(parent)
            tk.Label(card, text=season, bg=PANEL_DARK, fg=CYAN, font=FONT_BOLD, anchor="w").pack(fill="x", padx=10, pady=(8, 2))
            for team, score in [(home, home_score), (away, away_score)]:
                row = tk.Frame(card, bg=PANEL_DARK)
                row.pack(fill="x", padx=10, pady=2)
                tk.Label(row, text=self.team_initials(team), bg=PANEL_DARK, fg=MUTED, font=FONT_MONO_SMALL, width=6).pack(side="left")
                tk.Label(row, text=team, bg=PANEL_DARK, fg=TEXT, font=FONT_UI, anchor="w").pack(side="left", fill="x", expand=True)
                tk.Label(row, text=str(score), bg=PANEL_DARK, fg=TEXT, font=FONT_BOLD, width=4).pack(side="right")

    def chat_rooms(self):
        return ["Open Room", "Value Talk", "Live Pulse", "Post-match"]

    def chat_room_count(self, match, room_name):
        rooms = self.match_chats.get(match["id"])
        if not isinstance(rooms, dict):
            rooms = self.seed_chat_rooms(match)
            self.match_chats[match["id"]] = rooms
        return len(rooms.get(room_name, []))

    def chat_room_badge(self, match, room_name):
        count = self.chat_room_count(match, room_name)
        if room_name == "Live Pulse" and match["status"] == "LIVE":
            return "LIVE"
        if count >= 5:
            return "HOT"
        if room_name == "Post-match" and self.match_finished(match):
            return "FT"
        return ""

    def active_chat_room(self, match):
        if match["id"] not in self.match_chat_room:
            self.match_chat_room[match["id"]] = "Open Room"
        return self.match_chat_room[match["id"]]

    def set_chat_room(self, match, room_name):
        self.match_chat_room[match["id"]] = room_name
        self.chat_message.set("")
        self.render_chat_preview()
        if self.tab_name.get() == "Chat":
            self.render_tab()

    def chat_thread(self, match):
        if match["id"] not in self.match_chats or not isinstance(self.match_chats[match["id"]], dict):
            self.match_chats[match["id"]] = self.seed_chat_rooms(match)
        room = self.active_chat_room(match)
        return self.match_chats[match["id"]].setdefault(room, [])

    def seed_chat_rooms(self, match):
        minute = self.stats_reference_minute(match)
        return {
            "Open Room": self.seed_chat_thread(match, "Open Room", minute),
            "Value Talk": self.seed_chat_thread(match, "Value Talk", minute),
            "Live Pulse": self.seed_chat_thread(match, "Live Pulse", minute),
            "Post-match": self.seed_chat_thread(match, "Post-match", minute),
        }

    def seed_chat_thread(self, match, room_name, minute):
        minute = self.stats_reference_minute(match)
        status_text = "pre-match room is open" if match["status"] == "UP" else f"live room rolling at {minute:02d}'"
        seeds = {
            "Open Room": [
                {
                    "author": "EdgeAgent",
                    "tag": "agent",
                    "time": self.chat_time_label(match),
                    "text": f"{match['home']} vs {match['away']} {status_text}. Market edge is {match['edge']:+.1f}; good room to track price vs momentum.",
                },
                {
                    "author": "ValueHunter",
                    "tag": "community",
                    "time": self.chat_time_label(match),
                    "text": f"I want to see whether {match['away']} keeps the same pressure level if this reaches the last 20 minutes.",
                },
                {
                    "author": "MatchPulse",
                    "tag": "community",
                    "time": self.chat_time_label(match),
                    "text": "Thread stays attached to this match before kickoff, during live play, and after full-time.",
                },
            ],
            "Value Talk": [
                {
                    "author": "EdgeAgent",
                    "tag": "agent",
                    "time": self.chat_time_label(match),
                    "text": f"Value room open. Best angle right now is how the {match['edge']:+.1f} edge compares to available book prices.",
                },
                {
                    "author": "PriceWatcher",
                    "tag": "community",
                    "time": self.chat_time_label(match),
                    "text": "I only care whether the line is behind the state of the match. Everything else is noise until price moves.",
                },
            ],
            "Live Pulse": [
                {
                    "author": "EdgeAgent",
                    "tag": "agent",
                    "time": self.chat_time_label(match),
                    "text": f"Live pulse room at {minute:02d}'. Use this for momentum, pressure swings, and replay-minute reactions.",
                },
                {
                    "author": "PulseCheck",
                    "tag": "community",
                    "time": self.chat_time_label(match),
                    "text": "The room should follow the replay minute so people are arguing about the same state, not different moments.",
                },
            ],
            "Post-match": [
                {
                    "author": "EdgeAgent",
                    "tag": "agent",
                    "time": self.chat_time_label(match),
                    "text": "Post-match room is ready. Good place for reviewing what the market, replay, and final result actually said.",
                },
            ],
        }
        return seeds.get(room_name, seeds["Open Room"])

    def render_chat_message(self, parent, item):
        bubble = tk.Frame(parent, bg=PANEL_DARK)
        bubble.pack(fill="x", padx=10, pady=4)
        top = tk.Frame(bubble, bg=PANEL_DARK)
        top.pack(fill="x")
        color = ORANGE if item["tag"] == "agent" else GREEN if item["tag"] == "you" else CYAN
        tk.Label(top, text=item["author"], bg=PANEL_DARK, fg=color, font=FONT_BOLD, anchor="w").pack(side="left")
        tk.Label(top, text=item["time"], bg=PANEL_DARK, fg=MUTED, font=FONT_SMALL, anchor="e").pack(side="right")
        tk.Label(
            bubble,
            text=item["text"],
            bg=PANEL_DARK,
            fg=TEXT,
            font=FONT_SMALL,
            anchor="w",
            justify="left",
            wraplength=720,
        ).pack(fill="x", pady=(2, 0))
        tk.Frame(bubble, bg="#243244", height=1).pack(fill="x", pady=(8, 0))

    def render_prediction_challenge(self, parent, match):
        board = self.info_card(parent)
        board.pack(fill="x", pady=(0, 6))
        entries = self.challenge_entries(match)
        leader = entries[0]

        top = tk.Frame(board, bg=PANEL_DARK)
        top.pack(fill="x", padx=10, pady=(8, 6))
        tk.Label(top, text="Beat The Platform", bg=PANEL_DARK, fg=TEXT, font=FONT_BOLD, anchor="w").pack(side="left")
        tk.Label(top, text=f"Leader: {leader['name']}  |  {leader['accuracy']}%", bg=PANEL_DARK, fg=ORANGE, font=FONT_SMALL, anchor="e").pack(side="right")

        score_row = tk.Frame(board, bg=PANEL_DARK)
        score_row.pack(fill="x", padx=10, pady=(0, 8))
        platform = self.platform_challenge_entry(match)
        for label, value in [
            ("Platform", f"{platform['pick']}  {platform['confidence']}%"),
            ("Guests", str(len([row for row in entries if row["tag"] != "platform"]))),
            ("Market", self.guest_market.get()),
        ]:
            cell = tk.Frame(score_row, bg="#243244")
            cell.pack(side="left", expand=True, fill="x", padx=3)
            tk.Label(cell, text=label, bg="#243244", fg=MUTED, font=FONT_SMALL).pack(pady=(5, 2))
            tk.Label(cell, text=value, bg="#243244", fg=TEXT, font=FONT_BOLD).pack(pady=(0, 6))

        form = tk.Frame(board, bg=PANEL_DARK)
        form.pack(fill="x", padx=10, pady=(0, 8))
        tk.Label(form, text="Handle", bg=PANEL_DARK, fg=MUTED, font=FONT_SMALL).pack(side="left")
        entry = tk.Entry(
            form,
            textvariable=self.guest_handle,
            bg="#0f172a",
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=FONT_SMALL,
            width=14,
        )
        entry.pack(side="left", padx=(6, 10), ipady=5)

        market_frame = tk.Frame(form, bg=PANEL_DARK)
        market_frame.pack(side="left", padx=(0, 10))
        for market in ("1X2", "O/U 2.5", "BTTS"):
            active = self.guest_market.get() == market
            tk.Button(
                market_frame,
                text=market,
                bg=TEXT if active else "#243244",
                fg=BG if active else MUTED,
                activebackground=TEXT if active else "#334155",
                activeforeground=BG if active else TEXT,
                relief="flat",
                font=FONT_SMALL,
                padx=10,
                pady=5,
                command=lambda value=market, current=match: self.set_guest_market(value, current),
            ).pack(side="left", padx=3)

        pick_frame = tk.Frame(board, bg=PANEL_DARK)
        pick_frame.pack(fill="x", padx=10, pady=(0, 8))
        for option in self.challenge_pick_options(match):
            active = self.guest_pick.get() == option
            tk.Button(
                pick_frame,
                text=option,
                bg=ORANGE if active else "#243244",
                fg=TEXT if active else MUTED,
                activebackground=ORANGE,
                activeforeground=TEXT,
                relief="flat",
                font=FONT_SMALL,
                padx=12,
                pady=6,
                command=lambda value=option: self.guest_pick.set(value),
            ).pack(side="left", padx=(0, 6))
        self.button(
            pick_frame,
            "Submit Pick",
            CYAN_DARK,
            lambda current=match: self.submit_guest_prediction(current),
            width=12,
            pady=7,
        ).pack(side="right")

        header = tk.Frame(board, bg=PANEL_DARK)
        header.pack(fill="x", padx=10, pady=(0, 2))
        for text, width in [("#", 4), ("NAME", 14), ("MARKET", 12), ("PICK", 14), ("CONF", 8), ("ACC", 8)]:
            tk.Label(header, text=text, bg=PANEL_DARK, fg=ORANGE, font=FONT_MONO_SMALL, width=width, anchor="w").pack(side="left")

        for idx, row in enumerate(entries[:6], start=1):
            line = tk.Frame(board, bg=ROW if row["tag"] != "platform" else ROW_ALT)
            line.pack(fill="x", padx=10, pady=1)
            name_color = ORANGE if row["tag"] == "platform" else GREEN if row["tag"] == "you" else TEXT
            for value, width, color in [
                (str(idx), 4, MUTED),
                (row["name"], 14, name_color),
                (row["market"], 12, CYAN),
                (row["pick"], 14, TEXT),
                (f"{row['confidence']}%", 8, ORANGE),
                (f"{row['accuracy']}%", 8, GREEN),
            ]:
                tk.Label(line, text=value, bg=line.cget("bg"), fg=color, font=FONT_MONO_SMALL, width=width, anchor="w").pack(side="left", pady=4)

    def render_profile_board(self, parent):
        card = self.info_card(parent)
        card.pack(fill="x", pady=(0, 6))
        highlight = tk.Frame(card, bg=PANEL_DARK)
        highlight.pack(fill="x", padx=10, pady=(8, 8))
        featured = [
            self.profile_lookup("Edge Platform"),
            self.top_guest_profile(),
            self.profile_lookup(self.guest_handle.get().strip() or "Guest001"),
        ]
        labels = ["Platform", "Top Guest", "Your Handle"]
        for idx, profile in enumerate(featured):
            box = tk.Frame(highlight, bg="#243244")
            box.pack(side="left", expand=True, fill="x", padx=3)
            tk.Label(box, text=labels[idx], bg="#243244", fg=MUTED, font=FONT_SMALL).pack(pady=(6, 2))
            tk.Label(box, text=profile["name"], bg="#243244", fg=ORANGE if profile["tag"] == "platform" else GREEN if profile["tag"] == "you" else TEXT, font=FONT_BOLD).pack()
            tk.Label(box, text=f"{profile['badge']}  |  streak {profile['streak']}", bg="#243244", fg=CYAN, font=FONT_SMALL).pack(pady=(2, 2))
            tk.Label(box, text=f"hit {profile['hit_rate']}%  |  open {profile['open']}", bg="#243244", fg=TEXT, font=FONT_SMALL).pack(pady=(0, 6))

        header = tk.Frame(card, bg=PANEL_DARK)
        header.pack(fill="x", padx=10, pady=(8, 4))
        for text, width in [("USER", 14), ("W-L-P", 10), ("HIT", 8), ("OPEN", 8), ("BEST", 14), ("BADGE", 10)]:
            tk.Label(header, text=text, bg=PANEL_DARK, fg=ORANGE, font=FONT_MONO_SMALL, width=width, anchor="w").pack(side="left")

        for row in self.profile_rows()[:6]:
            line = tk.Frame(card, bg=ROW if row["tag"] != "platform" else ROW_ALT)
            line.pack(fill="x", padx=10, pady=1)
            name_color = ORANGE if row["tag"] == "platform" else GREEN if row["tag"] == "you" else TEXT
            values = [
                (row["name"], 14, name_color),
                (f"{row['wins']}-{row['losses']}-{row['pushes']}", 10, TEXT),
                (f"{row['hit_rate']}%", 8, GREEN),
                (str(row["open"]), 8, MUTED),
                (row["best_market"], 14, CYAN),
                (row["badge"], 10, ORANGE if row["badge"] == "Crown" else CYAN if row["badge"] == "Hot" else MUTED),
            ]
            for value, width, color in values:
                tk.Label(line, text=value, bg=line.cget("bg"), fg=color, font=FONT_MONO_SMALL, width=width, anchor="w").pack(side="left", pady=4)

    def render_platform_community_board(self, parent):
        card = self.info_card(parent)
        card.pack(fill="x", pady=(0, 6))
        summary = self.platform_vs_community_summary()
        top = tk.Frame(card, bg=PANEL_DARK)
        top.pack(fill="x", padx=10, pady=(8, 6))
        tk.Label(top, text="Long-run settled score", bg=PANEL_DARK, fg=TEXT, font=FONT_BOLD, anchor="w").pack(side="left")
        tk.Label(top, text=f"{summary['winner']} on top", bg=PANEL_DARK, fg=ORANGE, font=FONT_SMALL, anchor="e").pack(side="right")

        row = tk.Frame(card, bg=PANEL_DARK)
        row.pack(fill="x", padx=10, pady=(0, 8))
        for label, value, color in [
            ("Platform Hit", f"{summary['platform_hit']}%", ORANGE),
            ("Community Hit", f"{summary['community_hit']}%", CYAN),
            ("Settled Picks", str(summary["settled"]), GREEN),
            ("Open Picks", str(summary["open"]), MUTED),
        ]:
            cell = tk.Frame(row, bg="#243244")
            cell.pack(side="left", expand=True, fill="x", padx=3)
            tk.Label(cell, text=label, bg="#243244", fg=MUTED, font=FONT_SMALL).pack(pady=(5, 2))
            tk.Label(cell, text=value, bg="#243244", fg=color, font=FONT_BOLD).pack(pady=(0, 6))

        notes = tk.Frame(card, bg=PANEL_DARK)
        notes.pack(fill="x", padx=10, pady=(0, 8))
        for text in [
            f"Platform settled record: {summary['platform_wins']}-{summary['platform_losses']}-{summary['platform_pushes']}",
            f"Community settled record: {summary['community_wins']}-{summary['community_losses']}-{summary['community_pushes']}",
            "Open picks stay out of hit-rate scoring until the match is settled.",
        ]:
            tk.Label(notes, text=f"+ {text}", bg=PANEL_DARK, fg=MUTED, font=FONT_SMALL, anchor="w").pack(fill="x", pady=1)

    def chat_time_label(self, match):
        minute = self.current_replay_minute(match)
        if match["status"] == "UP" and minute == 0:
            return "Pre | now"
        return f"{minute:02d}' | now"

    def seed_challenge_history(self):
        return [
            self.make_history_record("Edge Platform", "platform", "1X2", "Liverpool", 45, 1, 1, 1),
            self.make_history_record("Edge Platform", "platform", "O/U 2.5", "Under 2.5", 58, 0, 0, 1),
            self.make_history_record("Edge Platform", "platform", "BTTS", "Yes", 61, 2, 1, 1),
            self.make_history_record("SharpTom", "guest", "1X2", "Liverpool", 58, 1, 1, 1),
            self.make_history_record("SharpTom", "guest", "BTTS", "No", 51, 0, 0, 1),
            self.make_history_record("OddsMuse", "guest", "O/U 2.5", "Under 2.5", 54, 0, 0, 1),
            self.make_history_record("OddsMuse", "guest", "1X2", "Draw", 31, 1, 1, 1),
            self.make_history_record("PulseRita", "guest", "BTTS", "Yes", 61, 2, 1, 1),
            self.make_history_record("PulseRita", "guest", "1X2", "Home", 44, 0, 2, 2),
            self.make_history_record("Guest001", "you", "1X2", "Man City", 52, 1, 0, 0),
            self.make_history_record("Guest001", "you", "O/U 2.5", "Over 2.5", 57, 2, 1, 1),
        ]

    def make_history_record(self, name, tag, market, pick, confidence, home_score, away_score, match_id):
        result = self.settle_pick(market, pick, home_score, away_score)
        return {
            "name": name,
            "tag": tag,
            "market": market,
            "pick": pick,
            "confidence": confidence,
            "home_score": home_score,
            "away_score": away_score,
            "match_id": match_id,
            "status": "Settled",
            "result": result,
        }

    def challenge_entries(self, match):
        if match["id"] not in self.match_challenges:
            self.match_challenges[match["id"]] = self.seed_challenge_entries(match)
        rows = [self.platform_challenge_entry(match)] + self.match_challenges[match["id"]]
        return sorted(rows, key=lambda item: (item["accuracy"], item["confidence"]), reverse=True)

    def seed_challenge_entries(self, match):
        return [
            {"name": "SharpTom", "tag": "guest", "market": "1X2", "pick": match["away"], "confidence": 58, "accuracy": 67},
            {"name": "OddsMuse", "tag": "guest", "market": "O/U 2.5", "pick": "Under 2.5", "confidence": 54, "accuracy": 63},
            {"name": "PulseRita", "tag": "guest", "market": "BTTS", "pick": "Yes", "confidence": 61, "accuracy": 65},
        ]

    def platform_challenge_entry(self, match):
        snapshot = self.analysis_snapshot(match)
        return {
            "name": "Edge Platform",
            "tag": "platform",
            "market": "1X2",
            "pick": snapshot["market"].split("|")[-1].replace("pick", "").strip(),
            "confidence": snapshot["confidence"],
            "accuracy": self.profile_lookup("Edge Platform")["hit_rate"],
        }

    def set_guest_market(self, value, match):
        self.guest_market.set(value)
        options = self.challenge_pick_options(match)
        if self.guest_pick.get() not in options:
            self.guest_pick.set(options[0])
        if self.tab_name.get() == "Chat":
            self.render_tab()

    def challenge_pick_options(self, match):
        market = self.guest_market.get()
        if market == "O/U 2.5":
            return ["Over 2.5", "Under 2.5"]
        if market == "BTTS":
            return ["Yes", "No"]
        return [match["home"], "Draw", match["away"]]

    def submit_guest_prediction(self, match):
        handle = self.guest_handle.get().strip() or "Guest001"
        pick = self.guest_pick.get().strip()
        if not pick:
            options = self.challenge_pick_options(match)
            pick = options[0]
            self.guest_pick.set(pick)
        rows = self.match_challenges.setdefault(match["id"], self.seed_challenge_entries(match))
        confidence = self.challenge_confidence(match, pick)
        accuracy = max(51, min(79, confidence + 8 - (match["id"] % 4)))
        rows.append(
            {
                "name": handle,
                "tag": "you",
                "market": self.guest_market.get(),
                "pick": pick,
                "confidence": confidence,
                "accuracy": accuracy,
            }
        )
        self.challenge_history.append(
            {
                "name": handle,
                "tag": "you",
                "market": self.guest_market.get(),
                "pick": pick,
                "confidence": confidence,
                "home_score": match["home_score"],
                "away_score": match["away_score"],
                "match_id": match["id"],
                "status": "Live" if match["status"] == "LIVE" else "Pending",
                "result": "Open",
            }
        )
        self.tracker_status.config(text=f"{handle} joined the challenge on {match['home']} vs {match['away']}.", fg=GREEN)
        self.render_chat_preview()
        if self.tab_name.get() == "Chat":
            self.render_tab()

    def challenge_confidence(self, match, pick):
        consensus = self.consensus_prediction(match)
        if pick == match["home"]:
            return consensus["home"]
        if pick == match["away"]:
            return consensus["away"]
        if pick == "Draw":
            return consensus["draw"]
        if pick == "Over 2.5":
            return min(78, int(round(match["over_price"])))
        if pick == "Under 2.5":
            return min(78, int(round(match["under_price"])))
        if pick == "Yes":
            return min(76, int(round((match["home_avg"] + match["away_avg"]) * 18)))
        return 100 - min(76, int(round((match["home_avg"] + match["away_avg"]) * 18)))

    def settle_pick(self, market, pick, home_score, away_score):
        if market == "1X2":
            outcome = "Draw" if home_score == away_score else "Home" if home_score > away_score else "Away"
            home_teams = {match["home"] for match in MATCHES}
            away_teams = {match["away"] for match in MATCHES}
            if pick == "Draw":
                mapped_pick = "Draw"
            elif pick == "Away" or pick in away_teams:
                mapped_pick = "Away"
            else:
                mapped_pick = "Home"
            return "W" if mapped_pick == outcome else "L"
        if market == "O/U 2.5":
            total = home_score + away_score
            outcome = "Over 2.5" if total >= 3 else "Under 2.5"
            return "W" if pick == outcome else "L"
        if market == "BTTS":
            outcome = "Yes" if home_score > 0 and away_score > 0 else "No"
            return "W" if pick == outcome else "L"
        return "P"

    def profile_rows(self):
        buckets = {}
        for item in self.challenge_history:
            row = buckets.setdefault(
                item["name"],
                {"name": item["name"], "tag": item["tag"], "wins": 0, "losses": 0, "pushes": 0, "open": 0, "best_market": item["market"], "history": []},
            )
            row["history"].append(item["result"])
            if item["status"] == "Settled":
                if item["result"] == "W":
                    row["wins"] += 1
                elif item["result"] == "L":
                    row["losses"] += 1
                else:
                    row["pushes"] += 1
            else:
                row["open"] += 1

        rows = []
        for row in buckets.values():
            settled = row["wins"] + row["losses"] + row["pushes"]
            hit_rate = 0 if settled == 0 else int(round((row["wins"] / max(1, settled)) * 100))
            row["hit_rate"] = hit_rate
            row["streak"] = self.profile_streak(row["history"])
            row["badge"] = self.profile_badge(row)
            rows.append(row)
        return sorted(rows, key=lambda item: (item["hit_rate"], item["wins"]), reverse=True)

    def profile_lookup(self, name):
        for row in self.profile_rows():
            if row["name"] == name:
                return row
        return {"name": name, "tag": "guest", "wins": 0, "losses": 0, "pushes": 0, "open": 0, "best_market": "1X2", "hit_rate": 0, "streak": "0", "badge": "New"}

    def top_guest_profile(self):
        guests = [row for row in self.profile_rows() if row["tag"] != "platform"]
        return guests[0] if guests else self.profile_lookup("Guest001")

    def profile_streak(self, history):
        streak_type = None
        streak_count = 0
        for result in reversed(history):
            if result not in ("W", "L"):
                continue
            if streak_type is None:
                streak_type = result
                streak_count = 1
            elif result == streak_type:
                streak_count += 1
            else:
                break
        if streak_type is None:
            return "0"
        return f"{streak_type}{streak_count}"

    def profile_badge(self, row):
        if row["tag"] == "platform":
            return "Crown"
        if row["streak"].startswith("W") and int(row["streak"][1:] or "0") >= 2:
            return "Hot"
        if row["open"] >= 2:
            return "Active"
        return "New"

    def platform_vs_community_summary(self):
        platform = {"wins": 0, "losses": 0, "pushes": 0, "open": 0}
        community = {"wins": 0, "losses": 0, "pushes": 0, "open": 0}
        for item in self.challenge_history:
            bucket = platform if item["tag"] == "platform" else community
            if item["status"] == "Settled":
                if item["result"] == "W":
                    bucket["wins"] += 1
                elif item["result"] == "L":
                    bucket["losses"] += 1
                else:
                    bucket["pushes"] += 1
            else:
                bucket["open"] += 1

        platform_settled = platform["wins"] + platform["losses"] + platform["pushes"]
        community_settled = community["wins"] + community["losses"] + community["pushes"]
        platform_hit = 0 if platform_settled == 0 else int(round((platform["wins"] / max(1, platform_settled)) * 100))
        community_hit = 0 if community_settled == 0 else int(round((community["wins"] / max(1, community_settled)) * 100))
        winner = "Platform" if platform_hit >= community_hit else "Community"
        return {
            "platform_hit": platform_hit,
            "community_hit": community_hit,
            "platform_wins": platform["wins"],
            "platform_losses": platform["losses"],
            "platform_pushes": platform["pushes"],
            "community_wins": community["wins"],
            "community_losses": community["losses"],
            "community_pushes": community["pushes"],
            "settled": platform_settled + community_settled,
            "open": platform["open"] + community["open"],
            "winner": winner,
        }

    def match_finished(self, match):
        return match.get("status") in ("FT", "FINISHED") or match.get("minute", 0) >= 90 and match.get("status") != "UP"

    def settle_match_challenges(self, match):
        changed = False
        for item in self.challenge_history:
            if item["match_id"] != match["id"] or item["status"] == "Settled":
                continue
            item["home_score"] = match["home_score"]
            item["away_score"] = match["away_score"]
            item["result"] = self.settle_pick(item["market"], item["pick"], match["home_score"], match["away_score"])
            item["status"] = "Settled"
            changed = True
        return changed

    def render_chat_preview(self):
        if self.chat_preview_body is None:
            return
        self.clear(self.chat_preview_body)
        match = self.current_match
        room = self.active_chat_room(match)
        thread = self.chat_thread(match)
        latest = thread[-3:]
        challenge = self.challenge_entries(match)[:3]
        header = tk.Frame(self.chat_preview_body, bg=PANEL_DARK)
        header.pack(fill="x", padx=8, pady=(8, 6))
        tk.Label(header, text=f"{match['home']} vs {match['away']}", bg=PANEL_DARK, fg=TEXT, font=FONT_BOLD, anchor="w").pack(fill="x")
        tk.Label(header, text=room, bg=PANEL_DARK, fg=CYAN, font=FONT_SMALL, anchor="w").pack(fill="x")
        for item in latest:
            row = tk.Frame(self.chat_preview_body, bg=PANEL_DARK)
            row.pack(fill="x", padx=8, pady=3)
            color = ORANGE if item["tag"] == "agent" else GREEN if item["tag"] == "you" else CYAN
            tk.Label(row, text=item["author"], bg=PANEL_DARK, fg=color, font=FONT_SMALL, width=10, anchor="w").pack(side="left")
            tk.Label(
                row,
                text=item["text"][:54] + ("..." if len(item["text"]) > 54 else ""),
                bg=PANEL_DARK,
                fg=MUTED,
                font=FONT_SMALL,
                anchor="w",
                justify="left",
            ).pack(side="left", fill="x", expand=True)
        tk.Label(
            self.chat_preview_body,
            text="Challenge",
            bg=PANEL_DARK,
            fg=ORANGE,
            font=FONT_BOLD,
            anchor="w",
            padx=8,
            pady=6,
        ).pack(fill="x")
        for idx, item in enumerate(challenge, start=1):
            row = tk.Frame(self.chat_preview_body, bg=PANEL_DARK)
            row.pack(fill="x", padx=8, pady=2)
            tk.Label(row, text=str(idx), bg=PANEL_DARK, fg=MUTED, font=FONT_SMALL, width=3, anchor="w").pack(side="left")
            tk.Label(row, text=item["name"], bg=PANEL_DARK, fg=ORANGE if item["tag"] == "platform" else GREEN if item["tag"] == "you" else TEXT, font=FONT_SMALL, width=14, anchor="w").pack(side="left")
            tk.Label(row, text=item["pick"], bg=PANEL_DARK, fg=CYAN, font=FONT_SMALL, width=12, anchor="w").pack(side="left")
            tk.Label(row, text=f"{item['accuracy']}%", bg=PANEL_DARK, fg=GREEN, font=FONT_SMALL, width=7, anchor="e").pack(side="right")
        tk.Label(
            self.chat_preview_body,
            text="Open the Chat tab for the full room and posting controls.",
            bg=PANEL_DARK,
            fg=MUTED,
            font=FONT_SMALL,
            anchor="w",
            padx=8,
            pady=6,
        ).pack(fill="x")

    def post_chat_message(self, match):
        text = self.chat_message.get().strip()
        if not text:
            self.tracker_status.config(text="Type a message for this match thread first.", fg=MUTED)
            return
        thread = self.chat_thread(match)
        thread.append({"author": "You", "tag": "you", "time": self.chat_time_label(match), "text": text})
        thread.append(self.agent_chat_reply(match, text))
        self.chat_message.set("")
        self.tracker_status.config(text=f"Posted into {match['home']} vs {match['away']} chat.", fg=GREEN)
        self.render_chat_preview()
        if self.tab_name.get() == "Chat":
            self.render_tab()

    def add_agent_note(self, match):
        thread = self.chat_thread(match)
        thread.append(self.agent_chat_reply(match, "agent note"))
        self.tracker_status.config(text=f"Agent note added to {match['home']} vs {match['away']} chat.", fg=CYAN)
        self.render_chat_preview()
        if self.tab_name.get() == "Chat":
            self.render_tab()

    def agent_chat_reply(self, match, prompt_text):
        minute = self.current_replay_minute(match)
        lower = prompt_text.lower()
        if "shot" in lower or "xg" in lower:
            text = f"EdgeAgent: at {minute:02d}' the shot/xG angle still leans toward the {self.resolve_quick_find_target('shots')[1]} view. Quick Find can jump there fast."
        elif "line" in lower or "odds" in lower or "price" in lower:
            text = f"EdgeAgent: the book side is still worth checking against the current room take. Right panel has the discrepancy view, and this thread can debate whether it is real or noise."
        elif "lineup" in lower or "sub" in lower:
            text = f"EdgeAgent: lineup shape at {minute:02d}' is live in the Line-ups tab now, and sub rings highlight the changes."
        else:
            text = f"EdgeAgent: room note for {match['home']} vs {match['away']} at {minute:02d}' - keep the debate tied to replay minute, market move, and whether the pressure is translating into real edge."
        return {"author": "EdgeAgent", "tag": "agent", "time": self.chat_time_label(match), "text": text}

    def mini_bar(self, parent, value, color):
        bar = tk.Frame(parent, bg="#334155", height=8)
        bar.pack(side="left", fill="x", expand=True, padx=8)
        fill = tk.Frame(bar, bg=color, height=8)
        fill.place(relx=0, rely=0, relwidth=max(0.04, min(value / 100, 1)), relheight=1)

    def stat_bar(self, parent, label, home, away):
        row = tk.Frame(parent, bg=PANEL)
        row.pack(fill="x", pady=5)
        top = tk.Frame(row, bg=PANEL)
        top.pack(fill="x")
        tk.Label(top, text=str(home), bg=PANEL, fg=TEXT, font=FONT_BOLD, width=8, anchor="w").pack(side="left")
        tk.Label(top, text=label, bg=PANEL, fg=MUTED, font=FONT_SMALL).pack(side="left", fill="x", expand=True)
        tk.Label(top, text=str(away), bg=PANEL, fg=TEXT, font=FONT_BOLD, width=8, anchor="e").pack(side="right")
        bar = tk.Frame(row, bg="#263244", height=9)
        bar.pack(fill="x", pady=(2, 0))
        total = max(float(home) + float(away), 1.0)
        left_weight = max(int((float(home) / total) * 100), 1)
        right_weight = max(100 - left_weight, 1)
        bar.grid_columnconfigure(0, weight=left_weight)
        bar.grid_columnconfigure(1, weight=right_weight)
        tk.Frame(bar, bg="#38bdf8", height=9).grid(row=0, column=0, sticky="ew")
        tk.Frame(bar, bg=ORANGE, height=9).grid(row=0, column=1, sticky="ew")

    def formation_line(self, parent, players, circle_bg, circle_fg):
        row = tk.Frame(parent, bg="#4d7112")
        row.pack(fill="x", pady=9)
        for idx, player in enumerate(players, start=1):
            slot = tk.Frame(row, bg="#4d7112")
            slot.pack(side="left", expand=True)
            tk.Label(slot, text=str(idx), bg=circle_bg, fg=circle_fg, font=FONT_BOLD, width=3, pady=4).pack()
            tk.Label(slot, text=player, bg="#4d7112", fg=TEXT, font=FONT_SMALL).pack()

    def lineup_formation(self, match, side, minute):
        if side == "home":
            return "4-3-3" if minute < 58 else "4-2-3-1"
        return "3-5-2" if minute < 63 else "4-4-2"

    def lineup_players(self, match, side, minute):
        if side == "home":
            players = [
                {"name": "Ederson", "number": 31, "x": 0.50, "y": 0.92},
                {"name": "Walker", "number": 2, "x": 0.18, "y": 0.79},
                {"name": "Dias", "number": 3, "x": 0.38, "y": 0.76},
                {"name": "Gvardiol", "number": 24, "x": 0.62, "y": 0.76},
                {"name": "Ake", "number": 6, "x": 0.82, "y": 0.79},
                {"name": "Rodri", "number": 16, "x": 0.50, "y": 0.63},
                {"name": "De Bruyne", "number": 17, "x": 0.30, "y": 0.57},
                {"name": "Bernardo", "number": 20, "x": 0.70, "y": 0.57},
                {"name": "Foden", "number": 47, "x": 0.20, "y": 0.38},
                {"name": "Haaland", "number": 9, "x": 0.50, "y": 0.31},
                {"name": "Doku", "number": 11, "x": 0.80, "y": 0.38},
            ]
            if minute >= 58:
                players[10] = {"name": "Grealish", "number": 10, "x": 0.80, "y": 0.44, "sub": True}
                players[6] = {"name": "Kovacic", "number": 8, "x": 0.34, "y": 0.60, "sub": True}
            return players

        players = [
            {"name": "Alisson", "number": 1, "x": 0.50, "y": 0.08},
            {"name": "Konate", "number": 5, "x": 0.24, "y": 0.19},
            {"name": "Van Dijk", "number": 4, "x": 0.50, "y": 0.16},
            {"name": "Robertson", "number": 26, "x": 0.76, "y": 0.19},
            {"name": "Alexander-Arnold", "number": 66, "x": 0.12, "y": 0.32},
            {"name": "Mac Allister", "number": 10, "x": 0.34, "y": 0.30},
            {"name": "Szoboszlai", "number": 8, "x": 0.50, "y": 0.28},
            {"name": "Gravenberch", "number": 38, "x": 0.66, "y": 0.30},
            {"name": "Diaz", "number": 7, "x": 0.88, "y": 0.32},
            {"name": "Salah", "number": 11, "x": 0.36, "y": 0.47},
            {"name": "Nunez", "number": 9, "x": 0.64, "y": 0.47},
        ]
        if minute >= 63:
            players[9] = {"name": "Jota", "number": 20, "x": 0.34, "y": 0.44, "sub": True}
            players[6] = {"name": "Jones", "number": 17, "x": 0.50, "y": 0.28, "sub": True}
        return players

    def draw_side_pitch(self, canvas, match, minute):
        canvas.delete("all")
        width = max(canvas.winfo_width(), 920)
        height = max(canvas.winfo_height(), 560)
        margin = 24

        canvas.create_rectangle(margin, margin, width - margin, height - margin, outline="#d5e59b", width=2)
        canvas.create_line(width / 2, margin, width / 2, height - margin, fill="#d5e59b", width=2)
        canvas.create_oval(width / 2 - 58, height / 2 - 58, width / 2 + 58, height / 2 + 58, outline="#d5e59b", width=2)
        canvas.create_oval(width / 2 - 4, height / 2 - 4, width / 2 + 4, height / 2 + 4, fill="#d5e59b", outline="")

        self.draw_side_penalty_box(canvas, width, height, margin, left_side=True)
        self.draw_side_penalty_box(canvas, width, height, margin, left_side=False)

        home_players = self.lineup_players(match, "home", minute)
        away_players = self.lineup_players(match, "away", minute)

        canvas.create_text(margin + 8, 10, text=f"{match['home']}  {self.lineup_formation(match, 'home', minute)}", fill=TEXT, font=FONT_BOLD, anchor="nw")
        canvas.create_text(width - margin - 8, 10, text=f"{match['away']}  {self.lineup_formation(match, 'away', minute)}", fill=TEXT, font=FONT_BOLD, anchor="ne")

        self.draw_team_side_pitch(canvas, home_players, width, height, margin, side="left", is_home=True)
        self.draw_team_side_pitch(canvas, away_players, width, height, margin, side="right", is_home=False)

    def draw_side_penalty_box(self, canvas, width, height, margin, left_side=True):
        if left_side:
            x0 = margin
            x1 = margin + 140
            six_x1 = margin + 56
        else:
            x0 = width - margin - 140
            x1 = width - margin
            six_x1 = width - margin - 56
        canvas.create_rectangle(x0, height * 0.22, x1, height * 0.78, outline="#d5e59b", width=2)
        if left_side:
            canvas.create_rectangle(x0, height * 0.38, six_x1, height * 0.62, outline="#d5e59b", width=2)
        else:
            canvas.create_rectangle(six_x1, height * 0.38, x1, height * 0.62, outline="#d5e59b", width=2)

    def draw_team_side_pitch(self, canvas, players, width, height, margin, side, is_home):
        circle_fill = "#101826" if is_home else "#f8fafc"
        text_fill = TEXT if is_home else "#0f172a"
        accent = ORANGE if is_home else CYAN
        usable_w = width - (margin * 2)
        usable_h = height - (margin * 2)

        for player in players:
            x_norm = 1 - player["y"] if side == "left" else player["y"]
            y_norm = player["x"]
            x = margin + usable_w * x_norm
            y = margin + usable_h * y_norm
            radius = 18
            if player.get("sub"):
                canvas.create_oval(x - radius - 4, y - radius - 4, x + radius + 4, y + radius + 4, outline=accent, width=2)
            canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=circle_fill, outline="")
            canvas.create_text(x, y, text=str(player["number"]), fill=text_fill, font=FONT_BOLD)
            canvas.create_text(x, y + 28, text=player["name"], fill=TEXT, font=FONT_SMALL)

    def lineup_notes(self, match, minute):
        notes = [
            f"Replay minute {minute:02d}' drives the shape shown on the pitch.",
            f"{match['home']} is shown on the left and {match['away']} on the right.",
            "Substitutions are highlighted with an outer ring so formation changes are easy to spot.",
            "This pitch is meant to work with the replay slider, not as a separate frozen view.",
        ]
        if minute >= 58:
            notes.append(f"{match['home']} has already made an attacking adjustment by this point.")
        if minute >= 63:
            notes.append(f"{match['away']} has already reshaped the front line by this point.")
        return notes

    def match_events(self, match):
        if match["status"] == "LIVE":
            return [
                ("09'", match["home"], "SHOT", "Early low shot forced a near-post save"),
                ("24'", match["home"], "CARD", "Tactical foul stopped a transition"),
                ("33'", match["away"], "SAVE", "Keeper denied a close-range finish"),
                ("41'", match["away"], "GOAL", f"{match['away']} took the lead after a quick break"),
                ("HT", "Match", "SCORE", f"{match['home_score']} - {match['away_score']} at the break"),
                ("58'", match["home"], "SUB", "Fresh winger introduced to raise tempo"),
                ("63'", match["away"], "VAR", "Penalty shout checked and waved away"),
                (f"{match['minute']}'", match["home"], "PRESS", "Home side pushing higher and winning second balls"),
            ]
        if match["minute"] == 0:
            return [
                ("00'", "Match", "INFO", "Pre-match view: replay will fill once live or historical event data is loaded"),
            ]
        return [
            ("12'", match["home"], "SHOT", "Early chance saved low to the keeper's left"),
            ("27'", match["away"], "GOAL", "Back-post finish after a diagonal switch"),
            ("49'", match["home"], "SUB", "Midfield change to control the center"),
            ("68'", match["away"], "CARD", "Late challenge in transition"),
            ("74'", match["home"], "PRESS", "Sustained spell pinned the away side deep"),
            ("FT", "Match", "SCORE", f"{match['home_score']} - {match['away_score']} full-time"),
        ]

    def timeline_events(self, match, max_minute):
        events = []
        for minute_text, team, event, detail in self.match_events(match):
            minute = self.event_minute_value(minute_text, max_minute)
            if minute is None:
                continue
            events.append(
                {
                    "minute": minute,
                    "minute_text": minute_text,
                    "team": team or "Match",
                    "event": event,
                    "detail": detail,
                }
            )
        return events

    def event_minute_value(self, minute_text, max_minute):
        text = str(minute_text).strip().upper().replace("'", "")
        if text == "HT":
            return min(45, max_minute)
        if text == "FT":
            return max_minute
        digits = "".join(ch for ch in text if ch.isdigit())
        if not digits:
            return None
        return min(int(digits), max_minute)

    def match_stats(self, match):
        home_edge = max(match["edge"], 0)
        return [
            ("Expected goals (xG)", round(0.8 + home_edge / 10, 2), round(0.7 + abs(min(match["edge"], 0)) / 10, 2)),
            ("Shots on target", 5 if match["home_score"] else 2, 3 if match["away_score"] else 2),
            ("Shots off target", 6, 4),
            ("Blocked shots", 4, 2),
            ("Possession (%)", 54 if match["edge"] >= 0 else 47, 46 if match["edge"] >= 0 else 53),
            ("Corner kicks", 6, 3),
            ("Offsides", 1, 2),
            ("Fouls", 10, 8),
            ("Throw ins", 19, 21),
            ("Yellow cards", 1, 1),
            ("Crosses", 14, 10),
            ("Goalkeeper saves", 2, 4),
        ]

    def stats_max_minute(self, match):
        return max(match["minute"], 1) if match["status"] == "LIVE" else 90

    def stats_reference_minute(self, match):
        if match["status"] == "LIVE":
            return max(match["minute"], 1)
        if match["status"] == "UP":
            return 0
        return 90

    def current_replay_minute(self, match):
        max_minute = self.stats_max_minute(match)
        if self.replay_minute is None:
            return self.stats_reference_minute(match)
        return max(0, min(int(self.replay_minute), max_minute))

    def stat_map(self, match, minute=None, max_minute=None):
        if max_minute is None:
            max_minute = self.stats_max_minute(match)
        if minute is None:
            minute = self.current_replay_minute(match)
        return {label: (home, away) for label, home, away in self.match_stats_at_minute(match, minute, max_minute)}

    def match_stats_at_minute(self, match, minute, max_minute=90):
        ratio = 0 if max_minute <= 0 else max(0.0, min(minute / max_minute, 1.0))
        live_bias = ((match["id"] % 5) - 2) / 14
        rows = []

        for label, final_home, final_away in self.match_stats(match):
            if label == "Possession (%)":
                swing = live_bias * (0.6 - ratio) * 18
                home_share = max(32, min(68, final_home + swing))
                away_share = 100 - home_share
                rows.append((label, int(round(home_share)), int(round(away_share))))
                continue

            home_progress = max(0.0, ratio + live_bias * 0.18)
            away_progress = max(0.0, ratio - live_bias * 0.18)

            if label == "Expected goals (xG)":
                home_value = round(final_home * self.timeline_curve(home_progress), 2)
                away_value = round(final_away * self.timeline_curve(away_progress), 2)
            else:
                home_value = int(round(final_home * self.timeline_curve(home_progress)))
                away_value = int(round(final_away * self.timeline_curve(away_progress)))

            rows.append((label, home_value, away_value))

        if match["status"] == "UP" and minute == 0:
            adjusted_rows = []
            for label, home_value, away_value in rows:
                if label == "Possession (%)":
                    adjusted_rows.append((label, 50, 50))
                elif label == "Expected goals (xG)":
                    adjusted_rows.append((label, 0.0, 0.0))
                else:
                    adjusted_rows.append((label, 0, 0))
            return adjusted_rows

        return rows

    def stats_summary_percentages(self, match, minute, max_minute=90):
        current_stats = {label: (home, away) for label, home, away in self.match_stats_at_minute(match, minute, max_minute)}
        xg_home, xg_away = current_stats.get("Expected goals (xG)", (0.0, 0.0))
        shots_home, shots_away = current_stats.get("Shots on target", (0, 0))
        possession_home, possession_away = current_stats.get("Possession (%)", (50, 50))
        pressure_home, pressure_away = current_stats.get("Corner kicks", (0, 0))

        def split(left, right):
            total = left + right
            if total <= 0:
                return 50, 50
            left_pct = int(round((left / total) * 100))
            return left_pct, max(0, 100 - left_pct)

        return [
            ("xG Share", *split(xg_home, xg_away)),
            ("Shot Quality", *split(shots_home, shots_away)),
            ("Possession", int(possession_home), int(possession_away)),
            ("Pressure", *split(pressure_home, pressure_away)),
        ]

    def timeline_curve(self, ratio):
        ratio = max(0.0, min(ratio, 1.0))
        if ratio <= 0:
            return 0.0
        if ratio >= 1:
            return 1.0
        return min(1.0, max(0.0, (ratio ** 0.84) * (0.92 + ratio * 0.08)))

    def attack_stats(self, match, minute, max_minute):
        stats = self.stat_map(match, minute, max_minute)
        xg_home, xg_away = stats.get("Expected goals (xG)", (0.0, 0.0))
        on_target_home, on_target_away = stats.get("Shots on target", (0, 0))
        off_target_home, off_target_away = stats.get("Shots off target", (0, 0))
        blocked_home, blocked_away = stats.get("Blocked shots", (0, 0))
        crosses_home, crosses_away = stats.get("Crosses", (0, 0))
        corners_home, corners_away = stats.get("Corner kicks", (0, 0))

        home_big = max(0, int(round(on_target_home * 0.6 + xg_home * 1.5)))
        away_big = max(0, int(round(on_target_away * 0.6 + xg_away * 1.5)))
        home_box = on_target_home + off_target_home + int(round(crosses_home * 0.4))
        away_box = on_target_away + off_target_away + int(round(crosses_away * 0.4))
        home_accuracy = int(round((on_target_home / max(on_target_home + off_target_home + blocked_home, 1)) * 100))
        away_accuracy = int(round((on_target_away / max(on_target_away + off_target_away + blocked_away, 1)) * 100))

        return [
            ("Expected goals (xG)", xg_home, xg_away),
            ("Shots on target", on_target_home, on_target_away),
            ("Shots off target", off_target_home, off_target_away),
            ("Blocked shots", blocked_home, blocked_away),
            ("Big chances", home_big, away_big),
            ("Touches in box", home_box, away_box),
            ("Crosses", crosses_home, crosses_away),
            ("Shot accuracy (%)", home_accuracy, away_accuracy),
            ("Set-piece threat", corners_home, corners_away),
        ]

    def attack_summary_percentages(self, match, minute, max_minute):
        rows = {label: (home, away) for label, home, away in self.attack_stats(match, minute, max_minute)}
        xg_home, xg_away = rows["Expected goals (xG)"]
        shots_home, shots_away = rows["Shots on target"]
        box_home, box_away = rows["Touches in box"]
        accuracy_home, accuracy_away = rows["Shot accuracy (%)"]
        return [
            ("xG Threat", *self.percentage_split(xg_home, xg_away)),
            ("On Target", *self.percentage_split(shots_home, shots_away)),
            ("Box Threat", *self.percentage_split(box_home, box_away)),
            ("Accuracy", accuracy_home, accuracy_away),
        ]

    def attack_players(self, match, team, minute, max_minute):
        ratio = 0 if max_minute <= 0 else max(0.0, min(minute / max_minute, 1.0))
        if team == match["home"]:
            names = ["Erling Haaland", "Phil Foden", "Kevin De Bruyne"]
            xg_base = [0.38, 0.18, 0.14]
            action_base = [4, 3, 5]
        else:
            names = ["Mohamed Salah", "Darwin Nunez", "Luis Diaz"]
            xg_base = [0.34, 0.22, 0.16]
            action_base = [4, 3, 4]

        rows = []
        for idx, name in enumerate(names):
            xg = round(xg_base[idx] * (0.45 + ratio * 0.75), 2)
            shots = max(1, int(round(action_base[idx] * (0.4 + ratio * 0.8))))
            key_passes = max(0, int(round((action_base[idx] - 1) * (0.3 + ratio * 0.7))))
            touches_box = max(1, int(round(shots + key_passes + ratio * 3 + idx)))
            rows.append(
                {
                    "name": name,
                    "team": team,
                    "summary": f"xG {xg}  |  shots {shots}  |  key passes {key_passes}",
                    "headline": f"{name} is one of the main attacking drivers for {team} at this point in the match.",
                    "metrics": [
                        ("xG", f"{xg:.2f}"),
                        ("Shots", str(shots)),
                        ("Key Passes", str(key_passes)),
                        ("Box Touches", str(touches_box)),
                    ],
                    "notes": [
                        f"Shot volume is building as the match moves toward {minute:02d}'.",
                        "Most value is coming from central combinations and second-ball attacks.",
                        "Useful for comparing player-level threat against the team totals above.",
                    ],
                }
            )
        return rows

    def control_stats(self, match, minute, max_minute):
        stats = self.stat_map(match, minute, max_minute)
        possession_home, possession_away = stats.get("Possession (%)", (50, 50))
        throw_home, throw_away = stats.get("Throw ins", (0, 0))
        corners_home, corners_away = stats.get("Corner kicks", (0, 0))
        crosses_home, crosses_away = stats.get("Crosses", (0, 0))

        ratio = 0 if max_minute <= 0 else max(0.0, min(minute / max_minute, 1.0))
        home_pass_accuracy = int(round(76 + possession_home * 0.18 + ratio * 4))
        away_pass_accuracy = int(round(76 + possession_away * 0.18 + ratio * 4))
        home_field_tilt = int(round(min(78, max(22, possession_home + corners_home * 2 + match["edge"] * 1.5))))
        away_field_tilt = 100 - home_field_tilt
        home_progressive = max(1, int(round(crosses_home * 0.8 + throw_home * 0.35 + ratio * 8)))
        away_progressive = max(1, int(round(crosses_away * 0.8 + throw_away * 0.35 + ratio * 8)))
        home_tempo = max(1, int(round((throw_home + corners_home + crosses_home) * 0.9)))
        away_tempo = max(1, int(round((throw_away + corners_away + crosses_away) * 0.9)))

        return [
            ("Possession (%)", possession_home, possession_away),
            ("Pass accuracy (%)", home_pass_accuracy, away_pass_accuracy),
            ("Field tilt (%)", home_field_tilt, away_field_tilt),
            ("Progressive entries", home_progressive, away_progressive),
            ("Corners won", corners_home, corners_away),
            ("Cross volume", crosses_home, crosses_away),
            ("Tempo actions", home_tempo, away_tempo),
            ("Restarts / throw-ins", throw_home, throw_away),
        ]

    def control_summary_percentages(self, match, minute, max_minute):
        rows = {label: (home, away) for label, home, away in self.control_stats(match, minute, max_minute)}
        possession_home, possession_away = rows["Possession (%)"]
        pass_home, pass_away = rows["Pass accuracy (%)"]
        tilt_home, tilt_away = rows["Field tilt (%)"]
        prog_home, prog_away = rows["Progressive entries"]
        return [
            ("Possession", possession_home, possession_away),
            ("Pass Clean", pass_home, pass_away),
            ("Field Tilt", tilt_home, tilt_away),
            ("Progression", *self.percentage_split(prog_home, prog_away)),
        ]

    def defense_stats(self, match, minute, max_minute):
        stats = self.stat_map(match, minute, max_minute)
        fouls_home, fouls_away = stats.get("Fouls", (0, 0))
        yellows_home, yellows_away = stats.get("Yellow cards", (0, 0))
        saves_home, saves_away = stats.get("Goalkeeper saves", (0, 0))
        offsides_home, offsides_away = stats.get("Offsides", (0, 0))
        blocked_home, blocked_away = stats.get("Blocked shots", (0, 0))
        ratio = 0 if max_minute <= 0 else max(0.0, min(minute / max_minute, 1.0))

        home_duels = max(1, int(round(9 + ratio * 11 + max(match["edge"], 0))))
        away_duels = max(1, int(round(9 + ratio * 11 + abs(min(match["edge"], 0)))))
        home_interceptions = max(1, int(round(blocked_home * 1.6 + offsides_home + ratio * 5)))
        away_interceptions = max(1, int(round(blocked_away * 1.6 + offsides_away + ratio * 5)))
        home_clearances = max(1, int(round(saves_home * 2.2 + fouls_home * 0.5 + ratio * 4)))
        away_clearances = max(1, int(round(saves_away * 2.2 + fouls_away * 0.5 + ratio * 4)))

        return [
            ("Goalkeeper saves", saves_home, saves_away),
            ("Blocked shots", blocked_home, blocked_away),
            ("Interceptions", home_interceptions, away_interceptions),
            ("Clearances", home_clearances, away_clearances),
            ("Duels won", home_duels, away_duels),
            ("Offsides forced", offsides_home, offsides_away),
            ("Fouls committed", fouls_home, fouls_away),
            ("Yellow cards", yellows_home, yellows_away),
        ]

    def defense_summary_percentages(self, match, minute, max_minute):
        rows = {label: (home, away) for label, home, away in self.defense_stats(match, minute, max_minute)}
        saves_home, saves_away = rows["Goalkeeper saves"]
        duels_home, duels_away = rows["Duels won"]
        intercept_home, intercept_away = rows["Interceptions"]
        discipline_home, discipline_away = rows["Yellow cards"]
        discipline_left, discipline_right = self.percentage_split(max(1, 5 - discipline_home), max(1, 5 - discipline_away))
        return [
            ("Duel Share", *self.percentage_split(duels_home, duels_away)),
            ("Save Load", *self.percentage_split(saves_home, saves_away)),
            ("Interceptions", *self.percentage_split(intercept_home, intercept_away)),
            ("Discipline", discipline_left, discipline_right),
        ]

    def defense_players(self, match, team, minute, max_minute):
        ratio = 0 if max_minute <= 0 else max(0.0, min(minute / max_minute, 1.0))
        if team == match["home"]:
            names = ["Ruben Dias", "Rodri", "Ederson"]
            tackle_base = [3, 4, 1]
            duel_base = [6, 7, 1]
        else:
            names = ["Virgil van Dijk", "Alexis Mac Allister", "Alisson"]
            tackle_base = [3, 4, 1]
            duel_base = [7, 6, 1]

        rows = []
        for idx, name in enumerate(names):
            tackles = max(1, int(round(tackle_base[idx] * (0.35 + ratio * 0.85))))
            duels = max(1, int(round(duel_base[idx] * (0.4 + ratio * 0.8))))
            recoveries = max(1, int(round((duel_base[idx] + 2) * (0.4 + ratio * 0.9))))
            rows.append(
                {
                    "name": name,
                    "team": team,
                    "summary": f"tackles {tackles}  |  duels {duels}  |  recoveries {recoveries}",
                    "headline": f"{name} is carrying a big share of the defensive work for {team}.",
                    "metrics": [
                        ("Tackles", str(tackles)),
                        ("Duels", str(duels)),
                        ("Recoveries", str(recoveries)),
                        ("Def Actions", str(tackles + duels + recoveries)),
                    ],
                    "notes": [
                        "Good for spotting whether the defense is proactive or just absorbing pressure.",
                        "Higher recovery volume often lines up with field tilt and transition stress.",
                        f"This snapshot reflects the replay state at {minute:02d}'.",
                    ],
                }
            )
        return rows

    def percentage_split(self, left, right):
        total = left + right
        if total <= 0:
            return 50, 50
        left_pct = int(round((left / total) * 100))
        return left_pct, max(0, 100 - left_pct)

    def odds_rows(self, match):
        base_home, base_draw, base_away = match["odds"]
        books = [
            ("DraftKings", -0.02, 0.04, 0.03),
            ("FanDuel", 0.03, -0.03, 0.02),
            ("BetMGM", 0.01, 0.02, -0.04),
            ("Caesars", -0.04, 0.05, 0.01),
            ("bet365", 0.02, -0.01, 0.04),
            ("Pinnacle", 0.05, 0.03, -0.02),
            ("BetRivers", -0.01, -0.04, 0.05),
            ("Unibet", 0.04, 0.00, -0.01),
        ]
        rows = []
        for index, (book, h_adj, d_adj, a_adj) in enumerate(books):
            home = max(1.01, base_home + h_adj)
            draw = max(1.01, base_draw + d_adj)
            away = max(1.01, base_away + a_adj)
            edge = round(match["edge"] + ((index % 4) - 1.5) * 0.7, 1)
            rows.append((book, home, draw, away, edge))
        return rows

    def odds_detail_rows(self, match, book_name):
        book_row = next((row for row in self.odds_rows(match) if row[0] == book_name), self.odds_rows(match)[0])
        _, home, draw, away, edge = book_row
        return [
            ("1X2", f"{home:.2f}", f"{draw:.2f}", f"{away:.2f}", "main line"),
            ("Double Chance", "1X 1.22", "", f"X2 1.61", "safer"),
            ("Draw No Bet", f"{max(1.10, home - 0.45):.2f}", "", f"{max(1.10, away - 0.55):.2f}", "reduced risk"),
            ("Over/Under 2.5", "Over 1.91", "", "Under 1.95", "tight market"),
            ("Over/Under 3.5", "Over 2.74", "", "Under 1.48", "tempo sensitive"),
            ("BTTS", "Yes 1.68", "", "No 2.18", "live pace"),
            ("Asian Handicap", f"{match['home']} -0.25", "", f"{match['away']} +0.25", "model value"),
            ("Corners O/U 9.5", "Over 1.87", "", "Under 1.98", "edge small"),
            ("Cards O/U 4.5", "Over 1.73", "", "Under 2.08", "ref linked"),
            ("Next Goal", f"{match['home']} 2.40", "", f"{match['away']} 2.75", "live only"),
        ]

    def prediction_rows(self, match):
        home, draw, away = match["pred"]
        sources = [
            ("Opta", 3, -1, -2),
            ("Forebet", -2, 1, 1),
            ("PredictZ", 1, 2, -3),
            ("SportsMole", -1, -2, 3),
            ("WinDrawWin", 2, 0, -2),
            ("Betimate", -3, 3, 0),
            ("SoccerVista", 0, -1, 1),
            ("Our Model", round(match["edge"]), 0, -round(match["edge"])),
        ]
        rows = []
        for source, h_adj, d_adj, a_adj in sources:
            h = max(1, min(98, int(home + h_adj)))
            d = max(1, min(98, int(draw + d_adj)))
            a = max(1, min(98, int(away + a_adj)))
            total = h + d + a
            h = round(h * 100 / total)
            d = round(d * 100 / total)
            a = max(1, 100 - h - d)
            pick = match["home"] if h >= d and h >= a else match["away"] if a >= d else "Draw"
            rows.append((source, h, d, a, pick))
        return rows

    def prediction_detail_snapshot(self, match, source_name):
        row = next((item for item in self.prediction_rows(match) if item[0] == source_name), self.prediction_rows(match)[0])
        _, home, draw, away, pick = row
        return {
            "headline": f"{source_name} leans {pick} for {match['home']} vs {match['away']}",
            "confidence": max(home, draw, away),
            "model_family": "ensemble + news weighting" if source_name in ("Opta", "Our Model") else "stats-led forecast",
            "updated": "live" if match["status"] == "LIVE" else "pre-match",
            "markets": [
                ("1X2", f"{home}% / {draw}% / {away}%"),
                ("Over 2.5", f"{min(78, away + 12)}%"),
                ("Under 2.5", f"{max(22, 100 - away - 12)}%"),
                ("BTTS", f"{52 + (match['home_score'] + match['away_score']) * 6}%"),
                ("Most likely score", "1-1" if draw >= max(home, away) - 4 else "1-2" if pick == match["away"] else "2-1"),
                ("Fair line", f"{pick} {round(100 / max(home, away), 2)}"),
            ],
            "reasons": [
                f"{source_name} weights recent form and matchup profile heavily.",
                f"{match['away']} pressure and transition threat improve the away scenario." if pick == match["away"] else f"{match['home']} control profile improves the home scenario." if pick == match["home"] else "Balanced game state keeps draw scenarios alive.",
                f"Weather, referee, and market movement are included as secondary adjustments.",
            ],
            "flags": [
                "Consensus can lag behind very recent lineup changes.",
                "Source-specific scoreline markets are usually noisier than moneyline probabilities.",
                "Treat as support evidence, not a standalone trigger.",
            ],
        }

    def consensus_prediction(self, match):
        rows = self.prediction_rows(match)
        home_avg = round(sum(row[1] for row in rows) / len(rows))
        draw_avg = round(sum(row[2] for row in rows) / len(rows))
        away_avg = round(sum(row[3] for row in rows) / len(rows))
        pick = match["home"] if home_avg >= draw_avg and home_avg >= away_avg else match["away"] if away_avg >= draw_avg else "Draw"
        confidence = max(home_avg, draw_avg, away_avg)
        return {
            "home": home_avg,
            "draw": draw_avg,
            "away": away_avg,
            "pick": pick,
            "confidence": confidence,
        }

    def analysis_snapshot(self, match):
        consensus = self.consensus_prediction(match)
        odds = self.odds_rows(match)
        best_book = max(odds, key=lambda item: item[4])
        market_prob = round(100 / best_book[1]) if consensus["pick"] == match["home"] else round(100 / best_book[3]) if consensus["pick"] == match["away"] else round(100 / best_book[2])
        true_prob = consensus["confidence"]
        edge = round(true_prob - market_prob, 1)
        data_quality = self.data_quality_score(match)
        freshness = self.freshness_label(match)
        lineup_status = self.lineup_status(match)
        weather = self.weather_label(match)
        market_move = self.market_movement_label(match)
        missing = self.missing_inputs(match)

        decision = "PASS"
        decision_color = MUTED
        if data_quality >= 82 and edge >= 5 and lineup_status == "Confirmed":
            decision = "BET"
            decision_color = GREEN
        elif data_quality >= 70 and edge >= 2:
            decision = "LEAN"
            decision_color = ORANGE

        reasons_for = [
            f"Model consensus leans {consensus['pick']} with {consensus['confidence']}% confidence.",
            f"Best tracked market is {best_book[0]} and leaves {edge:+.1f} implied edge.",
            f"Form profile: {match['home']} {''.join(match['home_form'])} vs {match['away']} {''.join(match['away_form'])}.",
        ]
        if match["status"] == "LIVE":
            reasons_for.append(f"Live state {match['minute']}' at {match['home_score']}-{match['away_score']} keeps the signal active.")
        else:
            reasons_for.append("Pre-match window still allows lineup, news, and odds confirmation before entry.")

        reasons_against = [
            f"Market move is {market_move.lower()}, so late entries may lose value.",
            f"Weather and referee context can shift pace and foul profile ({weather.lower()}, {match['referee']}).",
            "Prediction-source disagreement still matters even when average consensus looks strong.",
        ]
        if missing != ["None"]:
            reasons_against.append(f"Weak inputs: {', '.join(missing)}.")

        risk_controls = [
            "Pass if edge drops below +2 before entry.",
            "Use small fixed stake or fractional Kelly only.",
            "No stacking correlated bets on the same match without re-checking line movement.",
            "Downgrade to pass if lineup/news changes within the final refresh window.",
        ]

        data_buckets = [
            ("Match state", f"{match['status']} {match['minute']}'  score {match['home_score']}-{match['away_score']}"),
            ("Team profile", f"Attack {match['home_avg']:.1f}/{match['away_avg']:.1f}  form {''.join(match['home_form'])}/{''.join(match['away_form'])}"),
            ("Availability", f"Lineups {lineup_status}  injuries {self.injury_status(match)}"),
            ("Market", f"{len(odds)} books  best {best_book[0]}  move {market_move}"),
            ("Context", f"{weather}  ref {match['referee']}  venue {match['venue']}"),
            ("News", f"{self.news_status(match)}  local pulse {self.local_news_note(match)}"),
        ]

        sources = [
            ("Lineups", "Squads", lineup_status, "High"),
            ("Local News", "Context", self.news_state(match), "Medium"),
            ("Weather", "External", "Fresh", "Medium"),
            ("Odds Feed", "Market", "Live", "High"),
            ("Prediction Feed", "Consensus", "Live", "Medium"),
            ("Referee/Rules", "Context", "Confirmed", "Low"),
        ]

        return {
            "decision": decision,
            "decision_color": decision_color,
            "market": f"{best_book[0]} best price  |  pick {consensus['pick']}",
            "confidence": consensus["confidence"],
            "edge": edge,
            "true_prob": true_prob,
            "market_prob": market_prob,
            "data_quality": data_quality,
            "freshness": freshness,
            "lineups": lineup_status,
            "lineup_color": GREEN if lineup_status == "Confirmed" else YELLOW if lineup_status == "Partial" else RED,
            "weather": weather,
            "news_status": self.news_status(match),
            "reasons_for": reasons_for,
            "reasons_against": reasons_against,
            "risk_controls": risk_controls,
            "data_buckets": data_buckets,
            "missing": missing,
            "sources": sources,
            "consensus_spread": self.consensus_spread(match),
            "books_tracked": len(odds),
            "prediction_sources": len(self.prediction_rows(match)),
            "market_move": market_move,
            "referee_note": self.referee_note(match),
        }

    def data_quality_score(self, match):
        score = 76
        if match["status"] == "LIVE":
            score += 6
        if abs(match["edge"]) >= 4:
            score += 4
        if match["minute"] == 0:
            score -= 3
        if match["home"] in ("Man City", "Real Madrid", "Inter Milan"):
            score += 3
        return max(55, min(score, 94))

    def freshness_label(self, match):
        if match["status"] == "LIVE":
            return "15s live"
        if match["minute"] == 0:
            return "5m pre"
        return "30m old"

    def lineup_status(self, match):
        if match["status"] == "LIVE":
            return "Confirmed"
        if match["minute"] == 0 and match["edge"] >= 4:
            return "Partial"
        return "Pending"

    def weather_label(self, match):
        mapping = {
            "England": "Light rain 11C",
            "Spain": "Clear 17C",
            "Italy": "Calm 15C",
            "Germany": "Windy 9C",
        }
        return mapping.get(match["country"], "Normal 14C")

    def injury_status(self, match):
        return "minor doubts" if abs(match["edge"]) < 3 else "mostly clear"

    def news_status(self, match):
        return "2 local reports checked" if match["status"] == "LIVE" else "Awaiting final pre-match pressers"

    def news_state(self, match):
        return "Confirmed" if match["status"] == "LIVE" else "Checking"

    def local_news_note(self, match):
        return "travel and rotation flagged" if match["away"] in ("Liverpool", "Barcelona", "Napoli") else "quiet local cycle"

    def market_movement_label(self, match):
        return "Sharp move to away" if match["edge"] < -2 else "Mild move to home" if match["edge"] > 4 else "Flat market"

    def missing_inputs(self, match):
        missing = []
        if match["status"] != "LIVE":
            missing.append("confirmed lineups")
        if abs(match["edge"]) < 2:
            missing.append("clear market discrepancy")
        if match["country"] == "Germany":
            missing.append("local reporter confirmation")
        return missing or ["None"]

    def consensus_spread(self, match):
        rows = self.prediction_rows(match)
        picks = [row[4] for row in rows]
        leader = max(set(picks), key=picks.count)
        return picks.count(leader)

    def referee_note(self, match):
        return "card-happy profile" if "Taylor" in match["referee"] or "Oliver" in match["referee"] else "balanced whistle"

    def table_rows(self, match):
        base = [
            ("Inter", 33, 49, 78, 25),
            ("Napoli", 33, 15, 66, 20),
            ("AC Milan", 33, 20, 64, 18),
            ("Juventus", 32, 26, 60, 17),
            ("Como 1907", 33, 29, 58, 16),
            ("AS Roma", 33, 17, 58, 18),
            ("Atalanta", 33, 16, 54, 14),
            ("Bologna", 32, 5, 48, 14),
            ("Lazio", 33, 4, 47, 12),
            ("Sassuolo", 33, -3, 45, 13),
            ("Udinese", 33, -5, 43, 12),
            ("Torino", 33, -17, 40, 11),
        ]
        teams = [row[0] for row in base]
        if match["home"] not in teams:
            base.insert(6, (match["home"], 33, 8, 51, 13))
        if match["away"] not in teams:
            base.insert(3, (match["away"], 33, 20, 64, 18))
        return [(idx, *row) for idx, row in enumerate(base[:14], start=1)]

    def h2h_rows(self, match):
        return [
            ("2025", match["away"], match["home"], 3, 0),
            ("2024/25", match["away"], match["home"], 1, 0),
            ("2024", match["home"], match["away"], 0, 1),
            ("2023/24", match["home"], match["away"], 1, 3),
            ("2023", match["away"], match["home"], 1, 0),
            ("2022/23", match["away"], match["home"], 3, 1),
        ]

    def form_badges(self, parent, form):
        row = tk.Frame(parent, bg=PANEL)
        row.pack(fill="x")
        for result in form:
            color = GREEN if result == "W" else RED if result == "L" else MUTED
            bg = "#14532d" if result == "W" else "#7f1d1d" if result == "L" else "#475569"
            tk.Label(row, text=result, bg=bg, fg=color, font=FONT_MONO, width=3, pady=2).pack(side="left", padx=2)

    def render_decision_engine(self):
        self.clear(self.recommendation_body)
        snapshot = self.analysis_snapshot(self.current_match)

        top = self.info_card(self.recommendation_body)
        top.pack(fill="x", padx=6, pady=(6, 4))
        tk.Label(top, text=snapshot["decision"], bg=PANEL_DARK, fg=snapshot["decision_color"], font=("Segoe UI", 16, "bold"), anchor="w").pack(fill="x", padx=10, pady=(8, 2))
        tk.Label(top, text=snapshot["market"], bg=PANEL_DARK, fg=TEXT, font=FONT_BOLD, anchor="w").pack(fill="x", padx=10)
        tk.Label(top, text=f"Confidence {snapshot['confidence']}%  |  Edge {snapshot['edge']:+.1f}  |  Data quality {snapshot['data_quality']}%", bg=PANEL_DARK, fg=MUTED, font=FONT_SMALL, anchor="w").pack(fill="x", padx=10, pady=(0, 8))

        bands = tk.Frame(top, bg=PANEL_DARK)
        bands.pack(fill="x", padx=10, pady=(0, 10))
        for label, value, color in [
            ("True Prob", f"{snapshot['true_prob']}%", CYAN),
            ("Market Implied", f"{snapshot['market_prob']}%", ORANGE),
            ("Discrepancy", f"{snapshot['edge']:+.1f}", snapshot["decision_color"]),
        ]:
            box = tk.Frame(bands, bg="#243244")
            box.pack(side="left", expand=True, fill="x", padx=3)
            tk.Label(box, text=label, bg="#243244", fg=MUTED, font=FONT_SMALL).pack(pady=(6, 2))
            tk.Label(box, text=value, bg="#243244", fg=color, font=FONT_BOLD).pack(pady=(0, 6))

        self.section_title(self.recommendation_body, "WHY IT LIKES IT")
        likes = self.info_card(self.recommendation_body)
        likes.pack(fill="x", padx=6, pady=(0, 4))
        for reason in snapshot["reasons_for"]:
            tk.Label(likes, text=f"+ {reason}", bg=PANEL_DARK, fg=GREEN, font=FONT_SMALL, anchor="w", justify="left").pack(fill="x", padx=10, pady=2)

        self.section_title(self.recommendation_body, "WHY IT CAN FAIL")
        cautions = self.info_card(self.recommendation_body)
        cautions.pack(fill="x", padx=6, pady=(0, 4))
        for reason in snapshot["reasons_against"]:
            tk.Label(cautions, text=f"- {reason}", bg=PANEL_DARK, fg=RED, font=FONT_SMALL, anchor="w", justify="left").pack(fill="x", padx=10, pady=2)

        self.section_title(self.recommendation_body, "RISK CONTROLS")
        risk = self.info_card(self.recommendation_body)
        risk.pack(fill="x", padx=6, pady=(0, 4))
        for rule in snapshot["risk_controls"]:
            tk.Label(risk, text=f"* {rule}", bg=PANEL_DARK, fg=MUTED, font=FONT_SMALL, anchor="w", justify="left").pack(fill="x", padx=10, pady=2)

    def render_data_quality(self):
        self.clear(self.quality_body)
        snapshot = self.analysis_snapshot(self.current_match)

        row = tk.Frame(self.quality_body, bg=PANEL)
        row.pack(fill="x", padx=6, pady=(6, 6))
        for label, value, color in [
            ("Freshness", snapshot["freshness"], CYAN),
            ("Lineups", snapshot["lineups"], snapshot["lineup_color"]),
            ("Weather", snapshot["weather"], ORANGE),
            ("News", snapshot["news_status"], TEXT),
        ]:
            cell = tk.Frame(row, bg="#243244")
            cell.pack(side="left", expand=True, fill="x", padx=2)
            tk.Label(cell, text=label, bg="#243244", fg=MUTED, font=FONT_SMALL).pack(pady=(5, 2))
            tk.Label(cell, text=value, bg="#243244", fg=color, font=FONT_BOLD).pack(pady=(0, 6))

        self.section_title(self.quality_body, "DATA BUCKETS")
        buckets = self.info_card(self.quality_body)
        buckets.pack(fill="x", padx=6, pady=(0, 4))
        for label, value in snapshot["data_buckets"]:
            line = tk.Frame(buckets, bg=PANEL_DARK)
            line.pack(fill="x", padx=10, pady=2)
            tk.Label(line, text=label, bg=PANEL_DARK, fg=CYAN, font=FONT_SMALL, width=14, anchor="w").pack(side="left")
            tk.Label(line, text=value, bg=PANEL_DARK, fg=TEXT, font=FONT_SMALL, anchor="w").pack(side="left")

        self.section_title(self.quality_body, "MISSING / WEAK INPUTS")
        missing = self.info_card(self.quality_body)
        missing.pack(fill="x", padx=6, pady=(0, 4))
        for item in snapshot["missing"]:
            tk.Label(missing, text=f"- {item}", bg=PANEL_DARK, fg=RED if item != "None" else GREEN, font=FONT_SMALL, anchor="w").pack(fill="x", padx=10, pady=2)

    def render_source_monitor(self):
        self.clear(self.source_body)
        snapshot = self.analysis_snapshot(self.current_match)

        header = tk.Frame(self.source_body, bg=PANEL_DARK)
        header.pack(fill="x", padx=6, pady=(6, 2))
        for text, width in [("SOURCE", 14), ("TYPE", 10), ("STATE", 12), ("WEIGHT", 8)]:
            tk.Label(header, text=text, bg=PANEL_DARK, fg=ORANGE, font=FONT_MONO_SMALL, width=width, anchor="w").pack(side="left")

        for source, kind, state, weight in snapshot["sources"]:
            row = tk.Frame(self.source_body, bg=ROW)
            row.pack(fill="x", padx=6, pady=1)
            state_color = GREEN if state in ("Confirmed", "Live", "Fresh") else YELLOW if state in ("Partial", "Checking") else RED
            for value, width, color in [
                (source, 14, TEXT),
                (kind, 10, MUTED),
                (state, 12, state_color),
                (weight, 8, CYAN),
            ]:
                tk.Label(row, text=value, bg=ROW, fg=color, font=FONT_MONO_SMALL, width=width, anchor="w").pack(side="left", pady=4)

        footer = self.info_card(self.source_body)
        footer.pack(fill="x", padx=6, pady=(4, 4))
        tk.Label(footer, text=f"Consensus spread: {snapshot['consensus_spread']} pts  |  Books tracked: {snapshot['books_tracked']}  |  Prediction sources: {snapshot['prediction_sources']}", bg=PANEL_DARK, fg=MUTED, font=FONT_SMALL, anchor="w").pack(fill="x", padx=10, pady=(6, 4))
        tk.Label(footer, text=f"Market move: {snapshot['market_move']}  |  Referee note: {snapshot['referee_note']}", bg=PANEL_DARK, fg=TEXT, font=FONT_SMALL, anchor="w").pack(fill="x", padx=10, pady=(0, 6))

    def render_watchlist(self):
        self.clear(self.watchlist_frame)
        items = [m for m in MATCHES if m["id"] in self.watchlist_ids]
        if not items:
            tk.Label(
                self.watchlist_frame,
                text="No matches in watchlist. Click the star to add.",
                bg=PANEL_DARK,
                fg=MUTED,
                font=FONT_MONO_SMALL,
                anchor="center",
                pady=8,
            ).pack(fill="x", padx=4)
            return

        for match in items:
            self.compact_match_row(self.watchlist_frame, match, selected=False)
        self.watchlist_canvas.configure(scrollregion=self.watchlist_canvas.bbox("all"))

    def render_sidebar_watchlist(self):
        self.clear(self.sidebar_watch_body)
        items = [m for m in MATCHES if m["id"] in self.watchlist_ids]
        message = "No matches in watchlist." if not items else "\n".join(f"{m['home']} vs {m['away']}" for m in items[:4])
        tk.Label(self.sidebar_watch_body, text=message, bg=PANEL_DARK, fg=MUTED, font=FONT_MONO_SMALL, anchor="w", justify="left", padx=10, pady=10).pack(fill="both", expand=True)

    def render_history(self):
        self.clear(self.source_body)
        header = tk.Frame(self.source_body, bg=PANEL_DARK)
        header.pack(fill="x", padx=6, pady=(6, 2))
        cols = [("IDX", 4), ("TIME", 8), ("MATCH", 22), ("REC", 10), ("EDGE", 7), ("SETTLED", 8)]
        for name, width in cols:
            tk.Label(header, text=name, bg=PANEL_DARK, fg=ORANGE, font=FONT_MONO_SMALL, width=width, anchor="w").pack(side="left")

        for item in HISTORY_SAMPLE:
            idx, time, match, rec, edge, settled = item
            row = tk.Frame(self.source_body, bg=PANEL)
            row.pack(fill="x", padx=6)
            values = [idx, time, match[:22], rec[:10], f"{edge:+.1f}", settled]
            widths = [4, 8, 22, 10, 7, 8]
            for value, width in zip(values, widths):
                color = GREEN if value.startswith("+") or value == "YES" else RED if value == "NO" else MUTED
                tk.Label(row, text=value, bg=PANEL, fg=color, font=FONT_MONO_SMALL, width=width, anchor="w").pack(side="left")

    def render_accuracy(self):
        self.clear(self.accuracy_body)
        try:
            summary = summarize_accuracy()
            settled = summary.get("total_settled", 0)
            rec_hit = summary.get("recommended_hit_rate", 0.0)
            draw_hit = summary.get("draw_hit_rate", 0.0)
            under_hit = summary.get("under_hit_rate", 0.0)
        except Exception:
            settled = 12
            rec_hit = 75.0
            draw_hit = 60.0
            under_hit = 80.0

        tk.Label(self.accuracy_body, text="ACCURACY SUMMARY", bg=PANEL, fg=ORANGE, font=FONT_MONO_SMALL, anchor="w").pack(fill="x", padx=8, pady=(8, 3))
        for label, value in [
            ("Settled analyses", settled),
            ("Recommended hit %", rec_hit),
            ("Draw outcome %", draw_hit),
            ("Under 2.5 hit %", under_hit),
        ]:
            row = tk.Frame(self.accuracy_body, bg=PANEL)
            row.pack(fill="x", padx=8, pady=1)
            tk.Label(row, text=f"{label}:", bg=PANEL, fg=MUTED, font=FONT_MONO_SMALL, width=24, anchor="w").pack(side="left")
            tk.Label(row, text=str(value), bg=PANEL, fg=GREEN, font=FONT_MONO_SMALL, anchor="e").pack(side="right")

        community = self.platform_vs_community_summary()
        tk.Label(self.accuracy_body, text="PLATFORM VS COMMUNITY", bg=PANEL, fg=CYAN, font=FONT_MONO_SMALL, anchor="w").pack(fill="x", padx=8, pady=(10, 3))
        for label, value, color in [
            ("Platform hit %", community["platform_hit"], ORANGE),
            ("Community hit %", community["community_hit"], CYAN),
            ("Settled challenge picks", community["settled"], GREEN),
            ("Open challenge picks", community["open"], MUTED),
        ]:
            row = tk.Frame(self.accuracy_body, bg=PANEL)
            row.pack(fill="x", padx=8, pady=1)
            tk.Label(row, text=f"{label}:", bg=PANEL, fg=MUTED, font=FONT_MONO_SMALL, width=24, anchor="w").pack(side="left")
            tk.Label(row, text=str(value), bg=PANEL, fg=color, font=FONT_MONO_SMALL, anchor="e").pack(side="right")

    def toggle_watchlist(self, match):
        if match["id"] in self.watchlist_ids:
            self.watchlist_ids.remove(match["id"])
        else:
            self.watchlist_ids.add(match["id"])
        self.render_matches()
        self.render_watchlist()
        self.render_sidebar_watchlist()

    def add_current_to_watchlist(self):
        match = self.current_match
        self.watchlist_ids.add(match["id"])
        try:
            add_match(self.state_from_match(match), self.market_from_match(match))
        except Exception:
            pass
        self.tracker_status.config(text=f"{match['home']} vs {match['away']} added to watchlist.", fg=GREEN)
        self.render_matches()
        self.render_watchlist()
        self.render_sidebar_watchlist()

    def remove_current_from_watchlist(self):
        match = self.current_match
        self.watchlist_ids.discard(match["id"])
        self.tracker_status.config(text=f"{match['home']} vs {match['away']} removed from watchlist.", fg=MUTED)
        self.render_matches()
        self.render_watchlist()
        self.render_sidebar_watchlist()

    def state_from_match(self, match):
        return MatchState(
            home_team=match["home"],
            away_team=match["away"],
            minute=int(match["minute"]),
            home_goals=int(match["home_score"]),
            away_goals=int(match["away_score"]),
            stoppage_minutes_remaining=0,
            home_red_cards=0,
            away_red_cards=0,
            pressure_bias=1 if match["edge"] > 0 else 0,
        )

    def market_from_match(self, match):
        return MarketInput(
            total_line=2.5,
            draw_cents=match["draw_price"],
            under_cents=match["under_price"],
            over_cents=match["over_price"],
        )

    def run_analysis(self):
        match = self.current_match
        state = self.state_from_match(match)
        market = self.market_from_match(match)
        results = self.engine.full_analysis(state, market)

        edges = [
            ("DRAW", self.engine.fair_cents(results["draw_prob"]) - market.draw_cents),
            ("UNDER 2.5", self.engine.fair_cents(results["under_prob"]) - market.under_cents),
            ("OVER 2.5", self.engine.fair_cents(results["over_prob"]) - market.over_cents),
        ]
        best_label, best_edge = max(edges, key=lambda item: item[1])
        confidence = max(0.0, min(99.0, 50.0 + best_edge))

        lines = [
            f"{match['home']} vs {match['away']}",
            f"Recommendation: {best_label}",
            f"Best edge: {best_edge:+.1f}c",
            f"Confidence: {confidence:.1f}%",
            "",
            f"Draw model: {results['draw_prob'] * 100:.1f}%",
            f"Under 2.5 model: {results['under_prob'] * 100:.1f}%",
            f"Over 2.5 model: {results['over_prob'] * 100:.1f}%",
            "",
            "Inputs:",
            f"Minute {state.minute}, score {state.home_goals}-{state.away_goals}",
            f"Market D/U/O: {market.draw_cents:.0f}/{market.under_cents:.0f}/{market.over_cents:.0f}",
        ]

        try:
            log_analysis({
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
                "confidence": round(confidence, 1),
                "best_edge": round(best_edge, 1),
            })
        except Exception:
            pass

        HISTORY_SAMPLE.insert(0, (str(len(HISTORY_SAMPLE) + 1), "LIVE", f"{match['home']} vs {match['away']}", best_label, best_edge, "NO"))
        del HISTORY_SAMPLE[5:]
        self.render_decision_engine()
        self.render_data_quality()
        self.render_source_monitor()
        self.render_accuracy()
        self.tracker_status.config(text="Analysis complete.", fg=GREEN)

    def start_tracker(self):
        if self.tracker_running:
            self.tracker_status.config(text="Tracker already running.", fg=MUTED)
            return
        self.tracker_running = True
        self.tracker_status.config(text="Live tracker started.", fg=GREEN)
        self.tracker_tick()

    def tracker_tick(self):
        if not self.tracker_running:
            return
        if self.current_match["status"] == "LIVE" and self.current_match["minute"] < 90:
            self.current_match["minute"] += 1
            if self.current_match["minute"] >= 90:
                self.current_match["minute"] = 90
                self.current_match["status"] = "FT"
                self.tracker_running = False
                self.settle_match_challenges(self.current_match)
                self.tracker_status.config(text="Match finished. Challenge picks settled.", fg=GREEN)
            self.select_match(self.current_match)
        if self.tracker_running:
            self.tracker_job = self.root.after(5000, self.tracker_tick)
        else:
            self.tracker_job = None

    def stop_tracker(self):
        self.tracker_running = False
        if self.tracker_job is not None:
            self.root.after_cancel(self.tracker_job)
            self.tracker_job = None
        self.tracker_status.config(text="Live tracker stopped.", fg=MUTED)

    def switch_live_api(self):
        self.status_label.config(text="Live API switch requested. Local mock data still active.")

    def test_speed(self):
        self.status_label.config(text=f"Last Load: instant  |  Matches: {len(self.filtered_matches())}")

    def on_mousewheel(self, event):
        widget = self.root.focus_get()
        if widget is not None and str(widget).startswith(str(self.matches_canvas)):
            self.matches_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def clear(self, parent):
        for child in parent.winfo_children():
            child.destroy()

    def mainloop(self):
        self.root.mainloop()


if __name__ == "__main__":
    SoccerEdgeApp().mainloop()
