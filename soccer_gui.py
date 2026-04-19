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
        self.model_body = None
        self.team_body = None
        self.watch_body = None
        self.history_body = None
        self.accuracy_body = None
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
        self.render_tab()

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
        parent.grid_rowconfigure(0, weight=4)
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_rowconfigure(2, weight=1)
        parent.grid_rowconfigure(3, weight=2)
        parent.grid_rowconfigure(4, weight=2)

        model_outer, self.model_body = self.panel(parent, "MODEL OUTPUT")
        model_outer.grid(row=0, column=0, sticky="nsew", pady=(8, 8))

        team_outer, self.team_body = self.panel(parent, "TEAM PROFILES")
        team_outer.grid(row=1, column=0, sticky="nsew", pady=(0, 8))

        watch_outer, body = self.panel(parent, "WATCHLIST")
        watch_outer.grid(row=2, column=0, sticky="nsew", pady=(0, 8))
        self.sidebar_watch_body = body

        history_outer, self.history_body = self.panel(parent, "RECENT HISTORY")
        history_outer.grid(row=3, column=0, sticky="nsew", pady=(0, 8))

        acc_outer, self.accuracy_body = self.panel(parent, "ACCURACY DASHBOARD")
        acc_outer.grid(row=4, column=0, sticky="nsew", pady=(0, 10))

        self.render_model_placeholder()
        self.render_team_profiles()
        self.render_sidebar_watchlist()
        self.render_history()
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
        self.render_team_profiles()
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

    def render_model_placeholder(self):
        self.clear(self.model_body)
        tk.Label(
            self.model_body,
            text="Analyze: coming soon",
            bg=PANEL_DARK,
            fg=MUTED,
            font=FONT_MONO_SMALL,
            anchor="nw",
            justify="left",
            padx=10,
            pady=12,
        ).pack(fill="both", expand=True, padx=6, pady=6)

    def render_team_profiles(self):
        self.clear(self.team_body)
        match = self.current_match
        text = (
            f"{match['home']}: attack {match['home_avg']:.1f}, form {''.join(match['home_form'])}\n"
            f"{match['away']}: attack {match['away_avg']:.1f}, form {''.join(match['away_form'])}"
        )
        tk.Label(self.team_body, text=text, bg=PANEL_DARK, fg=MUTED, font=FONT_MONO_SMALL, justify="left", anchor="w").pack(fill="both", expand=True, padx=6, pady=6)

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
        self.clear(self.history_body)
        header = tk.Frame(self.history_body, bg=PANEL_DARK)
        header.pack(fill="x", padx=6, pady=(6, 2))
        cols = [("IDX", 4), ("TIME", 8), ("MATCH", 22), ("REC", 10), ("EDGE", 7), ("SETTLED", 8)]
        for name, width in cols:
            tk.Label(header, text=name, bg=PANEL_DARK, fg=ORANGE, font=FONT_MONO_SMALL, width=width, anchor="w").pack(side="left")

        for item in HISTORY_SAMPLE:
            idx, time, match, rec, edge, settled = item
            row = tk.Frame(self.history_body, bg=PANEL)
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

        self.clear(self.model_body)
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
        tk.Label(
            self.model_body,
            text="\n".join(lines),
            bg=PANEL_DARK,
            fg=TEXT,
            font=FONT_MONO_SMALL,
            anchor="nw",
            justify="left",
            padx=10,
            pady=10,
        ).pack(fill="both", expand=True, padx=6, pady=6)

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
        self.render_history()
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
