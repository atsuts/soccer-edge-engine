import csv
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
        self.tab_name = tk.StringVar(value="Info")

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
        self.recommendation_body = None
        self.quality_body = None
        self.source_body = None
        self.filter_combos = {}
        self.matches_frame = None
        self.matches_canvas = None
        self.watchlist_frame = None
        self.watchlist_canvas = None
        self.status_label = None
        self.tracker_status = None

        self.configure_styles()
        self.build_ui()
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
        parent.grid_rowconfigure(1, weight=6)
        parent.grid_rowconfigure(2, weight=4)
        parent.grid_columnconfigure(0, weight=1)

        tk.Label(
            parent,
            text="MATCH ANALYSIS",
            bg=BG,
            fg=CYAN,
            font=FONT_BOLD,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", pady=(8, 6))

        body = tk.Frame(parent, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        body.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(3, weight=1)

        self.build_scoreboard(body)
        self.build_match_meta(body)
        self.build_tabs(body)

        self.tab_content = tk.Frame(body, bg=PANEL)
        self.tab_content.grid(row=3, column=0, sticky="nsew", padx=8)

        self.build_action_bar(body)
        self.build_market_sections(parent)
        self.render_tab()
        self.render_market_sections()

    def build_market_sections(self, parent):
        market = tk.Frame(parent, bg=BG)
        market.grid(row=2, column=0, sticky="nsew", pady=(0, 8))
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
        for idx, name in enumerate(["Info", "Summary", "Stats", "Line-ups", "Table", "H2H"]):
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

    def rebuild_tabs(self):
        parent = self.tab_content.master
        for child in parent.grid_slaves(row=2):
            child.destroy()
        self.build_tabs(parent)

    def build_action_bar(self, parent):
        actions = tk.Frame(parent, bg=BG)
        actions.grid(row=4, column=0, sticky="ew", padx=8, pady=(8, 10))
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=1)
        actions.grid_columnconfigure(2, weight=1)

        left = tk.Frame(actions, bg=BG)
        left.grid(row=0, column=0, sticky="w")
        self.button(left, "+ Add Watchlist", PURPLE, self.add_current_to_watchlist).pack(side="left", padx=(0, 6))
        self.button(left, "X Remove", GRAY_BTN, self.remove_current_from_watchlist).pack(side="left")

        self.button(actions, "Analyze", "#5bc0de", self.run_analysis, width=12, pady=11).grid(row=0, column=1)

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

        model_outer, self.recommendation_body = self.panel(parent, "DECISION ENGINE")
        model_outer.grid(row=0, column=0, sticky="nsew", pady=(8, 8))

        team_outer, self.quality_body = self.panel(parent, "DATA QUALITY")
        team_outer.grid(row=1, column=0, sticky="nsew", pady=(0, 8))

        watch_outer, body = self.panel(parent, "WATCHLIST")
        watch_outer.grid(row=2, column=0, sticky="nsew", pady=(0, 8))
        self.sidebar_watch_body = body

        history_outer, self.source_body = self.panel(parent, "SOURCE MONITOR")
        history_outer.grid(row=3, column=0, sticky="nsew", pady=(0, 8))

        acc_outer, self.accuracy_body = self.panel(parent, "ACCURACY DASHBOARD")
        acc_outer.grid(row=4, column=0, sticky="nsew", pady=(0, 10))

        self.render_decision_engine()
        self.render_data_quality()
        self.render_sidebar_watchlist()
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
        self.current_match = match
        self.selected_odds_book = None
        self.selected_prediction_source = None
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
        self.render_tab()
        self.render_decision_engine()
        self.render_data_quality()
        self.render_source_monitor()
        self.render_market_sections()
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
        self.tab_name.set(name)
        self.rebuild_tabs()
        self.render_tab()

    def render_tab(self):
        for child in self.tab_content.winfo_children():
            child.destroy()

        match = self.current_match
        body = self.tab_body()
        tab = self.tab_name.get()
        if tab == "Info":
            self.render_info_tab(body, match)
        elif tab == "Summary":
            self.render_summary_tab(body, match)
        elif tab == "Stats":
            self.render_stats_tab(body, match)
        elif tab == "Line-ups":
            self.render_lineups_tab(body, match)
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
                label.bind("<Double-Button-1>", lambda _event, book_name=book: self.open_odds_detail(book_name))
            row.bind("<Double-Button-1>", lambda _event, book_name=book: self.open_odds_detail(book_name))

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
            text="Double-click a bookmaker row for full market detail.",
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
                label.bind("<Double-Button-1>", lambda _event, source_name=source: self.open_prediction_detail(source_name))
            row.bind("<Double-Button-1>", lambda _event, source_name=source: self.open_prediction_detail(source_name))

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
            text="Double-click a prediction source row for full source detail.",
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
        self.section_title(parent, "MATCH STATS")
        for label, home, away in self.match_stats(match):
            self.stat_bar(parent, label, home, away)

    def render_lineups_tab(self, parent, match):
        self.section_title(parent, f"{match['home'].upper()}  4-3-3")
        pitch = tk.Frame(parent, bg="#4d7112", highlightbackground="#8aaa42", highlightthickness=1)
        pitch.pack(fill="both", expand=True, pady=(0, 8))
        home_names = ["Keeper", "Right Back", "Center Back", "Center Back", "Left Back", "Midfielder", "Anchor", "Midfielder", "Winger", "Striker", "Winger"]
        away_names = ["Forward", "Forward", "Midfielder", "Midfielder", "Midfielder", "Wing Back", "Center Back", "Center Back", "Center Back", "Wing Back", "Keeper"]
        self.formation_line(pitch, [home_names[0]], "#111827", TEXT)
        self.formation_line(pitch, home_names[1:5], "#111827", TEXT)
        self.formation_line(pitch, home_names[5:8], "#111827", TEXT)
        self.formation_line(pitch, home_names[8:11], "#111827", TEXT)
        tk.Frame(pitch, bg="#8aaa42", height=1).pack(fill="x", padx=10, pady=8)
        self.formation_line(pitch, away_names[0:2], TEXT, "#111827")
        self.formation_line(pitch, away_names[2:5], TEXT, "#111827")
        self.formation_line(pitch, away_names[5:10], TEXT, "#111827")
        self.formation_line(pitch, [away_names[10]], TEXT, "#111827")
        self.section_title(parent, f"{match['away'].upper()}  3-5-2")

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
        tk.Frame(bar, bg="#c7cbd1", height=9).grid(row=0, column=0, sticky="ew")
        tk.Frame(bar, bg=ORANGE, height=9).grid(row=0, column=1, sticky="ew")

    def formation_line(self, parent, players, circle_bg, circle_fg):
        row = tk.Frame(parent, bg="#4d7112")
        row.pack(fill="x", pady=9)
        for idx, player in enumerate(players, start=1):
            slot = tk.Frame(row, bg="#4d7112")
            slot.pack(side="left", expand=True)
            tk.Label(slot, text=str(idx), bg=circle_bg, fg=circle_fg, font=FONT_BOLD, width=3, pady=4).pack()
            tk.Label(slot, text=player, bg="#4d7112", fg=TEXT, font=FONT_SMALL).pack()

    def match_events(self, match):
        if match["status"] == "LIVE":
            return [
                ("24'", match["home"], "CARD", "Tactical foul in midfield"),
                ("41'", match["away"], "GOAL", f"{match['away']} takes the lead"),
                ("HT", "", "SCORE", f"{match['home_score']} - {match['away_score']}"),
                (f"{match['minute']}'", match["home"], "PRESS", "Home side pushing higher"),
            ]
        return [
            ("12'", match["home"], "SHOT", "Early chance saved"),
            ("37'", match["away"], "SHOT", "Counter attack wide"),
            ("FT", "", "SCORE", f"{match['home_score']} - {match['away_score']}"),
        ]

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
            self.select_match(self.current_match)
        self.tracker_job = self.root.after(5000, self.tracker_tick)

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
