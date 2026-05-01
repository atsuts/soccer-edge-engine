"""
soccer_gui.py  —  Soccer Edge Engine  (fast, clean, production build)

Performance fixes:
- App opens instantly with mock data
- Right panel renders on demand only
- Match list uses lightweight rows
- API only called after user clicks Live button
- All tab content built lazily
- No blocking calls on startup
"""

import re
import queue
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk

from soccer_phase1_engine import SoccerEdgeEngine, MatchState, MarketInput
from history_logger import log_analysis, summarize_accuracy
from watchlist import add_match
from live_poller import LivePoller

APP_DIR = Path(__file__).resolve().parent

# ──────────────────────────────────────────────
# Theme
# ──────────────────────────────────────────────
BG         = "#0b1120"
TOP        = "#111827"
PANEL      = "#1e293b"
PANEL_DARK = "#0f172a"
ROW        = "#141d30"
ROW_ALT    = "#192437"
BORDER     = "#334155"
TEXT       = "#f8fafc"
MUTED      = "#94a3b8"
CYAN       = "#22d3ee"
CYAN_DARK  = "#0891b2"
GREEN      = "#22c55e"
GREEN_DARK = "#16a34a"
RED        = "#ef4444"
RED_DARK   = "#dc2626"
ORANGE     = "#f97316"
PURPLE     = "#6366f1"
GRAY_BTN   = "#475569"
YELLOW     = "#facc15"

FS   = ("Segoe UI", 9)
FB   = ("Segoe UI", 10, "bold")
FM   = ("Consolas", 9)
FT   = ("Segoe UI", 14, "bold")

# ──────────────────────────────────────────────
# Mock data (instant startup)
# ──────────────────────────────────────────────
MOCK_MATCHES = [
    {"id":1,"country":"England","league":"Premier League","tournament":"Premier League",
     "status":"LIVE","minute":67,"home":"Man City","away":"Liverpool",
     "home_score":1,"away_score":1,"edge":-0.2,"odds":(1.94,6.50,4.50),"pred":(30,25,45),
     "date":"Saturday, 11 April 2026","venue":"Etihad Stadium","referee":"Michael Oliver",
     "home_form":["W","W","L","D","W"],"away_form":["W","L","W","W","D"],
     "home_avg":2.1,"away_avg":1.8,"draw_price":40.0,"under_price":45.0,"over_price":60.0,
     "home_id":50,"away_id":40,"fixture_id":1208109},
    {"id":2,"country":"England","league":"Premier League","tournament":"Premier League",
     "status":"LIVE","minute":45,"home":"Arsenal","away":"Chelsea",
     "home_score":1,"away_score":0,"edge":5.7,"odds":(1.80,3.30,6.00),"pred":(29,31,40),
     "date":"Saturday, 11 April 2026","venue":"Emirates Stadium","referee":"Anthony Taylor",
     "home_form":["W","D","W","W","L"],"away_form":["L","W","D","W","W"],
     "home_avg":1.9,"away_avg":1.4,"draw_price":36.0,"under_price":52.0,"over_price":49.0,
     "home_id":42,"away_id":49,"fixture_id":1208110},
    {"id":3,"country":"England","league":"Premier League","tournament":"Premier League",
     "status":"UP","minute":0,"home":"Man United","away":"Newcastle",
     "home_score":0,"away_score":0,"edge":2.8,"odds":(4.70,3.90,4.00),"pred":(25,30,20),
     "date":"Saturday, 11 April 2026","venue":"Old Trafford","referee":"Paul Tierney",
     "home_form":["D","W","L","W","D"],"away_form":["W","W","D","L","W"],
     "home_avg":1.6,"away_avg":1.5,"draw_price":39.0,"under_price":55.0,"over_price":44.0,
     "home_id":33,"away_id":34,"fixture_id":1208111},
    {"id":4,"country":"Spain","league":"La Liga","tournament":"La Liga",
     "status":"UP","minute":0,"home":"Real Madrid","away":"Barcelona",
     "home_score":0,"away_score":0,"edge":-3.1,"odds":(2.80,4.60,5.80),"pred":(28,32,20),
     "date":"Saturday, 11 April 2026","venue":"Santiago Bernabeu","referee":"Jose Sanchez",
     "home_form":["W","W","W","D","L"],"away_form":["W","L","W","W","W"],
     "home_avg":2.3,"away_avg":2.0,"draw_price":42.0,"under_price":48.0,"over_price":54.0,
     "home_id":541,"away_id":529,"fixture_id":1208112},
    {"id":5,"country":"Spain","league":"La Liga","tournament":"La Liga",
     "status":"UP","minute":0,"home":"Atletico M","away":"Sevilla",
     "home_score":0,"away_score":0,"edge":3.9,"odds":(1.40,5.00,5.80),"pred":(24,30,18),
     "date":"Saturday, 11 April 2026","venue":"Metropolitano","referee":"Alejandro Hernandez",
     "home_form":["W","D","W","L","W"],"away_form":["D","L","W","D","L"],
     "home_avg":1.7,"away_avg":1.1,"draw_price":38.0,"under_price":58.0,"over_price":42.0,
     "home_id":530,"away_id":536,"fixture_id":1208113},
    {"id":6,"country":"Italy","league":"Serie A","tournament":"Serie A",
     "status":"UP","minute":0,"home":"Juventus","away":"AC Milan",
     "home_score":0,"away_score":0,"edge":6.8,"odds":(2.00,3.90,7.20),"pred":(18,30,20),
     "date":"Saturday, 11 April 2026","venue":"Allianz Stadium","referee":"Daniele Orsato",
     "home_form":["W","W","D","W","W"],"away_form":["L","W","D","W","D"],
     "home_avg":1.8,"away_avg":1.3,"draw_price":35.0,"under_price":60.0,"over_price":40.0,
     "home_id":496,"away_id":489,"fixture_id":1208114},
    {"id":7,"country":"Italy","league":"Serie A","tournament":"Serie A",
     "status":"UP","minute":0,"home":"Inter Milan","away":"Napoli",
     "home_score":0,"away_score":0,"edge":8.7,"odds":(1.70,4.60,7.80),"pred":(14,18,8),
     "date":"Saturday, 11 April 2026","venue":"San Siro","referee":"Marco Guida",
     "home_form":["W","W","W","D","W"],"away_form":["W","D","L","W","L"],
     "home_avg":2.2,"away_avg":1.4,"draw_price":37.0,"under_price":50.0,"over_price":51.0,
     "home_id":505,"away_id":492,"fixture_id":1208115},
    {"id":8,"country":"Germany","league":"Bundesliga","tournament":"Bundesliga",
     "status":"UP","minute":0,"home":"Bayern Mun","away":"Dortmund",
     "home_score":0,"away_score":0,"edge":-3.5,"odds":(1.75,5.40,6.50),"pred":(20,15,34),
     "date":"Saturday, 11 April 2026","venue":"Allianz Arena","referee":"Felix Zwayer",
     "home_form":["W","W","L","W","W"],"away_form":["D","W","W","L","W"],
     "home_avg":2.6,"away_avg":1.9,"draw_price":34.0,"under_price":44.0,"over_price":62.0,
     "home_id":157,"away_id":165,"fixture_id":1208116},
]

MATCHES = list(MOCK_MATCHES)

TOP_COUNTRIES = ["England","Spain","Italy","Germany","France"]
ALL_COUNTRIES = sorted(["Argentina","Australia","Austria","Belgium","Brazil","Chile",
    "Colombia","Croatia","Denmark","England","France","Germany","Greece","Italy",
    "Japan","Mexico","Netherlands","Norway","Poland","Portugal","Saudi Arabia",
    "Scotland","Spain","Sweden","Switzerland","Turkey","United States","Uruguay"])
TOP_LEAGUES = ["Premier League","La Liga","Serie A","Bundesliga","Ligue 1",
    "Champions League","Europa League","Eredivisie","Primeira Liga","MLS"]
ALL_LEAGUES = sorted(["2. Bundesliga","A-League","Allsvenskan","Belgian Pro League",
    "Brasileirao","Bundesliga","Championship","Champions League","EFL League One",
    "Eredivisie","Europa League","J1 League","La Liga","Liga MX","Ligue 1","MLS",
    "Premier League","Primeira Liga","Saudi Pro League","Scottish Premiership",
    "Serie A","Super Lig","Swiss Super League"])
COUNTRY_LEAGUES = {
    "England":["Premier League","Championship","EFL League One","EFL League Two","FA Cup","EFL Cup"],
    "Germany":["Bundesliga","2. Bundesliga","3. Liga","DFB Pokal"],
    "Spain":["La Liga","Segunda Division","Copa del Rey"],
    "Italy":["Serie A","Serie B","Coppa Italia"],
    "France":["Ligue 1","Ligue 2","Coupe de France"],
    "United States":["MLS","USL Championship"],
}
MAIN_TOURNAMENTS = ["Premier League","Champions League","Europa League","FA Cup",
    "Copa del Rey","Coppa Italia","DFB Pokal","Copa Libertadores"]
DATE_FILTERS = ["All","Live","Today","Tomorrow","Upcoming"]


def pref_order(top, all_):
    seen = {"All"}
    out  = ["All"] + [x for x in top if x not in seen and not seen.add(x)]
    out += [x for x in sorted(all_) if x not in seen and not seen.add(x)]
    return out


# ──────────────────────────────────────────────
# App
# ──────────────────────────────────────────────
class SoccerEdgeApp:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SOCCER EDGE ENGINE")
        self.root.geometry("1500x800")
        self.root.minsize(1200, 680)
        self.root.configure(bg=BG)

        # Core
        self.engine          = SoccerEdgeEngine()
        self.current_match   = MATCHES[0]
        self.live_api_active = False
        self.watchlist_ids   = set()

        # Tracker
        self.tracker_running = False
        self.tracker_job     = None

        # Replay
        self.replay_minute       = None
        self.replay_running      = False
        self.replay_job          = None
        self.replay_start_minute = None
        self.replay_slider       = None
        self.replay_refresh      = None
        self.replay_max_minute   = 0

        # UI state
        self._match_row_cache           = {}   # match_id → {frame, status, minute, ...}
        self._maximized_overlay         = None  # overlay frame when a panel is maximized
        self._user_preds                = []    # user prediction game records
        self._pred_win                  = None  # prediction window reference
        self._cmp_win                   = None  # comparison window reference
        self.tab_name                   = tk.StringVar(value="Stats Replay")
        self.quick_query                = tk.StringVar(value="")
        self.chat_message               = tk.StringVar(value="")
        self.guest_handle               = tk.StringVar(value="Guest001")
        self.guest_market               = tk.StringVar(value="1X2")
        self.guest_pick                 = tk.StringVar(value="")
        self.selected_odds_book         = None
        self.selected_prediction_source = None
        self.selected_player_detail     = None
        self.match_chats                = {}
        self.match_chat_room            = {}
        self.match_challenges           = {}
        self.challenge_history          = []
        self.center_split_initialized   = False

        # Filters
        self.filters = {
            "country":    tk.StringVar(value="All"),
            "league":     tk.StringVar(value="All"),
            "tournament": tk.StringVar(value="All"),
            "date":       tk.StringVar(value="All"),
        }

        # Widget refs (populated in build_*)
        self.status_label      = None
        self.live_api_btn      = None
        self.tracker_status    = None
        self.matches_canvas    = None
        self.matches_frame     = None
        self.watchlist_canvas  = None
        self.watchlist_frame   = None
        self.watch_body        = None
        self.center_split      = None
        self.tab_content       = None
        self.odds_body         = None
        self.predictions_body  = None
        self.recommendation_body = None
        self.quality_body      = None
        self.source_body       = None
        self.chat_preview_body = None
        self.accuracy_body     = None
        self.sidebar_watch_body= None
        self.score_labels      = {}
        self.meta_labels       = {}
        self.filter_combos     = {}

        # Live polling
        self.poller     = LivePoller()
        self.poll_queue = self.poller.queue

        # Build UI instantly — no API calls
        self._configure_styles()
        self._build_ui()
        self.challenge_history = self._seed_challenge_history()

        # Populate UI with mock data (deferred so window is visible first)
        self.root.after(120, self._initial_render)
        self.root.after(400, self._process_poll_queue)

    # ──────────────────────────────────────────
    # Startup
    # ──────────────────────────────────────────

    def _initial_render(self):
        """Called after window is visible — ensures soccer frame is shown and populated."""
        # Force the soccer frame to be visible and geometry to be computed
        self._soccer_frame.grid(row=0, column=0, sticky="nsew")
        self.root.update_idletasks()

        # Retry if the window hasn't been drawn yet (width = 0 or 1)
        w = self.root.winfo_width()
        if w <= 1:
            self.root.after(80, self._initial_render)
            return

        self.render_matches()
        self.render_watchlist()
        self.select_match(self.current_match, refresh=False)

    # ──────────────────────────────────────────
    # Live API polling
    # ──────────────────────────────────────────

    def _process_poll_queue(self):
        try:
            while True:
                event_type, data = self.poll_queue.get_nowait()
                if event_type == "live_matches":
                    self._ingest_live(data)
                elif event_type == "today_matches":
                    self._ingest_today(data)
                elif event_type == "error":
                    if self.status_label:
                        self.status_label.config(
                            text=f"API: {str(data)[:70]}", fg=RED)
        except queue.Empty:
            pass
        self.root.after(500, self._process_poll_queue)

    def _ingest_live(self, api_matches):
        if not api_matches:
            return
        global MATCHES
        existing = {m["id"]: i for i, m in enumerate(MATCHES)}
        for m in api_matches:
            fid = m.get("fixture_id")
            if not fid:
                continue
            st = m.get("status","")
            gui_st = "LIVE" if st in ("1H","2H","HT","ET","P","LIVE") else st
            if fid in existing:
                idx = existing[fid]
                MATCHES[idx].update({
                    "status":     gui_st,
                    "minute":     int(m.get("minute") or 0),
                    "home_score": int(m.get("home_goals") or 0),
                    "away_score": int(m.get("away_goals") or 0),
                })
            else:
                entry = self._api_to_match(m, gui_st)
                MATCHES.append(entry)
                existing[fid] = len(MATCHES) - 1
        live_n = sum(1 for x in MATCHES if x.get("status") == "LIVE")
        if self.status_label:
            self.status_label.config(
                text=f"Last Load: live API  |  Matches: {len(MATCHES)}  |  Live: {live_n}",
                fg=GREEN)
        self.render_matches()

    def _ingest_today(self, api_matches):
        global MATCHES
        existing = {m["id"] for m in MATCHES}
        added = 0
        for m in api_matches:
            fid = m.get("fixture_id")
            if not fid or fid in existing:
                continue
            MATCHES.append(self._api_to_match(m, "UP"))
            existing.add(fid)
            added += 1
        if added:
            self.render_matches()

    def _api_to_match(self, m, gui_st):
        return {
            "id": m.get("fixture_id"), "country": m.get("country",""),
            "league": m.get("league",""), "tournament": m.get("league",""),
            "status": gui_st, "minute": int(m.get("minute") or 0),
            "home": m["home"], "away": m["away"],
            "home_score": int(m.get("home_goals") or 0),
            "away_score": int(m.get("away_goals") or 0),
            "edge": 0.0, "odds": (2.0,3.5,4.0), "pred": (33,33,34),
            "date": m.get("date","")[:10], "venue": m.get("venue",""),
            "referee": m.get("referee","") or "",
            "home_form": ["?","?","?","?","?"],
            "away_form": ["?","?","?","?","?"],
            "home_avg": 1.5, "away_avg": 1.5,
            "draw_price": 33.0, "under_price": 50.0, "over_price": 50.0,
            "home_id": m.get("home_id"), "away_id": m.get("away_id"),
            "fixture_id": m.get("fixture_id"),
        }

    def _fetch_today_bg(self):
        try:
            from live_data import fetch_matches_by_date, today_str
            matches = fetch_matches_by_date(today_str())
            if matches:
                self.poll_queue.put(("today_matches", matches))
        except Exception as e:
            self.poll_queue.put(("error", f"today: {e}"))

    def _run_live_analysis(self, match):
        try:
            from match_bridge import analyze_from_gui_match
            result = analyze_from_gui_match(match)
            if result:
                self.root.after(0, lambda: self._apply_result(match, result))
        except Exception as e:
            print(f"[analysis] {e}")

    def _apply_result(self, match, result):
        if self.current_match["id"] != match["id"]:
            return
        match["edge"] = round(result.best_edge, 1)
        hx, ax = result.probabilities.get("xg", (0.0, 0.0))
        match["home_avg"] = round(hx, 2)
        match["away_avg"] = round(ax, 2)
        if "edge" in self.score_labels:
            self.score_labels["edge"].config(
                text=f"{result.best_edge:+.1f}",
                fg=GREEN if result.best_edge >= 0 else RED)
        self._render_right_panel()
        if self.tracker_status:
            self.tracker_status.config(
                text=f"Live: {result.best_pick}  edge {result.best_edge:+.1f}  conf {int(result.confidence*100)}%",
                fg=CYAN)

    # ──────────────────────────────────────────
    # Switch Live API
    # ──────────────────────────────────────────

    def _update_poll_interval(self):
        """Update live polling interval based on radio button selection."""
        import live_poller
        label = self._refresh_interval_var.get()
        mapping = {"15s": 15, "1min": 60, "2min": 120}
        secs = mapping.get(label, 15)
        live_poller.POLL_INTERVAL_LIVE = secs
        if self.status_label:
            self.status_label.config(
                text=f"Refresh interval: {label}", fg=MUTED)

    def switch_live_api(self):
        if self.live_api_active:
            self.poller.stop()
            self.live_api_active = False
            self.live_api_btn.config(text="Switch to Live API", bg="#5fa8d3", fg=TEXT)
            self.status_label.config(text="Live API stopped.", fg=MUTED)
            global MATCHES
            MATCHES.clear()
            MATCHES.extend(list(MOCK_MATCHES))
            self._match_row_cache.clear()
            self.render_matches()
        else:
            self.status_label.config(text="Connecting to Live API…", fg=YELLOW)
            self.live_api_btn.config(text="Connecting…", bg=YELLOW, fg=BG)
            self.root.update_idletasks()
            self.poller.start()
            self.live_api_active = True
            self.live_api_btn.config(text="Stop Live API  [LIVE]", bg=GREEN_DARK, fg=TEXT)
            threading.Thread(target=self._fetch_today_bg, daemon=True).start()

    # ──────────────────────────────────────────
    # Styles
    # ──────────────────────────────────────────

    def _configure_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("D.TCombobox",
            fieldbackground=PANEL_DARK, background=PANEL_DARK,
            foreground=TEXT, arrowcolor=TEXT,
            bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER, padding=3)
        s.map("D.TCombobox",
            fieldbackground=[("readonly", PANEL_DARK)],
            foreground=[("readonly", TEXT)])

    # ──────────────────────────────────────────
    # UI skeleton (built once, fast)
    # ──────────────────────────────────────────

    def _build_ui(self):
        # ── Top bar ──
        top = tk.Frame(self.root, bg=TOP, height=50)
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Label(top, text="SOCCER EDGE ENGINE", bg=TOP, fg="#7dd3fc",
            font=("Consolas",16,"bold"), anchor="w").pack(side="left", padx=10)

        # Screen nav buttons (right side of topbar)
        nav = tk.Frame(top, bg=TOP)
        nav.pack(side="right", padx=8)

        tk.Button(top, text="Test Speed", bg="#334155", fg=TEXT,
            activebackground="#475569", relief="flat", font=FS, padx=10,
            command=self.test_speed).pack(side="right", padx=4)

        self._nav_scanner_btn = tk.Button(nav,
            text="⚡ AI Market Scanner",
            bg=PURPLE, fg=TEXT, activebackground="#7c3aed",
            relief="flat", font=FB, padx=14, pady=6,
            command=lambda: self._show_screen("scanner"))
        self._nav_scanner_btn.pack(side="right", padx=(4,0))

        self._nav_soccer_btn = tk.Button(nav,
            text="⚽ Match Center",
            bg=CYAN_DARK, fg=TEXT, activebackground="#0e7490",
            relief="flat", font=FB, padx=14, pady=6,
            command=lambda: self._show_screen("soccer"))
        self._nav_soccer_btn.pack(side="right", padx=(4,0))

        # Layout preset buttons (only visible on soccer screen)
        sep = tk.Frame(nav, bg="#334155", width=1)
        sep.pack(side="right", fill="y", padx=6, pady=6)

        tk.Label(nav, text="LAYOUT:", bg=TOP, fg=MUTED,
            font=("Segoe UI", 8)).pack(side="right", padx=(0,4))

        self._layout_btns  = {}              # preset_name → Button widget
        self._active_preset = "equal"        # startup default is the equal/square layout

        for label, preset, tip in [
            ("□", "equal",        "Equal split"),   # □ clean outlined square
            ("▣", "default",      "Default view"),
            ("◧", "focus_left",   "Focus left panel"),
            ("◫", "focus_center", "Focus center panel"),
            ("◨", "focus_right",  "Focus right panel"),
        ]:
            btn = tk.Button(nav, text=label, bg="#243244", fg=CYAN,
                activebackground="#334155", relief="flat",
                font=("Segoe UI", 11), padx=6, pady=2,
                command=lambda p=preset: self._layout_preset(p))
            btn.pack(side="right", padx=1)
            self._layout_btns[preset] = btn

        tk.Button(nav, text="↺ Reset", bg="#243244", fg=MUTED,
            activebackground="#334155", relief="flat",
            font=("Segoe UI", 8), padx=6, pady=2,
            command=self._reset_layout
        ).pack(side="right", padx=(1,0))

        sep2 = tk.Frame(nav, bg="#334155", width=1)
        sep2.pack(side="right", fill="y", padx=6, pady=6)

        # ── Screen container ──
        self._screen_container = tk.Frame(self.root, bg=BG)
        self._screen_container.pack(fill="both", expand=True)
        self._screen_container.grid_rowconfigure(0, weight=1)
        self._screen_container.grid_columnconfigure(0, weight=1)

        # ── Soccer screen — fully resizable PanedWindow layout ──
        self._soccer_frame = tk.Frame(self._screen_container, bg=BG)
        self._soccer_frame.grid(row=0, column=0, sticky="nsew")
        self._soccer_frame.grid_rowconfigure(0, weight=1)
        self._soccer_frame.grid_columnconfigure(0, weight=1)

        # Horizontal paned window — left | center | right (drag sashes to resize)
        self._h_pane = tk.PanedWindow(
            self._soccer_frame,
            orient="horizontal",
            bg="#22d3ee",
            sashwidth=8,
            sashrelief="raised",
            opaqueresize=True,
            showhandle=True,
            handlesize=12,
            handlepad=100,
        )
        self._h_pane.grid(row=0, column=0, sticky="nsew")

        left   = tk.Frame(self._h_pane, bg=BG)
        center = tk.Frame(self._h_pane, bg=BG)
        right  = tk.Frame(self._h_pane, bg=BG)

        self._h_pane.add(left,   minsize=220, sticky="nsew")
        self._h_pane.add(center, minsize=380, sticky="nsew")
        self._h_pane.add(right,  minsize=200, sticky="nsew")

        self._build_left(left)
        self._build_center(center)
        self._build_right(right)

        # Set initial sash positions — after window is drawn AND data rendered
        self.root.after(550, self._set_initial_sashes)

        # ── Scanner screen (lazy — built on first visit) ──
        self._scanner_frame = None
        self._current_screen = "soccer"

    def _set_right_sashes(self, pane):
        """Set right panel sash positions proportionally."""
        try:
            h = pane.winfo_height()
            if h <= 1:
                self.root.after(100, lambda: self._set_right_sashes(pane))
                return
            # 6 sections: 28% decision, 16% quality, 10% watchlist,
            #             16% chat, 16% source, 14% accuracy
            positions = [0.28, 0.44, 0.54, 0.70, 0.86]
            for i, frac in enumerate(positions):
                try:
                    pane.sash_place(i, 0, int(h * frac))
                except Exception:
                    pass
        except Exception:
            pass

    def _set_initial_sashes(self):
        """
        Set panel widths after window is fully drawn.
        Startup default: "equal" layout (the big □ square button).
        Retries until the window has real geometry.
        """
        try:
            self.root.update_idletasks()
            w = self._h_pane.winfo_width()
            if w <= 1:
                self.root.after(150, self._set_initial_sashes)
                return
            # Apply "equal" layout: three panels in equal thirds
            self._h_pane.sash_place(0, int(w * 0.33), 0)
            self._h_pane.sash_place(1, int(w * 0.67), 0)
            # Also set right panel and center split after a short delay
            self.root.after(80, self._set_center_sash)
            if hasattr(self, "_rv_pane") and self._rv_pane:
                self.root.after(120, lambda: self._set_right_sashes(self._rv_pane))
            # Highlight the equal/square layout button on startup
            self.set_active_layout_button("equal")
        except Exception as e:
            print(f"[sash] {e}")

    def _set_center_sash(self):
        """Set center panel vertical split: 70% analysis / 30% odds board."""
        try:
            if not self.center_split:
                return
            h = self.center_split.winfo_height()
            if h <= 1:
                self.root.after(100, self._set_center_sash)
                return
            self.center_split.sash_place(0, 0, int(h * 0.70))
        except Exception:
            pass

    def set_active_layout_button(self, preset: str):
        """
        Highlight the active layout button; restore all others to normal style.
        Called whenever a layout is applied (user click or startup).
        """
        self._active_preset = preset
        for name, btn in getattr(self, "_layout_btns", {}).items():
            if name == preset:
                # Active: bright cyan background + white text
                btn.config(bg="#0e7490", fg="#ffffff",
                           relief="solid", highlightthickness=1,
                           highlightbackground="#22d3ee")
            else:
                # Inactive: dim background
                btn.config(bg="#243244", fg="#22d3ee",
                           relief="flat", highlightthickness=0)

    def _reset_layout(self):
        """Reset panels to default proportions — routes to correct screen."""
        if self._current_screen == "scanner":
            if self._scanner_frame is not None:
                self._scanner_frame.apply_layout("default")
        else:
            self.root.after(50, self._set_initial_sashes)
            if hasattr(self, "_rv_pane") and self._rv_pane:
                self.root.after(100, lambda: self._set_right_sashes(self._rv_pane))
        self.set_active_layout_button("equal")

    def _layout_preset(self, preset: str):
        """Apply a layout preset — routes to correct screen handler."""
        if self._current_screen == "scanner":
            self._scanner_layout(preset)
        else:
            self._soccer_layout(preset)
        self.set_active_layout_button(preset)

    def _scanner_layout(self, preset: str):
        """Apply layout to AI Market Scanner screen."""
        if self._scanner_frame is None:
            return
        self._scanner_frame.apply_layout(preset)

    def _soccer_layout(self, preset: str):
        """Apply layout to Match Center screen."""
        try:
            w = self._h_pane.winfo_width()
            if w <= 1:
                return
            if preset == "focus_center":
                self._h_pane.sash_place(0, int(w * 0.15), 0)
                self._h_pane.sash_place(1, int(w * 0.85), 0)
            elif preset == "focus_left":
                self._h_pane.sash_place(0, int(w * 0.50), 0)
                self._h_pane.sash_place(1, int(w * 0.78), 0)
            elif preset == "focus_right":
                self._h_pane.sash_place(0, int(w * 0.20), 0)
                self._h_pane.sash_place(1, int(w * 0.52), 0)
            elif preset == "equal":
                self._h_pane.sash_place(0, int(w * 0.33), 0)
                self._h_pane.sash_place(1, int(w * 0.66), 0)
            elif preset == "default":
                self.root.after(50, self._set_initial_sashes)
            if hasattr(self, "_rv_pane") and self._rv_pane:
                self.root.after(60, lambda: self._set_right_sashes(self._rv_pane))
        except Exception as e:
            print(f"[soccer layout] {e}")

    def _show_screen(self, screen: str):
        """Switch between 'soccer' and 'scanner' screens."""
        if screen == self._current_screen:
            return
        self._current_screen = screen

        if screen == "scanner":
            self._soccer_frame.grid_remove()
            if self._scanner_frame is None:
                # Build scanner on first visit
                from ai_market_scanner import AIMarketScannerFrame
                self._scanner_frame = AIMarketScannerFrame(self._screen_container)
                self._scanner_frame.grid(row=0, column=0, sticky="nsew")
            else:
                self._scanner_frame.grid()
            # Update nav button styles
            self._nav_scanner_btn.config(bg="#7c3aed")
            self._nav_soccer_btn.config(bg=CYAN_DARK)

        else:  # soccer
            if self._scanner_frame is not None:
                self._scanner_frame.grid_remove()
            self._soccer_frame.grid()
            self._nav_soccer_btn.config(bg="#0e7490")
            self._nav_scanner_btn.config(bg=PURPLE)

    # ── LEFT PANEL ────────────────────────────

    def _build_left(self, p):
        p.grid_rowconfigure(3, weight=7)
        p.grid_rowconfigure(4, weight=3)
        p.grid_columnconfigure(0, weight=1)

        self.status_label = tk.Label(p,
            text="Last Load: local mock  |  Matches: 8",
            bg=PANEL, fg=MUTED, font=FM, anchor="w", padx=6)
        self.status_label.grid(row=0, column=0, sticky="ew", pady=(6,4))

        # Filters row
        frow = tk.Frame(p, bg=PANEL)
        frow.grid(row=1, column=0, sticky="ew", pady=(0,6))
        for i in range(4):
            frow.grid_columnconfigure(i, weight=1)
        self._add_filter(frow,"COUNTRY","country",pref_order(TOP_COUNTRIES,ALL_COUNTRIES))
        self._add_filter(frow,"LEAGUE","league",self._league_opts("All"))
        self._add_filter(frow,"TOURNAMENT","tournament",pref_order(MAIN_TOURNAMENTS,MAIN_TOURNAMENTS))
        self._add_filter(frow,"DATE","date",DATE_FILTERS)

        # Live API button + refresh interval selector on same row
        live_row = tk.Frame(p, bg=BG)
        live_row.grid(row=2, column=0, sticky="ew", pady=(0,6))
        live_row.grid_columnconfigure(0, weight=1)

        self.live_api_btn = tk.Button(live_row, text="Switch to Live API",
            bg="#5fa8d3", fg=TEXT, activebackground="#72b8df",
            relief="flat", font=FB, pady=4, command=self.switch_live_api)
        self.live_api_btn.grid(row=0, column=0, sticky="ew")

        # Refresh interval control
        ri_row = tk.Frame(live_row, bg=PANEL_DARK)
        ri_row.grid(row=1, column=0, sticky="ew", pady=(2,0))
        tk.Label(ri_row, text="Refresh:", bg=PANEL_DARK, fg=MUTED,
            font=FS).pack(side="left", padx=6)
        self._refresh_interval_var = tk.StringVar(value="15s")
        for label in ["15s", "1min", "2min"]:
            tk.Radiobutton(ri_row, text=label,
                variable=self._refresh_interval_var, value=label,
                bg=PANEL_DARK, fg=TEXT, selectcolor=PANEL,
                activebackground=PANEL_DARK, font=FS,
                command=self._update_poll_interval).pack(side="left", padx=4)

        mo, mb = self._panel(p, "MATCHES")
        mo.grid(row=3, column=0, sticky="nsew", pady=(0,6))
        mb.grid_rowconfigure(0, weight=1)
        mb.grid_columnconfigure(0, weight=1)
        self._build_match_scroller(mb)

        wo, self.watch_body = self._panel(p, "WATCHLIST")
        wo.grid(row=4, column=0, sticky="nsew", pady=(0,6))
        self.watch_body.grid_rowconfigure(0, weight=1)
        self.watch_body.grid_columnconfigure(0, weight=1)
        self._build_watchlist_scroller(self.watch_body)

    def _add_filter(self, p, title, key, values):
        idx = len(p.grid_slaves())
        f = tk.Frame(p, bg=PANEL)
        f.grid(row=0, column=idx, sticky="ew", padx=4, pady=4)
        tk.Label(f, text=title, bg=PANEL, fg=CYAN, font=FS, anchor="w").pack(fill="x")
        cb = ttk.Combobox(f, textvariable=self.filters[key],
            values=values, state="readonly", style="D.TCombobox",
            height=12, font=FS)
        cb.pack(fill="x", pady=(1,0))
        cb.bind("<<ComboboxSelected>>", lambda _e, k=key: self._on_filter(k))
        self.filter_combos[key] = cb

    def _on_filter(self, key):
        if key == "country":
            country = self.filters["country"].get()
            vals = self._league_opts(country)
            self.filter_combos["league"].configure(values=vals)
            if self.filters["league"].get() not in vals:
                self.filters["league"].set("All")
        # Clear cache so filter changes force a full rebuild
        self._match_row_cache.clear()
        self.render_matches()

    def _league_opts(self, country):
        if country == "All":
            return pref_order(TOP_LEAGUES, ALL_LEAGUES)
        return ["All"] + COUNTRY_LEAGUES.get(country, [])

    def _build_match_scroller(self, p):
        self.matches_canvas = tk.Canvas(p, bg=PANEL_DARK, highlightthickness=0)
        sb = tk.Scrollbar(p, orient="vertical", command=self.matches_canvas.yview)
        self.matches_canvas.configure(yscrollcommand=sb.set)
        self.matches_canvas.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        self.matches_frame = tk.Frame(self.matches_canvas, bg=PANEL_DARK)
        wid = self.matches_canvas.create_window((0,0), window=self.matches_frame, anchor="nw")
        self.matches_frame.bind("<Configure>",
            lambda _e: self.matches_canvas.configure(scrollregion=self.matches_canvas.bbox("all")))
        self.matches_canvas.bind("<Configure>",
            lambda e: self.matches_canvas.itemconfigure(wid, width=e.width))
        self.matches_canvas.bind_all("<MouseWheel>", self._mousewheel)

    def _build_watchlist_scroller(self, p):
        self.watchlist_canvas = tk.Canvas(p, bg=PANEL_DARK, highlightthickness=0)
        sb = tk.Scrollbar(p, orient="vertical", command=self.watchlist_canvas.yview)
        self.watchlist_canvas.configure(yscrollcommand=sb.set)
        self.watchlist_canvas.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        self.watchlist_frame = tk.Frame(self.watchlist_canvas, bg=PANEL_DARK)
        wid = self.watchlist_canvas.create_window((0,0), window=self.watchlist_frame, anchor="nw")
        self.watchlist_frame.bind("<Configure>",
            lambda _e: self.watchlist_canvas.configure(scrollregion=self.watchlist_canvas.bbox("all")))
        self.watchlist_canvas.bind("<Configure>",
            lambda e: self.watchlist_canvas.itemconfigure(wid, width=e.width))

    # ── CENTER PANEL ──────────────────────────

    def _build_center(self, p):
        p.grid_rowconfigure(1, weight=1)
        p.grid_columnconfigure(0, weight=1)

        tk.Label(p, text="MATCH ANALYSIS", bg=BG, fg=CYAN,
            font=FB, anchor="w").grid(row=0, column=0, sticky="ew", pady=(6,4))

        self.center_split = tk.PanedWindow(p, orient="vertical",
            bg="#22d3ee",
            sashwidth=8,
            sashrelief="raised",
            opaqueresize=True,
            showhandle=True,
            handlesize=12,
            handlepad=60)
        self.center_split.grid(row=1, column=0, sticky="nsew", pady=(0,6))
        self.center_split.bind("<Configure>", self._split_configure)

        top_w    = tk.Frame(self.center_split, bg=BG)
        bottom_w = tk.Frame(self.center_split, bg=BG)
        self.center_split.add(top_w,    minsize=360, sticky="nsew")
        self.center_split.add(bottom_w, minsize=180, sticky="nsew")

        body = tk.Frame(top_w, bg=PANEL,
            highlightbackground=BORDER, highlightthickness=1)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(3, weight=1)

        self._build_scoreboard(body)
        self._build_meta(body)
        self._build_tabs(body)

        self.tab_content = tk.Frame(body, bg=PANEL)
        self.tab_content.grid(row=3, column=0, sticky="nsew", padx=6)

        self._build_action_bar(body)
        self._build_markets(bottom_w)

    def _split_configure(self, _e=None):
        if self.center_split_initialized:
            return
        h = self.center_split.winfo_height()
        if h <= 1:
            return
        self.center_split.sash_place(0, 0, int(h * 0.68))
        self.center_split_initialized = True

    def _build_scoreboard(self, p):
        sb = tk.Frame(p, bg=PANEL)
        sb.grid(row=0, column=0, sticky="ew", padx=8, pady=(8,6))
        sb.grid_columnconfigure(0, weight=1)
        sb.grid_columnconfigure(2, weight=1)

        # Home
        hb = tk.Frame(sb, bg=PANEL)
        hb.grid(row=0, column=0, sticky="nsew")
        tk.Label(hb, text="HOME", bg=PANEL, fg=CYAN, font=FS).pack()
        self.score_labels["home_badge"] = tk.Label(hb, text="MC",
            bg="#facc15", fg="#111827", font=("Segoe UI",11,"bold"), width=4, pady=4)
        self.score_labels["home_badge"].pack(pady=(0,3))
        self.score_labels["home"] = tk.Label(hb, text="", bg=PANEL, fg=TEXT,
            font=("Segoe UI",11,"bold"))
        self.score_labels["home"].pack()
        self.score_labels["home_form"] = tk.Label(hb, text="", bg=PANEL, fg=MUTED, font=FS)
        self.score_labels["home_form"].pack()
        self.score_labels["home_goals"] = tk.Label(hb, text="", bg=PANEL, fg=MUTED, font=FS)
        self.score_labels["home_goals"].pack()

        # Center score
        sc = tk.Frame(sb, bg=PANEL)
        sc.grid(row=0, column=1, sticky="n", padx=40)
        line = tk.Frame(sc, bg=PANEL)
        line.pack()
        self.score_labels["home_score"] = tk.Label(line, text="0", bg=PANEL,
            fg=ORANGE, font=("Consolas",20,"bold"))
        self.score_labels["home_score"].pack(side="left", padx=6)
        tk.Label(line, text="-", bg=PANEL, fg=ORANGE,
            font=("Consolas",20,"bold")).pack(side="left")
        self.score_labels["away_score"] = tk.Label(line, text="0", bg=PANEL,
            fg=ORANGE, font=("Consolas",20,"bold"))
        self.score_labels["away_score"].pack(side="left", padx=6)
        self.score_labels["minute"] = tk.Label(sc, text="00'", bg=PANEL, fg=CYAN, font=FM)
        self.score_labels["minute"].pack()
        self.score_labels["status"] = tk.Label(sc, text="LIVE", bg=PANEL, fg=GREEN, font=FS)
        self.score_labels["status"].pack()
        self.score_labels["edge"] = tk.Label(sc, text="+0.0",
            bg=PANEL_DARK, fg=TEXT, font=FM, padx=8, pady=2)
        self.score_labels["edge"].pack(pady=(4,0))
        self.score_labels["replay_state"] = tk.Label(sc, text="", bg=PANEL, fg=MUTED, font=FS)
        self.score_labels["replay_state"].pack(pady=(3,0))

        # Away
        ab = tk.Frame(sb, bg=PANEL)
        ab.grid(row=0, column=2, sticky="nsew")
        tk.Label(ab, text="AWAY", bg=PANEL, fg=RED, font=FS).pack()
        self.score_labels["away_badge"] = tk.Label(ab, text="LIV",
            bg="#ef4444", fg=TEXT, font=("Segoe UI",11,"bold"), width=4, pady=4)
        self.score_labels["away_badge"].pack(pady=(0,3))
        self.score_labels["away"] = tk.Label(ab, text="", bg=PANEL, fg=TEXT,
            font=("Segoe UI",11,"bold"))
        self.score_labels["away"].pack()
        self.score_labels["away_form"] = tk.Label(ab, text="", bg=PANEL, fg=MUTED, font=FS)
        self.score_labels["away_form"].pack()
        self.score_labels["away_goals"] = tk.Label(ab, text="", bg=PANEL, fg=MUTED, font=FS)
        self.score_labels["away_goals"].pack()

    def _build_meta(self, p):
        meta = tk.Frame(p, bg=PANEL_DARK)
        meta.grid(row=1, column=0, sticky="ew", padx=8, pady=(0,6))
        for i in range(3):
            meta.grid_columnconfigure(i, weight=1)
        self.meta_labels["date"]    = self._meta_pair(meta, 0, "Date")
        self.meta_labels["venue"]   = self._meta_pair(meta, 1, "Venue")
        self.meta_labels["referee"] = self._meta_pair(meta, 2, "Referee")

    def _meta_pair(self, p, col, title):
        f = tk.Frame(p, bg=PANEL_DARK)
        f.grid(row=0, column=col, sticky="ew", padx=6, pady=5)
        tk.Label(f, text=f"{title}:", bg=PANEL_DARK, fg=CYAN,
            font=FS, anchor="w").pack(side="left")
        lb = tk.Label(f, text="", bg=PANEL_DARK, fg=MUTED, font=FS, anchor="w")
        lb.pack(side="left", padx=(3,0))
        return lb

    def _build_tabs(self, p):
        self._tabs_frame = tk.Frame(p, bg=PANEL)
        self._tabs_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=(0,6))
        self._redraw_tabs()

    def _redraw_tabs(self):
        for w in self._tabs_frame.winfo_children():
            w.destroy()
        tabs = ["Overview","Stats Replay","Attack","Control","Defense","Line-ups","News","Weather","Form","Players","Video","Trivia","Chat","Table","H2H"]
        for i, name in enumerate(tabs):
            self._tabs_frame.grid_columnconfigure(i, weight=1)
            active = name == self.tab_name.get()
            tk.Button(self._tabs_frame, text=name,
                bg=PANEL_DARK if active else BG,
                fg=ORANGE if active else MUTED,
                activebackground=PANEL_DARK, activeforeground=ORANGE,
                relief="flat", font=FB, pady=5,
                command=lambda n=name: self.set_tab(n)
            ).grid(row=0, column=i, sticky="ew")

    def _build_action_bar(self, p):
        bar = tk.Frame(p, bg=BG)
        bar.grid(row=4, column=0, sticky="ew", padx=6, pady=(6,8))
        bar.grid_columnconfigure(0, weight=1)
        bar.grid_columnconfigure(1, weight=2)
        bar.grid_columnconfigure(2, weight=1)

        lf = tk.Frame(bar, bg=BG)
        lf.grid(row=0, column=0, sticky="w")
        self._btn(lf, "+ Watch", PURPLE, self.add_to_watchlist).pack(side="left", padx=(0,4))
        self._btn(lf, "Remove",  GRAY_BTN, self.remove_from_watchlist).pack(side="left")

        cf = tk.Frame(bar, bg=BG)
        cf.grid(row=0, column=1, sticky="ew", padx=8)
        cf.grid_columnconfigure(0, weight=1)
        qw = tk.Frame(cf, bg="#243244",
            highlightbackground=BORDER, highlightthickness=1)
        qw.grid(row=0, column=0, sticky="ew")
        tk.Label(qw, text="Quick Find", bg="#243244", fg=CYAN,
            font=FB, padx=8).pack(side="left")
        qe = tk.Entry(qw, textvariable=self.quick_query,
            bg=PANEL_DARK, fg=TEXT, insertbackground=TEXT,
            relief="flat", font=FS)
        qe.pack(side="left", fill="x", expand=True, padx=(0,4), pady=6)
        qe.bind("<Return>", lambda _e: self.quick_find())
        self._btn(qw,"Go",  CYAN_DARK, self.quick_find,       width=7, pady=6).pack(side="left", padx=(0,4), pady=3)
        self._btn(qw,"Live",ORANGE,    self.reset_to_live,     width=7, pady=6).pack(side="left", padx=(0,4), pady=3)
        tk.Label(cf, text="Try: shots, lineups, possession, h2h, table",
            bg=BG, fg=MUTED, font=FS, anchor="w").grid(row=1, column=0, sticky="ew", pady=(2,0))

        rf = tk.Frame(bar, bg=BG)
        rf.grid(row=0, column=2, sticky="e")
        self._btn(rf,"Predictions",  PURPLE,    self._show_predictions_window).pack(side="left",padx=(0,4))
        self._btn(rf,"Team vs Team", "#0e7490",  self._show_team_comparison).pack(side="left",padx=(0,4))
        self._btn(rf,"Start Tracker",GREEN_DARK, self.start_tracker).pack(side="left",padx=(0,4))
        self._btn(rf,"Stop Tracker", GRAY_BTN,   self.stop_tracker).pack(side="left")

        self.tracker_status = tk.Label(p, text="", bg=PANEL, fg=MUTED, font=FS, anchor="w")
        self.tracker_status.grid(row=5, column=0, sticky="ew", padx=8, pady=(0,6))

    def _build_markets(self, p):
        mf = tk.Frame(p, bg=BG)
        mf.pack(fill="both", expand=True)
        mf.grid_columnconfigure(0, weight=1, uniform="m")
        mf.grid_columnconfigure(1, weight=1, uniform="m")
        mf.grid_rowconfigure(0, weight=1)
        oo, self.odds_body        = self._panel(mf, "ODDS BOARD")
        po, self.predictions_body = self._panel(mf, "PREDICTION FEED")
        oo.grid(row=0, column=0, sticky="nsew", padx=(0,3))
        po.grid(row=0, column=1, sticky="nsew", padx=(3,0))

    # ── RIGHT PANEL ───────────────────────────

    def _build_right(self, p):
        p.grid_columnconfigure(0, weight=1)
        p.grid_rowconfigure(0, weight=1)

        # Vertical PanedWindow for right panel — all sections resizable
        rv = tk.PanedWindow(p, orient="vertical",
            bg="#22d3ee",
            sashwidth=8,
            sashrelief="raised",
            opaqueresize=True,
            showhandle=True,
            handlesize=12,
            handlepad=40)
        rv.grid(row=0, column=0, sticky="nsew")

        def rp(title):
            outer, body = self._panel(rv, title)
            rv.add(outer, minsize=60, sticky="nsew")
            return body

        self.recommendation_body = rp("DECISION ENGINE")
        self.quality_body        = rp("DATA QUALITY")
        sbody_outer, sbody = self._panel(rv, "WATCHLIST")
        rv.add(sbody_outer, minsize=50, sticky="nsew")
        self.sidebar_watch_body  = sbody
        self.chat_preview_body   = rp("CHAT PREVIEW")
        self.source_body         = rp("SOURCE MONITOR")
        self.accuracy_body       = rp("ACCURACY DASHBOARD")

        # Set right panel initial sash positions after draw
        self.root.after(300, lambda: self._set_right_sashes(rv))
        self._rv_pane = rv

    # ──────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────

    def _panel(self, p, title):
        outer = tk.Frame(p, bg=BG,
            highlightbackground=BORDER, highlightthickness=1)
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(1, weight=1)

        # Header row with title + maximize button
        hdr = tk.Frame(outer, bg=BG)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)
        tk.Label(hdr, text=title, bg=BG, fg=CYAN,
            font=FB, anchor="w", padx=6, pady=4).grid(row=0, column=0, sticky="ew")
        # Maximize button — calls panel overlay system
        tk.Button(hdr, text="⛶", bg=BG, fg=MUTED,
            activebackground="#1e293b", activeforeground=CYAN,
            relief="flat", font=("Segoe UI",9), padx=4, pady=2,
            command=lambda t=title: self._maximize_panel(outer, t)
        ).grid(row=0, column=1, sticky="e", padx=4)

        body = tk.Frame(outer, bg=PANEL)
        body.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0,4))
        return outer, body

    def _maximize_panel(self, panel_frame, title):
        """
        Maximize a panel into an overlay covering the whole app.
        Clicking the button again restores the panel.
        """
        if hasattr(self, "_maximized_overlay") and self._maximized_overlay:
            # Already maximized — restore
            self._restore_panel()
            return

        # Create full-screen overlay on top of screen container
        overlay = tk.Frame(self._screen_container, bg=BG,
            highlightbackground=CYAN_DARK, highlightthickness=2)
        overlay.grid(row=0, column=0, sticky="nsew")
        overlay.grid_rowconfigure(1, weight=1)
        overlay.grid_columnconfigure(0, weight=1)
        overlay.lift()

        # Header with title + restore button
        ohdr = tk.Frame(overlay, bg=TOP)
        ohdr.grid(row=0, column=0, sticky="ew")
        ohdr.grid_columnconfigure(0, weight=1)
        tk.Label(ohdr, text=f"MAXIMIZED: {title}", bg=TOP, fg=CYAN,
            font=FB, padx=10, pady=6).grid(row=0, column=0, sticky="w")
        tk.Button(ohdr, text="⊡ Restore",
            bg="#334155", fg=TEXT, activebackground="#475569",
            relief="flat", font=FB, padx=12, pady=5,
            command=self._restore_panel).grid(row=0, column=1, sticky="e", padx=8)

        # Clone content into overlay using a new frame for the body
        body = tk.Frame(overlay, bg=PANEL)
        body.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)

        # Build expanded content based on title
        self._build_maximized_content(body, title)

        self._maximized_overlay = overlay

    def _restore_panel(self):
        """Remove the maximized overlay and return to normal layout."""
        if hasattr(self, "_maximized_overlay") and self._maximized_overlay:
            try:
                self._maximized_overlay.destroy()
            except Exception:
                pass
            self._maximized_overlay = None

    def _build_maximized_content(self, p, title):
        """
        Build richer expanded content when a panel is maximized.
        Falls back to a helpful message if no special view exists.
        """
        m = self.current_match
        if "DECISION" in title:
            self._render_decision_engine()
            home = m.get("home","")
            away = m.get("away","")
            tk.Label(p,
                text=(f"Decision Engine expanded for {home} vs {away}."
                      " All signal detail shown above."),
                bg=PANEL, fg=MUTED, font=FS, justify="left",
                padx=12, pady=20).pack(fill="x")
        elif "MATCH" in title.upper() or "MATCHES" in title.upper():
            # Expanded match list with more columns
            tk.Label(p, text="EXPANDED MATCH LIST — More columns visible",
                bg=PANEL, fg=CYAN, font=FB, anchor="w", padx=8, pady=4).pack(fill="x")
            self.render_matches()
        else:
            tk.Label(p,
                text=(f"Expanded view: {title}\n"
                      "This panel is now maximized.\n"
                      "All content from the normal view is shown.\n"
                      "Click Restore to return to the normal layout."),
                bg=PANEL, fg=MUTED, font=FS, justify="left",
                padx=16, pady=30).pack(fill="both", expand=True)

    def _btn(self, p, text, bg, cmd, width=None, pady=5):
        return tk.Button(p, text=text, bg=bg, fg=TEXT,
            activebackground=bg, activeforeground=TEXT,
            relief="flat", font=FB, padx=8, pady=pady,
            width=width, command=cmd)

    def _lbl(self, p, text, fg=None, font=None, **kw):
        return tk.Label(p, text=text, bg=PANEL_DARK,
            fg=fg or TEXT, font=font or FS, **kw)

    def _card(self, p):
        c = tk.Frame(p, bg=PANEL_DARK,
            highlightbackground=BORDER, highlightthickness=1)
        c.pack(fill="x", pady=3)
        return c

    def _sec(self, p, text):
        tk.Label(p, text=text, bg=PANEL, fg=CYAN,
            font=FB, anchor="w", pady=4).pack(fill="x")

    def _clear(self, p):
        for w in p.winfo_children():
            w.destroy()

    def _initials(self, name):
        w = [x for x in str(name).replace("-"," ").split() if x]
        if not w:    return "FC"
        if len(w)==1: return w[0][:3].upper()
        return "".join(x[0] for x in w[:3]).upper()

    def _mousewheel(self, e):
        w = self.root.focus_get()
        if w and str(w).startswith(str(self.matches_canvas)):
            self.matches_canvas.yview_scroll(int(-1*(e.delta/120)), "units")

    def _tab_body(self):
        c = tk.Canvas(self.tab_content, bg=PANEL, highlightthickness=0)
        sb = tk.Scrollbar(self.tab_content, orient="vertical", command=c.yview)
        c.configure(yscrollcommand=sb.set)
        c.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        body = tk.Frame(c, bg=PANEL)
        wid  = c.create_window((0,0), window=body, anchor="nw")
        body.bind("<Configure>", lambda _e: c.configure(scrollregion=c.bbox("all")))
        c.bind("<Configure>",    lambda e:  c.itemconfigure(wid, width=e.width))
        return body

    def _stat_bar(self, p, label, home, away):
        row = tk.Frame(p, bg=PANEL)
        row.pack(fill="x", pady=3)
        top = tk.Frame(row, bg=PANEL)
        top.pack(fill="x")
        tk.Label(top, text=str(home), bg=PANEL, fg=TEXT, font=FB, width=7, anchor="w").pack(side="left")
        tk.Label(top, text=label,     bg=PANEL, fg=MUTED, font=FS).pack(side="left", fill="x", expand=True)
        tk.Label(top, text=str(away), bg=PANEL, fg=TEXT, font=FB, width=7, anchor="e").pack(side="right")
        bar = tk.Frame(row, bg="#263244", height=7)
        bar.pack(fill="x", pady=(1,0))
        total = max(float(home)+float(away), 1.0)
        lw = max(int(float(home)/total*100), 1)
        bar.grid_columnconfigure(0, weight=lw)
        bar.grid_columnconfigure(1, weight=max(100-lw,1))
        tk.Frame(bar, bg="#38bdf8", height=7).grid(row=0, column=0, sticky="ew")
        tk.Frame(bar, bg=ORANGE,    height=7).grid(row=0, column=1, sticky="ew")

    def _summary_row(self, p, summaries):
        card = tk.Frame(p, bg=PANEL_DARK,
            highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", pady=(0,6))
        row = tk.Frame(card, bg=PANEL_DARK)
        row.pack(fill="x", padx=8, pady=6)
        for label, hp, ap in summaries:
            box = tk.Frame(row, bg="#243244")
            box.pack(side="left", expand=True, fill="x", padx=2)
            tk.Label(box, text=label,          bg="#243244", fg=MUTED, font=FS).pack(pady=(5,1))
            tk.Label(box, text=f"{hp}% / {ap}%",bg="#243244",fg=TEXT, font=FB).pack(pady=(0,1))
            strip = tk.Frame(box, bg="#1a2435", height=5)
            strip.pack(fill="x", padx=8, pady=(1,6))
            lw = max(1, int(hp)); rw = max(1, int(ap))
            strip.grid_columnconfigure(0, weight=lw)
            strip.grid_columnconfigure(1, weight=rw)
            tk.Frame(strip, bg=CYAN,   height=5).grid(row=0, column=0, sticky="ew")
            tk.Frame(strip, bg=ORANGE, height=5).grid(row=0, column=1, sticky="ew")
        return card

    # ──────────────────────────────────────────
    # Match list rendering  (FAST)
    # ──────────────────────────────────────────

    def filtered_matches(self):
        country = self.filters["country"].get()
        league  = self.filters["league"].get()
        tourn   = self.filters["tournament"].get()
        date_f  = self.filters["date"].get()
        result  = []
        for m in MATCHES:
            if country != "All" and m.get("country","") != country: continue
            if league  != "All" and m.get("league","")  != league:  continue
            if tourn   != "All" and m.get("tournament","") != tourn: continue
            st = m.get("status","")
            if date_f == "Live"     and st not in ("LIVE","1H","2H","HT","ET","P"): continue
            if date_f == "Upcoming" and st in ("LIVE","1H","2H","HT","ET","P"):     continue
            result.append(m)
        return result

    def render_matches(self):
        """
        Smooth match list update — never destroys all rows at once.

        Strategy:
        - On first call (or filter change): full rebuild is unavoidable.
        - On live data updates: only rebuild rows whose data changed.
        - Tracks rows by match_id in self._match_row_cache.
        - Preserves scroll position throughout.
        """
        matches = self.filtered_matches()
        src     = "live API" if self.live_api_active else "local mock"
        live_n  = sum(1 for m in matches if m.get("status") == "LIVE")
        self.status_label.config(
            text=f"Last Load: {src}  |  Matches: {len(matches)}  |  Live: {live_n}")

        # Build a fast lookup: id → match
        new_by_id = {m["id"]: m for m in matches}

        # Decide whether we need a full rebuild:
        # - First render (cache empty)
        # - Filter changed (different set of IDs)
        # - League grouping changed (different leagues visible)
        old_ids     = set(self._match_row_cache.keys())
        new_ids     = set(new_by_id.keys())
        need_rebuild = (old_ids != new_ids)

        if need_rebuild:
            # Full rebuild — only done when structure changes
            self._full_render_matches(matches)
        else:
            # Smooth in-place update — only update changed rows
            self._update_match_rows(new_by_id)

        # Update canvas scroll region
        self.matches_frame.update_idletasks()
        self.matches_canvas.configure(
            scrollregion=self.matches_canvas.bbox("all"))

    def _full_render_matches(self, matches):
        """Full rebuild of match list. Preserves scroll position."""
        # Save scroll position
        try:
            scroll_pos = self.matches_canvas.yview()[0]
        except Exception:
            scroll_pos = 0.0

        self._clear(self.matches_frame)
        self._match_row_cache.clear()

        if not matches:
            tk.Label(self.matches_frame,
                text="No matches for selected filters.",
                bg=PANEL_DARK, fg=MUTED, font=FM, pady=12).pack(fill="x")
            return

        grouped = {}
        for m in matches:
            grouped.setdefault(m.get("league", "?"), []).append(m)

        for league, ms in grouped.items():
            tk.Label(self.matches_frame,
                text=f"─── {league.upper()} ───",
                bg="#111827", fg=MUTED, font=FM, pady=2,
                anchor="w", padx=4).pack(fill="x", pady=(3, 1))
            for m in ms:
                row_frame = self._match_row(m)
                # Cache the row frame and last-seen data snapshot
                self._match_row_cache[m["id"]] = {
                    "frame":      row_frame,
                    "status":     m.get("status", ""),
                    "minute":     m.get("minute", 0),
                    "home_score": m.get("home_score", 0),
                    "away_score": m.get("away_score", 0),
                    "edge":       m.get("edge", 0.0),
                }

        # Restore scroll position
        try:
            self.matches_frame.update_idletasks()
            self.matches_canvas.yview_moveto(scroll_pos)
        except Exception:
            pass

    def _update_match_rows(self, new_by_id: dict):
        """
        In-place update of existing rows.
        Only rebuilds a row's labels when its data changed.
        No flicker — unchanged rows are untouched.
        """
        for mid, m in new_by_id.items():
            cached = self._match_row_cache.get(mid)
            if not cached:
                continue

            # Check what changed
            changed = (
                cached.get("status")     != m.get("status", "") or
                cached.get("minute")     != m.get("minute", 0) or
                cached.get("home_score") != m.get("home_score", 0) or
                cached.get("away_score") != m.get("away_score", 0) or
                cached.get("edge")       != m.get("edge", 0.0)
            )

            if not changed:
                continue

            # Rebuild only this row's frame in-place
            frame = cached.get("frame")
            if frame and frame.winfo_exists():
                for widget in frame.winfo_children():
                    widget.destroy()
                self._populate_match_row(frame, m)
                # Brief highlight flash on changed row
                self._flash_row(frame, m)

            # Update cache
            self._match_row_cache[mid].update({
                "status":     m.get("status", ""),
                "minute":     m.get("minute", 0),
                "home_score": m.get("home_score", 0),
                "away_score": m.get("away_score", 0),
                "edge":       m.get("edge", 0.0),
            })

    def _flash_row(self, frame, m):
        """Subtle 400ms highlight on a changed row. No heavy animation."""
        try:
            orig_bg = "#1f2937" if (
                self.current_match and m["id"] == self.current_match["id"]
            ) else ROW
            flash_bg = "#1a3a4a"   # very subtle teal tint
            frame.configure(bg=flash_bg)
            for w in frame.winfo_children():
                try:
                    w.configure(bg=flash_bg)
                except Exception:
                    pass
            self.root.after(420, lambda: self._unflash_row(frame, orig_bg))
        except Exception:
            pass

    def _unflash_row(self, frame, orig_bg):
        """Restore row background after flash."""
        try:
            if not frame.winfo_exists():
                return
            frame.configure(bg=orig_bg)
            for w in frame.winfo_children():
                try:
                    w.configure(bg=orig_bg)
                except Exception:
                    pass
        except Exception:
            pass

    def _trunc(self, name: str, maxlen: int) -> str:
        """Truncate from the END with ellipsis — never from the front."""
        if len(name) <= maxlen:
            return name
        return name[:maxlen - 1] + "…"

    def _match_row(self, m, parent=None) -> tk.Frame:
        """Create a new match row frame, populate it, and return it."""
        container = parent if parent is not None else self.matches_frame
        selected  = self.current_match and m["id"] == self.current_match["id"]
        bg        = "#1f2937" if selected else ROW
        row       = tk.Frame(container, bg=bg)
        row.pack(fill="x", padx=2, pady=1)
        self._populate_match_row(row, m)
        return row

    def _populate_match_row(self, row: tk.Frame, m):
        """Fill (or refill) all labels/buttons inside a match row frame."""
        selected = self.current_match and m["id"] == self.current_match["id"]
        bg = "#1f2937" if selected else ROW

        # Column weights: team name columns stretch, others fixed
        for col_i, weight in enumerate([0, 0, 1, 0, 1, 0, 0, 0]):
            row.grid_columnconfigure(col_i, weight=weight)

        st    = m.get("status", "")
        sc    = GREEN if st == "LIVE" else YELLOW
        ec    = GREEN if m.get("edge", 0) >= 0 else RED
        score = f"{m.get('home_score',0)}-{m.get('away_score',0)}"
        odds  = m.get("odds", (2.0, 3.5, 4.0))
        star  = "★" if m["id"] in self.watchlist_ids else "☆"
        # Truncate from the END — team names never get front-clipped
        home  = self._trunc(m.get("home", ""), 14)
        away  = self._trunc(m.get("away", ""), 14)
        min_  = str(m.get("minute", "")) if m.get("minute") else "--"

        # (text, min_width_chars, fg_color, anchor, col_index)
        cols = [
            (st[:4],                         5,  sc,        "w", 0),
            (min_,                           4,  "#60a5fa",  "c", 1),
            (home,                           13, TEXT,       "w", 2),
            (score,                          5,  ORANGE,     "c", 3),
            (away,                           13, TEXT,       "w", 4),
            (f"{m.get('edge', 0):+.1f}",     6,  ec,        "c", 5),
            (f"{odds[0]:.1f}/{odds[2]:.1f}", 9,  MUTED,     "c", 6),
        ]
        for txt, w, c, a, ci in cols:
            lb = tk.Label(row, text=txt, bg=bg, fg=c,
                font=FM, width=w, anchor=a)
            lb.grid(row=0, column=ci, sticky="ew", padx=1, pady=3)
            lb.bind("<Button-1>", lambda _e, item=m: self.select_match(item))

        tk.Button(row, text=star, bg=bg,
            fg=YELLOW if m["id"] in self.watchlist_ids else MUTED,
            activebackground=bg, relief="flat", width=2,
            font=("Segoe UI Symbol", 10),
            command=lambda item=m: self._toggle_watchlist(item)
        ).grid(row=0, column=7, padx=(1, 3))
        row.bind("<Button-1>", lambda _e, item=m: self.select_match(item))

    def render_watchlist(self):
        self._clear(self.watchlist_frame)
        items = [m for m in MATCHES if m["id"] in self.watchlist_ids]
        if not items:
            tk.Label(self.watchlist_frame,
                text="No matches. Click ☆ to add.",
                bg=PANEL_DARK, fg=MUTED, font=FM, pady=6).pack(fill="x", padx=4)
            return
        for m in items:
            self._match_row(m, parent=self.watchlist_frame)
        self.watchlist_canvas.configure(scrollregion=self.watchlist_canvas.bbox("all"))

    def _toggle_watchlist(self, m):
        if m["id"] in self.watchlist_ids:
            self.watchlist_ids.remove(m["id"])
        else:
            self.watchlist_ids.add(m["id"])
        self.render_matches()
        self.render_watchlist()
        self._render_sidebar_watchlist()

    # ──────────────────────────────────────────
    # Match selection
    # ──────────────────────────────────────────

    def select_match(self, match, refresh=True):
        self._stop_replay(reset=False)
        self.current_match = match
        if self._match_finished(match):
            self._settle_challenges(match)
        self.selected_odds_book = None
        self.selected_prediction_source = None
        self.selected_player_detail = None
        self.replay_minute = self._ref_minute(match)

        sl = self.score_labels
        sl["home_badge"].config(text=self._initials(match.get("home","")))
        sl["away_badge"].config(text=self._initials(match.get("away","")))
        sl["home"].config(text=match.get("home",""))
        sl["away"].config(text=match.get("away",""))
        sl["home_score"].config(text=str(match.get("home_score",0)))
        sl["away_score"].config(text=str(match.get("away_score",0)))
        sl["minute"].config(text=f"{match.get('minute',0):02d}'")
        st = match.get("status","UP")
        sl["status"].config(text=st, fg=GREEN if st=="LIVE" else YELLOW)
        edge = match.get("edge",0.0)
        sl["edge"].config(text=f"{edge:+.1f}", fg=GREEN if edge>=0 else RED)
        sl["home_form"].config(text="Form: "+"-".join(match.get("home_form",["?","?","?","?","?"])))
        sl["away_form"].config(text="Form: "+"-".join(match.get("away_form",["?","?","?","?","?"])))
        sl["home_goals"].config(text=f"Goals: {match.get('home_avg',0)}/game")
        sl["away_goals"].config(text=f"Goals: {match.get('away_avg',0)}/game")
        self.meta_labels["date"].config(   text=match.get("date",""))
        self.meta_labels["venue"].config(  text=match.get("venue",""))
        self.meta_labels["referee"].config(text=match.get("referee",""))

        self._update_replay_header()
        self._render_tab()
        self._render_right_panel()
        self._render_markets()
        if refresh:
            self.render_matches()

        if match.get("fixture_id") and match.get("home_id") and self.live_api_active:
            threading.Thread(target=self._run_live_analysis,
                args=(match,), daemon=True).start()

    # ──────────────────────────────────────────
    # Right panel  (lazy — only when visible)
    # ──────────────────────────────────────────

    def _render_right_panel(self):
        self._render_decision_engine()
        self._render_data_quality()
        self._render_source_monitor()
        self._render_chat_preview()
        self._render_sidebar_watchlist()
        self._render_accuracy()

    def _render_decision_engine(self):
        self._clear(self.recommendation_body)
        snap = self._snapshot(self.current_match)
        p    = self.recommendation_body

        top = self._card(p)
        tk.Label(top, text=snap["decision"], bg=PANEL_DARK,
            fg=snap["decision_color"], font=("Segoe UI",14,"bold"), anchor="w"
        ).pack(fill="x", padx=8, pady=(6,1))
        tk.Label(top, text=snap["market"], bg=PANEL_DARK, fg=TEXT,
            font=FB, anchor="w").pack(fill="x", padx=8)
        tk.Label(top,
            text=f"Confidence {snap['confidence']}%  |  Edge {snap['edge']:+.1f}  |  Quality {snap['data_quality']}%",
            bg=PANEL_DARK, fg=MUTED, font=FS, anchor="w").pack(fill="x", padx=8, pady=(0,6))

        bands = tk.Frame(top, bg=PANEL_DARK)
        bands.pack(fill="x", padx=8, pady=(0,8))
        for lbl, val, col in [
            ("True Prob",      f"{snap['true_prob']}%",   CYAN),
            ("Market Implied", f"{snap['market_prob']}%", ORANGE),
            ("Discrepancy",    f"{snap['edge']:+.1f}",    snap["decision_color"]),
        ]:
            box = tk.Frame(bands, bg="#243244")
            box.pack(side="left", expand=True, fill="x", padx=2)
            tk.Label(box, text=lbl, bg="#243244", fg=MUTED, font=FS).pack(pady=(5,1))
            tk.Label(box, text=val, bg="#243244", fg=col,  font=FB).pack(pady=(0,5))

        self._sec(p, "WHY IT LIKES IT")
        c = self._card(p)
        for r in snap["reasons_for"]:
            tk.Label(c, text=f"+ {r}", bg=PANEL_DARK, fg=GREEN,
                font=FS, anchor="w", justify="left", wraplength=260
            ).pack(fill="x", padx=8, pady=1)

        self._sec(p, "WHY IT CAN FAIL")
        c2 = self._card(p)
        for r in snap["reasons_against"]:
            tk.Label(c2, text=f"- {r}", bg=PANEL_DARK, fg=RED,
                font=FS, anchor="w", justify="left", wraplength=260
            ).pack(fill="x", padx=8, pady=1)

    def _render_data_quality(self):
        self._clear(self.quality_body)
        snap = self._snapshot(self.current_match)
        p    = self.quality_body

        row = tk.Frame(p, bg=PANEL)
        row.pack(fill="x", padx=4, pady=4)
        for lbl, val, col in [
            ("Freshness", snap["freshness"],   CYAN),
            ("Lineups",   snap["lineups"],     snap["lineup_color"]),
            ("Weather",   snap["weather"],     ORANGE),
            ("News",      snap["news_status"], TEXT),
        ]:
            box = tk.Frame(row, bg="#243244")
            box.pack(side="left", expand=True, fill="x", padx=2)
            tk.Label(box, text=lbl, bg="#243244", fg=MUTED, font=FS).pack(pady=(4,1))
            tk.Label(box, text=val, bg="#243244", fg=col,  font=FB).pack(pady=(0,4))

        self._sec(p, "DATA BUCKETS")
        c = self._card(p)
        for lbl, val in snap["data_buckets"]:
            line = tk.Frame(c, bg=PANEL_DARK)
            line.pack(fill="x", padx=6, pady=1)
            tk.Label(line, text=lbl, bg=PANEL_DARK, fg=CYAN,
                font=FS, width=13, anchor="w").pack(side="left")
            tk.Label(line, text=val, bg=PANEL_DARK, fg=TEXT,
                font=FS, anchor="w").pack(side="left")

    def _render_source_monitor(self):
        self._clear(self.source_body)
        snap = self._snapshot(self.current_match)
        p    = self.source_body

        hdr = tk.Frame(p, bg=PANEL_DARK)
        hdr.pack(fill="x", padx=4, pady=(4,1))
        for txt, w in [("SOURCE",13),("TYPE",9),("STATE",11),("WEIGHT",7)]:
            tk.Label(hdr, text=txt, bg=PANEL_DARK, fg=ORANGE,
                font=FM, width=w, anchor="w").pack(side="left")

        for src, kind, state, weight in snap["sources"]:
            row = tk.Frame(p, bg=ROW)
            row.pack(fill="x", padx=4, pady=1)
            sc = GREEN if state in ("Confirmed","Live","Fresh") else YELLOW if state in ("Partial","Checking") else RED
            for txt, w, c in [(src,13,TEXT),(kind,9,MUTED),(state,11,sc),(weight,7,CYAN)]:
                tk.Label(row, text=txt, bg=ROW, fg=c,
                    font=FM, width=w, anchor="w").pack(side="left", pady=3)

    def _render_chat_preview(self):
        self._clear(self.chat_preview_body)
        m      = self.current_match
        room   = self._active_room(m)
        thread = self._chat_thread(m)
        p      = self.chat_preview_body

        hdr = tk.Frame(p, bg=PANEL_DARK)
        hdr.pack(fill="x", padx=6, pady=(6,4))
        tk.Label(hdr, text=f"{m.get('home','')} vs {m.get('away','')}",
            bg=PANEL_DARK, fg=TEXT, font=FB, anchor="w").pack(fill="x")
        tk.Label(hdr, text=room, bg=PANEL_DARK, fg=CYAN, font=FS, anchor="w").pack(fill="x")

        for item in thread[-3:]:
            row = tk.Frame(p, bg=PANEL_DARK)
            row.pack(fill="x", padx=6, pady=2)
            col = ORANGE if item["tag"]=="agent" else GREEN if item["tag"]=="you" else CYAN
            tk.Label(row, text=item["author"], bg=PANEL_DARK, fg=col,
                font=FS, width=10, anchor="w").pack(side="left")
            tk.Label(row,
                text=item["text"][:50]+("…" if len(item["text"])>50 else ""),
                bg=PANEL_DARK, fg=MUTED, font=FS, anchor="w"
            ).pack(side="left", fill="x", expand=True)

    def _render_sidebar_watchlist(self):
        self._clear(self.sidebar_watch_body)
        items = [m for m in MATCHES if m["id"] in self.watchlist_ids]
        msg = "No matches in watchlist." if not items else \
              "\n".join(f"{m.get('home','')} vs {m.get('away','')}" for m in items[:4])
        tk.Label(self.sidebar_watch_body, text=msg, bg=PANEL_DARK, fg=MUTED,
            font=FM, anchor="w", justify="left", padx=8, pady=8).pack(fill="both", expand=True)

    def _render_accuracy(self):
        self._clear(self.accuracy_body)
        p = self.accuracy_body
        try:
            s = summarize_accuracy()
            rows = [
                ("Settled", s.get("total_settled",0)),
                ("Rec hit %", s.get("recommended_hit_rate",0.0)),
                ("Draw hit %", s.get("draw_hit_rate",0.0)),
                ("Under hit %", s.get("under_hit_rate",0.0)),
            ]
        except Exception:
            rows = [("Settled",0),("Rec hit %",0),("Draw hit %",0),("Under hit %",0)]

        tk.Label(p, text="ACCURACY SUMMARY", bg=PANEL, fg=ORANGE,
            font=FM, anchor="w").pack(fill="x", padx=6, pady=(6,2))
        for lbl, val in rows:
            row = tk.Frame(p, bg=PANEL)
            row.pack(fill="x", padx=6, pady=1)
            tk.Label(row, text=f"{lbl}:", bg=PANEL, fg=MUTED,
                font=FM, width=20, anchor="w").pack(side="left")
            tk.Label(row, text=str(val), bg=PANEL, fg=GREEN,
                font=FM, anchor="e").pack(side="right")

    # ──────────────────────────────────────────
    # Tabs
    # ──────────────────────────────────────────

    def set_tab(self, name):
        if name != "Stats Replay":
            self._pause_replay()
        self.tab_name.set(name)
        self._redraw_tabs()
        self._render_tab()
        self._update_replay_header()

    def _render_tab(self):
        self._clear(self.tab_content)
        m    = self.current_match
        body = self._tab_body()
        t    = self.tab_name.get()
        if   t == "Overview":     self._tab_overview(body, m)
        elif t == "Stats Replay": self._tab_stats(body, m)
        elif t == "Attack":       self._tab_attack(body, m)
        elif t == "Control":      self._tab_control(body, m)
        elif t == "Defense":      self._tab_defense(body, m)
        elif t == "Line-ups":     self._tab_lineups(body, m)
        elif t == "News":         self._tab_news(body, m)
        elif t == "Weather":      self._tab_weather(body, m)
        elif t == "Form":         self._tab_form(body, m)
        elif t == "Players":      self._tab_players(body, m)
        elif t == "Video":        self._tab_video(body, m)
        elif t == "Trivia":       self._tab_trivia(body, m)
        elif t == "Chat":         self._tab_chat(body, m)
        elif t == "Table":        self._tab_table(body, m)
        elif t == "H2H":          self._tab_h2h(body, m)

    def _tab_overview(self, p, m):
        minute = self._cur_minute(m)
        maxm   = self._max_minute(m)
        self._sec(p, "MATCH OVERVIEW")
        tk.Label(p, text=f"Viewing replay at {minute:02d}' of {maxm}'",
            bg=PANEL, fg=MUTED, font=FS, anchor="w").pack(fill="x", pady=(0,4))
        self._summary_row(p, self._stats_summary(m, minute, maxm))
        self._sec(p, "MATCH DETAILS")
        d = self._card(p)
        for lbl, val in [
            ("Competition", m.get("tournament","")),
            ("Status",      m.get("status","")),
            ("Venue",       m.get("venue","")),
            ("Minute",      f"{minute:02d}'" if minute else "Pre-match"),
            ("Referee",     m.get("referee","")),
        ]:
            row = tk.Frame(d, bg=PANEL_DARK)
            row.pack(fill="x", padx=10, pady=3)
            tk.Label(row, text=lbl, bg=PANEL_DARK, fg=MUTED,  font=FS, width=14, anchor="w").pack(side="left")
            tk.Label(row, text=val, bg=PANEL_DARK, fg=TEXT,   font=FB, anchor="w").pack(side="left")
        self._sec(p, "KEY STATS")
        c = self._card(p)
        c.pack(fill="x", pady=(0,4))
        for lbl, h, a in self._stats_at(m, minute, maxm)[:6]:
            self._stat_bar(c, lbl, h, a)

    def _tab_stats(self, p, m):
        maxm = self._max_minute(m)
        self._sec(p, "MATCH STATS TIMELINE")
        summ = self._summary_row(p, self._stats_summary(m, maxm))
        slbls = {}
        for box in summ.winfo_children()[0].winfo_children():
            lbls = [c for c in box.winfo_children() if isinstance(c, tk.Label)]
            if len(lbls) >= 2:
                slbls[lbls[0].cget("text")] = lbls[1]

        sc = self._card(p)
        sc.pack(fill="x", pady=(0,6))
        top = tk.Frame(sc, bg=PANEL_DARK)
        top.pack(fill="x", padx=8, pady=(6,2))
        tk.Label(top, text="MATCH REPLAY", bg=PANEL_DARK, fg=CYAN,
            font=FB, anchor="w").pack(side="left")
        ml = tk.Label(top, text="", bg=PANEL_DARK, fg=ORANGE, font=FB, anchor="e")
        ml.pack(side="right")

        sw = tk.Frame(sc, bg=PANEL_DARK)
        sw.pack(fill="x", padx=8, pady=(0,6))
        tk.Label(sw, text="0'", bg=PANEL_DARK, fg=MUTED, font=FS).pack(side="left")
        slider = tk.Scale(sw, from_=0, to=maxm, orient="horizontal",
            showvalue=False, resolution=1, bg=PANEL_DARK, fg=TEXT,
            troughcolor="#243244", highlightthickness=0, activebackground=ORANGE)
        slider.pack(side="left", fill="x", expand=True, padx=6)
        tk.Label(sw, text=f"{maxm}'", bg=PANEL_DARK, fg=MUTED, font=FS).pack(side="right")
        tk.Label(sc,
            text="Slide to replay how stats changed minute by minute.",
            bg=PANEL_DARK, fg=MUTED, font=FS, anchor="w").pack(fill="x", padx=8, pady=(0,4))

        mkr = tk.Canvas(sc, bg=PANEL_DARK, height=24, highlightthickness=0)
        mkr.pack(fill="x", padx=8, pady=(0,6))

        ctrl = tk.Frame(sc, bg=PANEL_DARK)
        ctrl.pack(fill="x", padx=8, pady=(0,6))
        self._btn(ctrl,"Play", CYAN_DARK, self._play_replay,  width=8,pady=5).pack(side="left",padx=(0,4))
        self._btn(ctrl,"Pause",GRAY_BTN,  self._pause_replay, width=8,pady=5).pack(side="left",padx=(0,4))
        self._btn(ctrl,"Stop", RED_DARK,  self._stop_replay,  width=8,pady=5).pack(side="left")

        sf = tk.Frame(p, bg=PANEL)
        sf.pack(fill="x")
        ef = self._card(p)
        ef.pack(fill="x", pady=(6,3))

        def refresh(val):
            mn = int(float(val))
            self.replay_minute = mn
            ml.config(text=f"{mn:02d}'")
            for lbl, hp, ap in self._stats_summary(m, mn, maxm):
                if lbl in slbls:
                    slbls[lbl].config(text=f"{hp}% / {ap}%")
            self._clear(sf)
            for lbl, h, a in self._stats_at(m, mn, maxm):
                self._stat_bar(sf, lbl, h, a)
            self._render_replay_events(ef, m, mn, maxm)

        slider.configure(command=refresh)
        self._draw_markers(mkr, m, maxm)
        mkr.bind("<Configure>", lambda _e: self._draw_markers(mkr, m, maxm))
        self.replay_slider  = slider
        self.replay_refresh = refresh
        self.replay_max_minute = maxm
        slider.set(self._cur_minute(m))
        refresh(slider.get())

    def _tab_attack(self, p, m):
        mn = self._cur_minute(m); mx = self._max_minute(m)
        self._sec(p, "ATTACK PROFILE")
        tk.Label(p, text=f"Replay at {mn:02d}' of {mx}'",
            bg=PANEL, fg=MUTED, font=FS, anchor="w").pack(fill="x", pady=(0,4))
        self._summary_row(p, self._attack_summary(m, mn, mx))
        self._sec(p, "ATTACKING STATS")
        c = self._card(p); c.pack(fill="x", pady=(0,4))
        for lbl, h, a in self._attack_stats(m, mn, mx):
            self._stat_bar(c, lbl, h, a)

    def _tab_control(self, p, m):
        mn = self._cur_minute(m); mx = self._max_minute(m)
        self._sec(p, "CONTROL & TERRITORY")
        self._summary_row(p, self._control_summary(m, mn, mx))
        self._sec(p, "CONTROL STATS")
        c = self._card(p); c.pack(fill="x", pady=(0,4))
        for lbl, h, a in self._control_stats(m, mn, mx):
            self._stat_bar(c, lbl, h, a)

    def _tab_defense(self, p, m):
        mn = self._cur_minute(m); mx = self._max_minute(m)
        self._sec(p, "DEFENSE & DISCIPLINE")
        self._summary_row(p, self._defense_summary(m, mn, mx))
        self._sec(p, "DEFENSIVE STATS")
        c = self._card(p); c.pack(fill="x", pady=(0,4))
        for lbl, h, a in self._defense_stats(m, mn, mx):
            self._stat_bar(c, lbl, h, a)

    def _tab_lineups(self, p, m):
        mn = self._cur_minute(m); mx = self._max_minute(m)
        self._sec(p, "LINE-UPS & SHAPE")
        tk.Label(p, text=f"Replay at {mn:02d}'",
            bg=PANEL, fg=MUTED, font=FS, anchor="w").pack(fill="x", pady=(0,4))
        summ = self._card(p)
        sr = tk.Frame(summ, bg=PANEL_DARK)
        sr.pack(fill="x", padx=8, pady=6)
        for lbl, val in [
            (m.get("home",""), self._lineup_formation(m,"home",mn)),
            ("Replay", f"{mn:02d}'"),
            (m.get("away",""), self._lineup_formation(m,"away",mn)),
        ]:
            box = tk.Frame(sr, bg="#243244")
            box.pack(side="left", expand=True, fill="x", padx=2)
            tk.Label(box, text=lbl, bg="#243244", fg=MUTED, font=FS).pack(pady=(4,1))
            tk.Label(box, text=val, bg="#243244", fg=TEXT, font=FB).pack(pady=(0,4))
        pc = self._card(p)
        pitch = tk.Canvas(pc, bg="#56761b", height=480, highlightthickness=0)
        pitch.pack(fill="both", expand=True, padx=6, pady=6)
        self._draw_pitch(pitch, m, mn)

    def _tab_chat(self, p, m):
        self._sec(p, "MATCH CHAT")
        mn = self._cur_minute(m)
        rm = self._active_room(m)

        rooms_f = tk.Frame(p, bg=PANEL)
        rooms_f.pack(fill="x", pady=(0,4))
        for r in ["Open Room","Value Talk","Live Pulse","Post-match"]:
            active = r == rm
            count  = len(self._chat_thread_room(m, r))
            tk.Button(rooms_f, text=f"{r} {count}",
                bg=TEXT if active else PANEL_DARK,
                fg=BG  if active else MUTED,
                relief="flat", font=FB, padx=10, pady=4,
                command=lambda rn=r: self._set_room(m, rn)).pack(side="left", padx=(0,4))

        feed = self._card(p)
        feed.pack(fill="both", expand=True, pady=(0,4))
        fc = tk.Canvas(feed, bg=PANEL_DARK, height=300, highlightthickness=0)
        fsc= tk.Scrollbar(feed, orient="vertical", command=fc.yview)
        fc.configure(yscrollcommand=fsc.set)
        fc.pack(side="left", fill="both", expand=True, padx=(6,0), pady=6)
        fsc.pack(side="right", fill="y", pady=6, padx=(0,6))
        fb = tk.Frame(fc, bg=PANEL_DARK)
        wid = fc.create_window((0,0), window=fb, anchor="nw")
        fb.bind("<Configure>", lambda _e: fc.configure(scrollregion=fc.bbox("all")))
        fc.bind("<Configure>", lambda e: fc.itemconfigure(wid, width=e.width))
        for item in self._chat_thread(m):
            self._chat_bubble(fb, item)

        comp = self._card(p)
        comp.pack(fill="x", pady=(0,4))
        row = tk.Frame(comp, bg=PANEL_DARK)
        row.pack(fill="x", padx=8, pady=8)
        e = tk.Entry(row, textvariable=self.chat_message,
            bg=PANEL_DARK, fg=TEXT, insertbackground=TEXT, relief="flat", font=FS)
        e.pack(side="left", fill="x", expand=True, padx=(0,6), ipady=5)
        e.bind("<Return>", lambda _e, mc=m: self._post_chat(mc))
        self._btn(row,"Post",CYAN_DARK,lambda mc=m: self._post_chat(mc),width=8,pady=5).pack(side="left")

    def _tab_table(self, p, m):
        self._sec(p, f"{m.get('league','')} TABLE")
        t = self._card(p)
        hdr = tk.Frame(t, bg=PANEL_DARK)
        hdr.pack(fill="x", padx=6, pady=(6,2))
        for txt, w in [("#",4),("Team",20),("P",5),("GD",6),("PTS",6),("W",5)]:
            tk.Label(hdr, text=txt, bg=PANEL_DARK, fg=MUTED,
                font=FS, width=w, anchor="w").pack(side="left")
        for pos, team, played, gd, pts, wins in self._table_rows(m):
            active = team in (m.get("home",""), m.get("away",""))
            row = tk.Frame(t, bg="#263244" if active else PANEL_DARK)
            row.pack(fill="x", padx=6, pady=1)
            col = ORANGE if active else TEXT
            for txt, w, fg in [
                (str(pos),4,MUTED),(team,20,col),(str(played),5,MUTED),
                (f"{gd:+}",6,MUTED),(str(pts),6,TEXT),(str(wins),5,MUTED),
            ]:
                tk.Label(row, text=txt, bg=row.cget("bg"),
                    fg=fg, font=FB if active else FS,
                    width=w, anchor="w").pack(side="left", pady=4)

    def _tab_h2h(self, p, m):
        self._sec(p, "HEAD TO HEAD")
        for season, home, away, hs, as_ in self._h2h_rows(m):
            c = self._card(p)
            tk.Label(c, text=season, bg=PANEL_DARK, fg=CYAN,
                font=FB, anchor="w").pack(fill="x", padx=8, pady=(6,2))
            for team, score in [(home,hs),(away,as_)]:
                row = tk.Frame(c, bg=PANEL_DARK)
                row.pack(fill="x", padx=8, pady=2)
                tk.Label(row, text=self._initials(team), bg=PANEL_DARK,
                    fg=MUTED, font=FM, width=5).pack(side="left")
                tk.Label(row, text=team, bg=PANEL_DARK, fg=TEXT,
                    font=FS, anchor="w").pack(side="left", fill="x", expand=True)
                tk.Label(row, text=str(score), bg=PANEL_DARK, fg=TEXT,
                    font=FB, width=3).pack(side="right")

    # ──────────────────────────────────────────
    # Markets (bottom center)
    # ──────────────────────────────────────────

    def _render_markets(self):
        if not self.odds_body or not self.predictions_body:
            return
        self._clear(self.odds_body)
        self._clear(self.predictions_body)
        m = self.current_match
        if self.selected_odds_book:
            self._odds_detail(m, self.selected_odds_book)
        else:
            self._odds_board(m)
        if self.selected_prediction_source:
            self._pred_detail(m, self.selected_prediction_source)
        else:
            self._pred_feed(m)

    def _odds_board(self, m):
        p = self.odds_body
        hdr = tk.Frame(p, bg=PANEL_DARK)
        hdr.pack(fill="x", padx=4, pady=(4,2))
        for txt, w in [("BOOK",13),("HOME",7),("DRAW",7),("AWAY",7),("EDGE",7)]:
            tk.Label(hdr, text=txt, bg=PANEL_DARK, fg=ORANGE,
                font=FM, width=w, anchor="w").pack(side="left")
        for book, home, draw, away, edge in self._odds_rows(m):
            rb = ROW_ALT if edge>=0 else ROW
            row= tk.Frame(p, bg=rb)
            row.pack(fill="x", padx=4, pady=1)
            for txt, w, c in [
                (book,13,TEXT),(f"{home:.2f}",7,CYAN),
                (f"{draw:.2f}",7,MUTED),(f"{away:.2f}",7,ORANGE),
                (f"{edge:+.1f}",7,GREEN if edge>=0 else RED),
            ]:
                lb = tk.Label(row, text=txt, bg=rb, fg=c, font=FM, width=w, anchor="w")
                lb.pack(side="left", pady=3)
                lb.bind("<Button-1>", lambda _e, b=book: self._open_odds(b))
            row.bind("<Button-1>", lambda _e, b=book: self._open_odds(b))
        best = max(self._odds_rows(m), key=lambda x: x[4])
        tk.Label(p, text=f"Best: {best[0]}  edge {best[4]:+.1f}",
            bg=PANEL, fg=GREEN if best[4]>=0 else RED,
            font=FS, anchor="w").pack(fill="x", padx=4, pady=(3,2))

    def _odds_detail(self, m, book_name):
        p = self.odds_body
        top = tk.Frame(p, bg=PANEL_DARK)
        top.pack(fill="x", padx=4, pady=(4,4))
        tk.Button(top, text="< Back", bg="#243244", fg=TEXT,
            relief="flat", font=FS, command=self._close_odds).pack(side="left")
        tk.Label(top, text=f"{book_name}", bg=PANEL_DARK,
            fg=ORANGE, font=FB).pack(side="left", padx=8)
        for market, left, mid, right, note in self._odds_detail_rows(m, book_name):
            row = tk.Frame(p, bg=ROW)
            row.pack(fill="x", padx=4, pady=1)
            for txt, w, c in [
                (market,18,TEXT),(left,10,CYAN),(mid,9,MUTED),
                (right,10,ORANGE),(note,15,GREEN if "value" in note.lower() else MUTED),
            ]:
                tk.Label(row, text=txt, bg=ROW, fg=c,
                    font=FM, width=w, anchor="w").pack(side="left", pady=3)

    def _pred_feed(self, m):
        p = self.predictions_body
        hdr = tk.Frame(p, bg=PANEL_DARK)
        hdr.pack(fill="x", padx=4, pady=(4,2))
        for txt, w in [("SOURCE",13),("HOME",7),("DRAW",7),("AWAY",7),("PICK",10)]:
            tk.Label(hdr, text=txt, bg=PANEL_DARK, fg=ORANGE,
                font=FM, width=w, anchor="w").pack(side="left")
        for src, h, d, a, pick in self._pred_rows(m):
            row = tk.Frame(p, bg=ROW)
            row.pack(fill="x", padx=4, pady=1)
            pc = CYAN if pick==m.get("home") else ORANGE if pick==m.get("away") else MUTED
            for txt, w, c in [
                (src,13,TEXT),(f"{h}%",7,CYAN),(f"{d}%",7,MUTED),
                (f"{a}%",7,ORANGE),(pick[:10],10,pc),
            ]:
                lb = tk.Label(row, text=txt, bg=ROW, fg=c, font=FM, width=w, anchor="w")
                lb.pack(side="left", pady=3)
                lb.bind("<Button-1>", lambda _e, s=src: self._open_pred(s))
            row.bind("<Button-1>", lambda _e, s=src: self._open_pred(s))
        cons = self._consensus(m)
        sc = self._card(p)
        tk.Label(sc, text=f"CONSENSUS: {cons['pick']}  {cons['confidence']}% confidence",
            bg=PANEL_DARK, fg=TEXT, font=FB, anchor="w").pack(fill="x", padx=8, pady=5)

    def _pred_detail(self, m, source_name):
        p = self.predictions_body
        top = tk.Frame(p, bg=PANEL_DARK)
        top.pack(fill="x", padx=4, pady=(4,4))
        tk.Button(top, text="< Back", bg="#243244", fg=TEXT,
            relief="flat", font=FS, command=self._close_pred).pack(side="left")
        tk.Label(top, text=source_name, bg=PANEL_DARK,
            fg=ORANGE, font=FB).pack(side="left", padx=8)
        detail = self._pred_detail_data(m, source_name)
        sc = self._card(p)
        tk.Label(sc, text=detail["headline"], bg=PANEL_DARK, fg=TEXT,
            font=FB, anchor="w").pack(fill="x", padx=8, pady=(6,2))
        for lbl, val in detail["markets"]:
            row = tk.Frame(sc, bg=PANEL_DARK)
            row.pack(fill="x", padx=8, pady=1)
            tk.Label(row, text=lbl, bg=PANEL_DARK, fg=CYAN, font=FS, width=16, anchor="w").pack(side="left")
            tk.Label(row, text=val, bg=PANEL_DARK, fg=TEXT, font=FS, anchor="w").pack(side="left")

    def _open_odds(self, b):
        self.selected_odds_book = b; self._render_markets()
    def _close_odds(self):
        self.selected_odds_book = None; self._render_markets()
    def _open_pred(self, s):
        self.selected_prediction_source = s; self._render_markets()
    def _close_pred(self):
        self.selected_prediction_source = None; self._render_markets()

    # ──────────────────────────────────────────
    # Quick find / action bar
    # ──────────────────────────────────────────

    def quick_find(self):
        query = self.quick_query.get().strip()
        if not query:
            return
        lower = query.lower()
        mn = None
        hit = re.search(r"(\d{1,3})", lower)
        if hit:
            mn = min(int(hit.group(1)), self._max_minute(self.current_match))
            self._set_replay_minute(mn)
        tab, lbl = self._qf_target(lower)
        if tab:
            self.set_tab(tab)
        msg = f"Quick Find: {lbl}"
        if mn is not None:
            msg += f" at {self._cur_minute(self.current_match):02d}'"
        if self.tracker_status:
            self.tracker_status.config(text=msg, fg=CYAN)

    def _qf_target(self, q):
        for terms, tab, lbl in [
            (("chat","room"),               "Chat",         "chat"),
            (("lineup","formation"),        "Line-ups",     "line-ups"),
            (("table","standings","rank"),  "Table",        "table"),
            (("h2h","head to head"),        "H2H",          "h2h"),
            (("attack","shot","xg"),        "Attack",       "attack"),
            (("possession","control"),      "Control",      "control"),
            (("defense","defence","foul"),  "Defense",      "defense"),
            (("replay","timeline"),         "Stats Replay", "replay"),
            (("overview","summary"),        "Overview",     "overview"),
        ]:
            if any(t in q for t in terms):
                return tab, lbl
        return "Overview", "overview"

    def reset_to_live(self):
        t = self._ref_minute(self.current_match)
        self._set_replay_minute(t)
        if self.tracker_status:
            self.tracker_status.config(text=f"Reset to {t:02d}'", fg=GREEN)

    # ──────────────────────────────────────────
    # Replay
    # ──────────────────────────────────────────

    def _update_replay_header(self):
        mn  = self._cur_minute(self.current_match)
        ref = self._ref_minute(self.current_match)
        txt = f"Viewing current state {mn:02d}'" if mn==ref else f"Viewing {mn:02d}' replay"
        if self.replay_running:
            txt = f"Playing from {self.replay_start_minute:02d}'  |  now {mn:02d}'"
        self.score_labels["replay_state"].config(text=txt)

    def _play_replay(self):
        if self.replay_slider is None:
            self.set_tab("Stats Replay")
        if not self.replay_slider or self.replay_running:
            return
        self.replay_running = True
        self.replay_start_minute = self._cur_minute(self.current_match)
        self._update_replay_header()
        self._replay_tick()

    def _replay_tick(self):
        if not self.replay_running or not self.replay_slider:
            return
        cur = self._cur_minute(self.current_match)
        if cur >= self.replay_max_minute:
            self._pause_replay(); return
        self._set_replay_minute(cur + 1)
        self.replay_job = self.root.after(380, self._replay_tick)

    def _pause_replay(self):
        self.replay_running = False
        if self.replay_job:
            self.root.after_cancel(self.replay_job)
            self.replay_job = None
        self._update_replay_header()

    def _stop_replay(self, reset=True):
        self._pause_replay()
        target = self.replay_start_minute if self.replay_start_minute is not None else self._ref_minute(self.current_match)
        self.replay_start_minute = None
        self._set_replay_minute(target)

    def _set_replay_minute(self, mn):
        mn = max(0, min(int(mn), self._max_minute(self.current_match)))
        self.replay_minute = mn
        if self.replay_slider and self.tab_name.get() == "Stats Replay":
            self.replay_slider.set(mn)
            if self.replay_refresh:
                self.replay_refresh(str(mn))
        else:
            self._update_replay_header()
            self._render_tab()

    def _draw_markers(self, canvas, m, maxm):
        canvas.delete("all")
        W = max(canvas.winfo_width(), 10)
        lp, rp, ly = 4, 4, 10
        canvas.create_line(lp, ly, W-rp, ly, fill=BORDER, width=2)
        for idx, ev in enumerate(self._timeline_events(m, maxm)):
            x   = lp + (W-lp-rp) * ev["minute"] / max(maxm,1)
            col = self._ev_color(ev["event"])
            tag = f"mk_{idx}"
            canvas.create_line(x,3,x,17, fill=col, width=2, tags=(tag,))
            canvas.create_oval(x-3,ly-3,x+3,ly+3, fill=col, outline=col, tags=(tag,))
            canvas.create_text(x,21, text=ev["minute_text"],
                fill=MUTED, font=FS, tags=(tag,))
            canvas.tag_bind(tag,"<Button-1>",
                lambda _e, mn=ev["minute"]: self._set_replay_minute(mn))

    def _render_replay_events(self, p, m, mn, maxm):
        self._clear(p)
        shown = [e for e in self._timeline_events(m,maxm) if e["minute"] <= mn]
        if not shown:
            tk.Label(p, text="No events yet at this point.",
                bg=PANEL_DARK, fg=MUTED, font=FS, pady=6).pack(fill="x")
            return
        for ev in shown[-5:]:
            row = tk.Frame(p, bg=PANEL_DARK)
            row.pack(fill="x", padx=8, pady=2)
            tk.Label(row, text=ev["minute_text"], bg="#243244", fg=TEXT,
                font=FM, width=5, pady=3).pack(side="left")
            tk.Label(row, text=ev["event"], bg=PANEL_DARK,
                fg=self._ev_color(ev["event"]), font=FB,
                width=7, anchor="w").pack(side="left", padx=(6,8))
            tk.Label(row, text=ev["team"], bg=PANEL_DARK, fg=TEXT,
                font=FB, width=14, anchor="w").pack(side="left")
            tk.Label(row, text=ev["detail"], bg=PANEL_DARK, fg=MUTED,
                font=FS, anchor="w").pack(side="left", fill="x", expand=True)

    # ──────────────────────────────────────────
    # Chat helpers
    # ──────────────────────────────────────────

    def _active_room(self, m):
        return self.match_chat_room.setdefault(m["id"], "Open Room")

    def _set_room(self, m, room):
        self.match_chat_room[m["id"]] = room
        self.chat_message.set("")
        self._render_chat_preview()
        if self.tab_name.get() == "Chat":
            self._render_tab()

    def _chat_thread(self, m):
        if m["id"] not in self.match_chats or not isinstance(self.match_chats[m["id"]], dict):
            self.match_chats[m["id"]] = {
                "Open Room":  self._seed_thread(m,"Open Room"),
                "Value Talk": self._seed_thread(m,"Value Talk"),
                "Live Pulse": self._seed_thread(m,"Live Pulse"),
                "Post-match": self._seed_thread(m,"Post-match"),
            }
        return self.match_chats[m["id"]].setdefault(self._active_room(m), [])

    def _chat_thread_room(self, m, room):
        if m["id"] not in self.match_chats or not isinstance(self.match_chats[m["id"]], dict):
            self._chat_thread(m)
        return self.match_chats[m["id"]].get(room, [])

    def _seed_thread(self, m, room):
        mn  = self._ref_minute(m)
        st  = "pre-match" if m.get("status")=="UP" else f"live at {mn:02d}'"
        seeds = {
            "Open Room": [
                {"author":"EdgeAgent","tag":"agent",
                 "time":f"{mn:02d}'",
                 "text":f"{m.get('home','')} vs {m.get('away','')} {st}. Edge {m.get('edge',0):+.1f}."},
                {"author":"ValueHunter","tag":"community","time":f"{mn:02d}'",
                 "text":f"Watching whether {m.get('away','')} keeps pressure in last 20."},
            ],
            "Value Talk": [
                {"author":"EdgeAgent","tag":"agent","time":f"{mn:02d}'",
                 "text":f"Value room open. Edge {m.get('edge',0):+.1f} vs book prices."},
            ],
            "Live Pulse": [
                {"author":"EdgeAgent","tag":"agent","time":f"{mn:02d}'",
                 "text":f"Live pulse at {mn:02d}'. Track momentum and pressure swings here."},
            ],
            "Post-match": [
                {"author":"EdgeAgent","tag":"agent","time":f"{mn:02d}'",
                 "text":"Post-match room ready for review and analysis."},
            ],
        }
        return seeds.get(room, seeds["Open Room"])

    def _chat_bubble(self, p, item):
        b = tk.Frame(p, bg=PANEL_DARK)
        b.pack(fill="x", padx=8, pady=3)
        top = tk.Frame(b, bg=PANEL_DARK)
        top.pack(fill="x")
        c = ORANGE if item["tag"]=="agent" else GREEN if item["tag"]=="you" else CYAN
        tk.Label(top, text=item["author"], bg=PANEL_DARK, fg=c, font=FB, anchor="w").pack(side="left")
        tk.Label(top, text=item.get("time",""), bg=PANEL_DARK, fg=MUTED, font=FS, anchor="e").pack(side="right")
        tk.Label(b, text=item["text"], bg=PANEL_DARK, fg=TEXT,
            font=FS, anchor="w", justify="left", wraplength=680).pack(fill="x", pady=(1,0))
        tk.Frame(b, bg="#243244", height=1).pack(fill="x", pady=(6,0))

    def _post_chat(self, m):
        text = self.chat_message.get().strip()
        if not text: return
        thread = self._chat_thread(m)
        mn = self._cur_minute(m)
        thread.append({"author":"You","tag":"you","time":f"{mn:02d}'","text":text})
        thread.append({"author":"EdgeAgent","tag":"agent","time":f"{mn:02d}'",
            "text":f"EdgeAgent: noted at {mn:02d}' — keep the debate tied to replay minute and real edge."})
        self.chat_message.set("")
        self._render_chat_preview()
        if self.tab_name.get() == "Chat":
            self._render_tab()

    # ──────────────────────────────────────────
    # Watchlist actions
    # ──────────────────────────────────────────

    def add_to_watchlist(self):
        m = self.current_match
        self.watchlist_ids.add(m["id"])
        try:
            add_match(self._state(m), self._market(m))
        except Exception:
            pass
        if self.tracker_status:
            self.tracker_status.config(text=f"Added: {m.get('home','')} vs {m.get('away','')}", fg=GREEN)
        self.render_matches(); self.render_watchlist(); self._render_sidebar_watchlist()

    def remove_from_watchlist(self):
        m = self.current_match
        self.watchlist_ids.discard(m["id"])
        if self.tracker_status:
            self.tracker_status.config(text=f"Removed: {m.get('home','')} vs {m.get('away','')}", fg=MUTED)
        self.render_matches(); self.render_watchlist(); self._render_sidebar_watchlist()

    # ──────────────────────────────────────────
    # Tracker
    # ──────────────────────────────────────────

    def start_tracker(self):
        if self.tracker_running:
            return
        self.tracker_running = True
        if self.tracker_status:
            self.tracker_status.config(text="Tracker started.", fg=GREEN)
        self._tracker_tick()

    def _tracker_tick(self):
        if not self.tracker_running: return
        m = self.current_match
        if m.get("status")=="LIVE" and m.get("minute",0) < 90:
            m["minute"] += 1
            if m["minute"] >= 90:
                m["status"] = "FT"
                self.tracker_running = False
                self._settle_challenges(m)
                if self.tracker_status:
                    self.tracker_status.config(text="Match finished.", fg=GREEN)
            self.select_match(m)
        if self.tracker_running:
            self.tracker_job = self.root.after(5000, self._tracker_tick)

    def stop_tracker(self):
        self.tracker_running = False
        if self.tracker_job:
            self.root.after_cancel(self.tracker_job)
            self.tracker_job = None
        if self.tracker_status:
            self.tracker_status.config(text="Tracker stopped.", fg=MUTED)

    def test_speed(self):
        if self.status_label:
            self.status_label.config(
                text=f"Speed test: {len(self.filtered_matches())} matches filtered instantly")

    # ──────────────────────────────────────────
    # Stats engine
    # ──────────────────────────────────────────

    def _max_minute(self, m):
        return max(m.get("minute",1),1) if m.get("status")=="LIVE" else 90

    def _ref_minute(self, m):
        if m.get("status")=="LIVE": return max(m.get("minute",1),1)
        if m.get("status")=="UP":   return 0
        return 90

    def _cur_minute(self, m):
        mx = self._max_minute(m)
        if self.replay_minute is None: return self._ref_minute(m)
        return max(0, min(int(self.replay_minute), mx))

    def _curve(self, r):
        r = max(0.0, min(r, 1.0))
        if r<=0: return 0.0
        if r>=1: return 1.0
        return min(1.0, max(0.0, (r**0.84)*(0.92+r*0.08)))

    def _base_stats(self, m):
        e = max(m.get("edge",0), 0)
        return [
            ("Expected goals (xG)", round(0.8+e/10,2), round(0.7+abs(min(m.get("edge",0),0))/10,2)),
            ("Shots on target", 5 if m.get("home_score",0) else 2, 3 if m.get("away_score",0) else 2),
            ("Shots off target",6,4),("Blocked shots",4,2),
            ("Possession (%)", 54 if m.get("edge",0)>=0 else 47, 46 if m.get("edge",0)>=0 else 53),
            ("Corner kicks",6,3),("Offsides",1,2),("Fouls",10,8),
            ("Throw ins",19,21),("Yellow cards",1,1),
            ("Crosses",14,10),("Goalkeeper saves",2,4),
        ]

    def _stats_at(self, m, mn, mx=90):
        ratio = 0 if mx<=0 else max(0.0, min(mn/mx, 1.0))
        bias  = ((m.get("id",1)%5)-2)/14
        rows  = []
        for lbl, fh, fa in self._base_stats(m):
            if lbl == "Possession (%)":
                sw = bias*(0.6-ratio)*18
                hs = max(32,min(68,fh+sw))
                rows.append((lbl, int(round(hs)), int(round(100-hs))))
                continue
            hp = max(0.0, ratio+bias*0.18)
            ap = max(0.0, ratio-bias*0.18)
            if lbl == "Expected goals (xG)":
                rows.append((lbl, round(fh*self._curve(hp),2), round(fa*self._curve(ap),2)))
            else:
                rows.append((lbl, int(round(fh*self._curve(hp))), int(round(fa*self._curve(ap)))))
        if m.get("status")=="UP" and mn==0:
            return [(lbl, 50 if lbl=="Possession (%)" else 0.0 if lbl=="Expected goals (xG)" else 0,
                         50 if lbl=="Possession (%)" else 0.0 if lbl=="Expected goals (xG)" else 0)
                    for lbl,_,_ in rows]
        return rows

    def _smap(self, m, mn=None, mx=None):
        if mx is None: mx = self._max_minute(m)
        if mn is None: mn = self._cur_minute(m)
        return {lbl:(h,a) for lbl,h,a in self._stats_at(m,mn,mx)}

    def _split(self, l, r):
        t = l+r
        if t<=0: return 50,50
        lp = int(round(l/t*100))
        return lp, max(0,100-lp)

    def _stats_summary(self, m, mn, mx=90):
        s = {lbl:(h,a) for lbl,h,a in self._stats_at(m,mn,mx)}
        xh,xa = s.get("Expected goals (xG)",(0.0,0.0))
        sh,sa = s.get("Shots on target",(0,0))
        ph,pa = s.get("Possession (%)",(50,50))
        ch,ca = s.get("Corner kicks",(0,0))
        return [
            ("xG Share",    *self._split(xh,xa)),
            ("Shot Quality",*self._split(sh,sa)),
            ("Possession",  int(ph),int(pa)),
            ("Pressure",    *self._split(ch,ca)),
        ]

    def _attack_stats(self, m, mn, mx):
        s = self._smap(m,mn,mx)
        xh,xa = s.get("Expected goals (xG)",(0.0,0.0))
        sh,sa = s.get("Shots on target",(0,0))
        oh,oa = s.get("Shots off target",(0,0))
        bh,ba = s.get("Blocked shots",(0,0))
        ch,ca = s.get("Crosses",(0,0))
        kh,ka = s.get("Corner kicks",(0,0))
        return [
            ("Expected goals (xG)",xh,xa),
            ("Shots on target",sh,sa),("Shots off target",oh,oa),
            ("Blocked shots",bh,ba),
            ("Big chances",max(0,int(round(sh*0.6+xh*1.5))),max(0,int(round(sa*0.6+xa*1.5)))),
            ("Touches in box",sh+oh+int(round(ch*0.4)),sa+oa+int(round(ca*0.4))),
            ("Crosses",ch,ca),("Set-piece threat",kh,ka),
        ]

    def _attack_summary(self, m, mn, mx):
        rows = {l:(h,a) for l,h,a in self._attack_stats(m,mn,mx)}
        return [
            ("xG Threat",  *self._split(*rows["Expected goals (xG)"])),
            ("On Target",  *self._split(*rows["Shots on target"])),
            ("Box Threat", *self._split(*rows["Touches in box"])),
        ]

    def _control_stats(self, m, mn, mx):
        s = self._smap(m,mn,mx)
        ph,pa = s.get("Possession (%)",(50,50))
        th,ta = s.get("Throw ins",(0,0))
        ch,ca = s.get("Corner kicks",(0,0))
        xh,xa = s.get("Crosses",(0,0))
        r = 0 if mx<=0 else max(0.0,min(mn/mx,1.0))
        return [
            ("Possession (%)",ph,pa),
            ("Pass accuracy (%)",int(round(76+ph*0.18+r*4)),int(round(76+pa*0.18+r*4))),
            ("Field tilt (%)",int(round(min(78,max(22,ph+ch*2+m.get("edge",0)*1.5)))),0),
            ("Corners won",ch,ca),("Cross volume",xh,xa),
            ("Tempo actions",max(1,int(round((th+ch+xh)*0.9))),max(1,int(round((ta+ca+xa)*0.9)))),
        ]

    def _control_summary(self, m, mn, mx):
        rows = {l:(h,a) for l,h,a in self._control_stats(m,mn,mx)}
        return [
            ("Possession", *rows["Possession (%)"]),
            ("Corners",    *self._split(*rows["Corners won"])),
        ]

    def _defense_stats(self, m, mn, mx):
        s = self._smap(m,mn,mx)
        fh,fa = s.get("Fouls",(0,0))
        yh,ya = s.get("Yellow cards",(0,0))
        svh,sva=s.get("Goalkeeper saves",(0,0))
        bh,ba = s.get("Blocked shots",(0,0))
        r = 0 if mx<=0 else max(0.0,min(mn/mx,1.0))
        dh=max(1,int(round(9+r*11+max(m.get("edge",0),0))))
        da=max(1,int(round(9+r*11+abs(min(m.get("edge",0),0)))))
        return [
            ("Goalkeeper saves",svh,sva),("Blocked shots",bh,ba),
            ("Duels won",dh,da),("Fouls committed",fh,fa),("Yellow cards",yh,ya),
        ]

    def _defense_summary(self, m, mn, mx):
        rows = {l:(h,a) for l,h,a in self._defense_stats(m,mn,mx)}
        return [
            ("Save Load",  *self._split(*rows["Goalkeeper saves"])),
            ("Duels",      *self._split(*rows["Duels won"])),
            ("Discipline", *self._split(max(1,5-rows["Yellow cards"][0]),max(1,5-rows["Yellow cards"][1]))),
        ]

    # ──────────────────────────────────────────
    # Snapshot / Decision engine data
    # ──────────────────────────────────────────

    def _snapshot(self, m):
        cons      = self._consensus(m)
        odds      = self._odds_rows(m)
        best      = max(odds, key=lambda x: x[4])
        if cons["pick"] == m.get("home"):
            mp = round(100/best[1])
        elif cons["pick"] == m.get("away"):
            mp = round(100/best[3])
        else:
            mp = round(100/best[2])
        tp   = cons["confidence"]
        edge = round(tp - mp, 1)
        dq   = self._data_quality(m)
        ls   = self._lineup_status(m)
        wth  = self._weather(m)
        mm   = self._mkt_move(m)

        dec = "PASS"; dc = MUTED
        if dq>=82 and edge>=5 and ls=="Confirmed": dec,dc = "BET",GREEN
        elif dq>=70 and edge>=2:                   dec,dc = "LEAN",ORANGE

        rf = [
            f"Consensus leans {cons['pick']} with {cons['confidence']}% confidence.",
            f"Best book is {best[0]} — {edge:+.1f} implied edge.",
            f"Form: {m.get('home','')} {''.join(m.get('home_form',['?']*5))} vs {m.get('away','')} {''.join(m.get('away_form',['?']*5))}.",
        ]
        if m.get("status")=="LIVE":
            rf.append(f"Live at {m.get('minute',0)}' — score {m.get('home_score',0)}-{m.get('away_score',0)}.")
        ra = [
            f"Market move is {mm.lower()} — late entries may lose value.",
            f"{wth} conditions. Referee: {m.get('referee','')}.",
            "Source disagreement matters even when average consensus looks strong.",
        ]
        mis = self._missing(m)
        if mis != ["None"]:
            ra.append(f"Weak inputs: {', '.join(mis)}.")

        return {
            "decision": dec, "decision_color": dc,
            "market": f"{best[0]} best price  |  pick {cons['pick']}",
            "confidence": tp, "edge": edge,
            "true_prob": tp, "market_prob": mp, "data_quality": dq,
            "freshness": self._freshness(m),
            "lineups": ls, "lineup_color": GREEN if ls=="Confirmed" else YELLOW if ls=="Partial" else RED,
            "weather": wth, "news_status": self._news(m),
            "reasons_for": rf, "reasons_against": ra,
            "data_buckets": [
                ("Match state",  f"{m.get('status','')} {m.get('minute',0)}'  {m.get('home_score',0)}-{m.get('away_score',0)}"),
                ("Team profile", f"Atk {m.get('home_avg',0):.1f}/{m.get('away_avg',0):.1f}  form {''.join(m.get('home_form',['?']*5))}/{''.join(m.get('away_form',['?']*5))}"),
                ("Availability", f"Lineups {ls}"),
                ("Market",       f"{len(odds)} books  best {best[0]}  {mm}"),
                ("Context",      f"{wth}  {m.get('venue','')}"),
            ],
            "sources": [
                ("Lineups",       "Squads",    ls,                                      "High"),
                ("Local News",    "Context",   "Confirmed" if m.get("status")=="LIVE" else "Checking", "Medium"),
                ("Weather",       "External",  "Fresh",                                 "Medium"),
                ("Odds Feed",     "Market",    "Live",                                  "High"),
                ("Pred Feed",     "Consensus", "Live",                                  "Medium"),
            ],
            "consensus_spread": len([r[4] for r in self._pred_rows(m) if r[4]==cons["pick"]]),
            "books_tracked": len(odds),
            "prediction_sources": len(self._pred_rows(m)),
            "market_move": mm,
            "referee_note": "card-heavy" if any(n in m.get("referee","") for n in ("Taylor","Oliver")) else "balanced",
        }

    def _data_quality(self, m):
        s = 76
        if m.get("status")=="LIVE": s+=6
        if abs(m.get("edge",0))>=4: s+=4
        if m.get("minute",0)==0:    s-=3
        return max(55, min(s, 94))

    def _freshness(self, m):
        if m.get("status")=="LIVE": return "15s live"
        if m.get("minute",0)==0:    return "5m pre"
        return "30m old"

    def _lineup_status(self, m):
        if m.get("status")=="LIVE": return "Confirmed"
        if m.get("minute",0)==0 and m.get("edge",0)>=4: return "Partial"
        return "Pending"

    def _weather(self, m):
        return {"England":"Light rain 11C","Spain":"Clear 17C",
                "Italy":"Calm 15C","Germany":"Windy 9C"}.get(m.get("country",""),"Normal 14C")

    def _news(self, m):
        return "2 reports checked" if m.get("status")=="LIVE" else "Awaiting pressers"

    def _mkt_move(self, m):
        e = m.get("edge",0)
        return "Sharp to away" if e<-2 else "Mild to home" if e>4 else "Flat market"

    def _missing(self, m):
        out = []
        if m.get("status")!="LIVE":    out.append("confirmed lineups")
        if abs(m.get("edge",0))<2:      out.append("clear discrepancy")
        return out or ["None"]

    def _consensus(self, m):
        rows = self._pred_rows(m)
        ha = round(sum(r[1] for r in rows)/len(rows))
        da = round(sum(r[2] for r in rows)/len(rows))
        aa = round(sum(r[3] for r in rows)/len(rows))
        pick = m.get("home") if ha>=da and ha>=aa else m.get("away") if aa>=da else "Draw"
        return {"home":ha,"draw":da,"away":aa,"pick":pick,"confidence":max(ha,da,aa)}

    def _odds_rows(self, m):
        bh,bd,ba = m.get("odds",(2.0,3.5,4.0))
        books = [
            ("DraftKings",-0.02,0.04,0.03),("FanDuel",0.03,-0.03,0.02),
            ("BetMGM",0.01,0.02,-0.04),("Caesars",-0.04,0.05,0.01),
            ("bet365",0.02,-0.01,0.04),("Pinnacle",0.05,0.03,-0.02),
            ("BetRivers",-0.01,-0.04,0.05),("Unibet",0.04,0.00,-0.01),
        ]
        return [(book, max(1.01,bh+h), max(1.01,bd+d), max(1.01,ba+a),
                 round(m.get("edge",0)+((i%4)-1.5)*0.7,1))
                for i,(book,h,d,a) in enumerate(books)]

    def _odds_detail_rows(self, m, book_name):
        br = next((r for r in self._odds_rows(m) if r[0]==book_name), self._odds_rows(m)[0])
        _,home,draw,away,_ = br
        return [
            ("1X2",         f"{home:.2f}", f"{draw:.2f}", f"{away:.2f}", "main line"),
            ("Double Chance","1X 1.22",    "",            "X2 1.61",     "safer"),
            ("Over/Under 2.5","Over 1.91", "",            "Under 1.95",  "tight"),
            ("BTTS",        "Yes 1.68",    "",            "No 2.18",     "live pace"),
            ("Asian Handicap",f"{m.get('home','')} -0.25","",f"{m.get('away','')} +0.25","model value"),
            ("Corners O/U 9.5","Over 1.87","",            "Under 1.98",  "edge small"),
        ]

    def _pred_rows(self, m):
        home,draw,away = m.get("pred",(33,33,34))
        sources = [
            ("Opta",3,-1,-2),("Forebet",-2,1,1),("PredictZ",1,2,-3),
            ("SportsMole",-1,-2,3),("WinDrawWin",2,0,-2),
            ("Betimate",-3,3,0),("SoccerVista",0,-1,1),
            ("Our Model",round(m.get("edge",0)),0,-round(m.get("edge",0))),
        ]
        rows = []
        for src,ha,da,aa in sources:
            h=max(1,min(98,int(home+ha))); d=max(1,min(98,int(draw+da))); a=max(1,min(98,int(away+aa)))
            t=h+d+a; h=round(h*100/t); d=round(d*100/t); a=max(1,100-h-d)
            pick = m.get("home") if h>=d and h>=a else m.get("away") if a>=d else "Draw"
            rows.append((src,h,d,a,pick))
        return rows

    def _pred_detail_data(self, m, source_name):
        row = next((r for r in self._pred_rows(m) if r[0]==source_name), self._pred_rows(m)[0])
        _,home,draw,away,pick = row
        return {
            "headline": f"{source_name} leans {pick} for {m.get('home','')} vs {m.get('away','')}",
            "markets": [
                ("1X2",        f"{home}% / {draw}% / {away}%"),
                ("Over 2.5",   f"{min(78,away+12)}%"),
                ("Under 2.5",  f"{max(22,100-away-12)}%"),
                ("BTTS",       f"{52+(m.get('home_score',0)+m.get('away_score',0))*6}%"),
            ],
        }

    # ──────────────────────────────────────────
    # Pitch drawing
    # ──────────────────────────────────────────

    def _draw_pitch(self, canvas, m, mn):
        canvas.delete("all")
        W = max(canvas.winfo_width(), 860); H = max(canvas.winfo_height(), 480)
        mg = 20
        canvas.create_rectangle(mg,mg,W-mg,H-mg,outline="#d5e59b",width=2)
        canvas.create_line(W/2,mg,W/2,H-mg,fill="#d5e59b",width=2)
        canvas.create_oval(W/2-50,H/2-50,W/2+50,H/2+50,outline="#d5e59b",width=2)
        canvas.create_oval(W/2-4,H/2-4,W/2+4,H/2+4,fill="#d5e59b",outline="")
        self._penalty_box(canvas,W,H,mg,True)
        self._penalty_box(canvas,W,H,mg,False)
        canvas.create_text(mg+6,8,text=f"{m.get('home','')}  {self._lineup_formation(m,'home',mn)}",fill=TEXT,font=FB,anchor="nw")
        canvas.create_text(W-mg-6,8,text=f"{m.get('away','')}  {self._lineup_formation(m,'away',mn)}",fill=TEXT,font=FB,anchor="ne")
        self._draw_team(canvas,self._lineup_players(m,"home",mn),W,H,mg,"left",True)
        self._draw_team(canvas,self._lineup_players(m,"away",mn),W,H,mg,"right",False)

    def _penalty_box(self, canvas, W, H, mg, left):
        if left:
            x0,x1,sx1 = mg,mg+120,mg+48
        else:
            x0,x1,sx1 = W-mg-120,W-mg,W-mg-48
        canvas.create_rectangle(x0,H*0.22,x1,H*0.78,outline="#d5e59b",width=2)
        if left:
            canvas.create_rectangle(x0,H*0.38,sx1,H*0.62,outline="#d5e59b",width=2)
        else:
            canvas.create_rectangle(sx1,H*0.38,x1,H*0.62,outline="#d5e59b",width=2)

    def _draw_team(self, canvas, players, W, H, mg, side, is_home):
        cf = "#101826" if is_home else "#f8fafc"
        tf = TEXT if is_home else "#0f172a"
        ac = ORANGE if is_home else CYAN
        uw = W-(mg*2); uh = H-(mg*2)
        for pl in players:
            xn = 1-pl["y"] if side=="left" else pl["y"]
            x  = mg+uw*xn; y = mg+uh*pl["x"]
            r  = 16
            if pl.get("sub"):
                canvas.create_oval(x-r-3,y-r-3,x+r+3,y+r+3,outline=ac,width=2)
            canvas.create_oval(x-r,y-r,x+r,y+r,fill=cf,outline="")
            canvas.create_text(x,y,text=str(pl["number"]),fill=tf,font=FB)
            canvas.create_text(x,y+24,text=pl["name"],fill=TEXT,font=FS)

    def _lineup_formation(self, m, side, mn):
        if side=="home": return "4-3-3" if mn<58 else "4-2-3-1"
        return "3-5-2" if mn<63 else "4-4-2"

    def _lineup_players(self, m, side, mn):
        if side=="home":
            pl = [
                {"name":"Ederson","number":31,"x":0.50,"y":0.92},
                {"name":"Walker","number":2,"x":0.18,"y":0.79},
                {"name":"Dias","number":3,"x":0.38,"y":0.76},
                {"name":"Gvardiol","number":24,"x":0.62,"y":0.76},
                {"name":"Ake","number":6,"x":0.82,"y":0.79},
                {"name":"Rodri","number":16,"x":0.50,"y":0.63},
                {"name":"De Bruyne","number":17,"x":0.30,"y":0.57},
                {"name":"Bernardo","number":20,"x":0.70,"y":0.57},
                {"name":"Foden","number":47,"x":0.20,"y":0.38},
                {"name":"Haaland","number":9,"x":0.50,"y":0.31},
                {"name":"Doku","number":11,"x":0.80,"y":0.38},
            ]
            if mn>=58:
                pl[10]={"name":"Grealish","number":10,"x":0.80,"y":0.44,"sub":True}
                pl[6] ={"name":"Kovacic","number":8,"x":0.34,"y":0.60,"sub":True}
            return pl
        pl = [
            {"name":"Alisson","number":1,"x":0.50,"y":0.08},
            {"name":"Konate","number":5,"x":0.24,"y":0.19},
            {"name":"Van Dijk","number":4,"x":0.50,"y":0.16},
            {"name":"Robertson","number":26,"x":0.76,"y":0.19},
            {"name":"Alexander-Arnold","number":66,"x":0.12,"y":0.32},
            {"name":"Mac Allister","number":10,"x":0.34,"y":0.30},
            {"name":"Szoboszlai","number":8,"x":0.50,"y":0.28},
            {"name":"Gravenberch","number":38,"x":0.66,"y":0.30},
            {"name":"Diaz","number":7,"x":0.88,"y":0.32},
            {"name":"Salah","number":11,"x":0.36,"y":0.47},
            {"name":"Nunez","number":9,"x":0.64,"y":0.47},
        ]
        if mn>=63:
            pl[9]={"name":"Jota","number":20,"x":0.34,"y":0.44,"sub":True}
            pl[6]={"name":"Jones","number":17,"x":0.50,"y":0.28,"sub":True}
        return pl

    # ──────────────────────────────────────────
    # Table / H2H data
    # ──────────────────────────────────────────

    def _table_rows(self, m):
        base = [
            ("Inter",33,49,78,25),("Napoli",33,15,66,20),("AC Milan",33,20,64,18),
            ("Juventus",32,26,60,17),("Como 1907",33,29,58,16),("AS Roma",33,17,58,18),
            ("Atalanta",33,16,54,14),("Bologna",32,5,48,14),("Lazio",33,4,47,12),
            ("Udinese",33,-5,43,12),("Torino",33,-17,40,11),("Salernitana",33,-22,28,7),
        ]
        teams = [r[0] for r in base]
        if m.get("home") not in teams: base.insert(4,(m.get("home",""),33,8,51,13))
        if m.get("away") not in teams: base.insert(2,(m.get("away",""),33,20,64,18))
        return [(i,*r) for i,r in enumerate(base[:14],start=1)]

    def _h2h_rows(self, m):
        h = m.get("home",""); a = m.get("away","")
        return [
            ("2025",a,h,3,0),("2024/25",a,h,1,0),
            ("2024",h,a,0,1),("2023/24",h,a,1,3),
            ("2023",a,h,1,0),("2022/23",a,h,3,1),
        ]

    # ──────────────────────────────────────────
    # Events / timeline
    # ──────────────────────────────────────────

    def _ev_color(self, ev):
        return {"GOAL":ORANGE,"CARD":YELLOW,"SUB":CYAN,"SHOT":CYAN,
                "SAVE":CYAN,"PRESS":GREEN,"VAR":PURPLE,"PEN":RED}.get(ev,CYAN)

    def _match_events(self, m):
        if m.get("status")=="LIVE":
            return [
                ("09'",m.get("home",""),"SHOT","Early chance forced a save"),
                ("24'",m.get("home",""),"CARD","Tactical foul in transition"),
                ("41'",m.get("away",""),"GOAL",f"{m.get('away','')} took the lead"),
                ("HT","Match","SCORE",f"{m.get('home_score',0)}-{m.get('away_score',0)} at half"),
                ("58'",m.get("home",""),"SUB","Fresh winger to raise tempo"),
                (f"{m.get('minute',0)}'",m.get("home",""),"PRESS","Home pressing higher now"),
            ]
        if m.get("minute",0)==0:
            return [("00'","Match","INFO","Pre-match — awaiting kickoff")]
        return [
            ("12'",m.get("home",""),"SHOT","Early chance saved"),
            ("27'",m.get("away",""),"GOAL","Back-post finish"),
            ("49'",m.get("home",""),"SUB","Midfield change"),
            ("68'",m.get("away",""),"CARD","Late challenge"),
            ("FT","Match","SCORE",f"{m.get('home_score',0)}-{m.get('away_score',0)} full time"),
        ]

    def _timeline_events(self, m, maxm):
        events = []
        for mt, team, ev, detail in self._match_events(m):
            mn = self._ev_minute(mt, maxm)
            if mn is None: continue
            events.append({"minute":mn,"minute_text":mt,
                "team":team or "Match","event":ev,"detail":detail})
        return events

    def _ev_minute(self, txt, maxm):
        t = str(txt).strip().upper().replace("'","")
        if t=="HT": return min(45,maxm)
        if t=="FT": return maxm
        d = "".join(c for c in t if c.isdigit())
        return min(int(d),maxm) if d else None

    # ──────────────────────────────────────────
    # Challenge / accuracy stubs
    # ──────────────────────────────────────────

    def _seed_challenge_history(self):
        return []

    def _settle_challenges(self, m):
        pass

    def _match_finished(self, m):
        return m.get("status") in ("FT","FINISHED") or (m.get("minute",0)>=90 and m.get("status")!="UP")

    def _state(self, m):
        return MatchState(
            home_team=m.get("home",""), away_team=m.get("away",""),
            minute=int(m.get("minute",0)),
            home_goals=int(m.get("home_score",0)), away_goals=int(m.get("away_score",0)),
            stoppage_minutes_remaining=0, home_red_cards=0, away_red_cards=0,
            pressure_bias=1 if m.get("edge",0)>0 else 0)

    def _market(self, m):
        return MarketInput(total_line=2.5,
            draw_cents=m.get("draw_price",33.0),
            under_cents=m.get("under_price",50.0),
            over_cents=m.get("over_price",50.0))

    # ──────────────────────────────────────────
    # New tabs: News, Weather, Form, Players, Video, Trivia
    # ──────────────────────────────────────────

    def _placeholder_tab(self, p, title, lines):
        """Generic placeholder tab with a message and bullet points."""
        self._sec(p, title)
        c = self._card(p)
        c.pack(fill="x", pady=4)
        for line in lines:
            col = CYAN if line.startswith("•") else MUTED
            tk.Label(c, text=line, bg=PANEL_DARK, fg=col,
                font=FS, anchor="w", justify="left",
                padx=10, pady=3, wraplength=580).pack(fill="x")

    def _tab_news(self, p, m):
        self._sec(p, f"MATCH NEWS — {m.get('home','')} vs {m.get('away','')}")
        tk.Label(p, text="Latest news and articles about this match.",
            bg=PANEL, fg=MUTED, font=FS, anchor="w", pady=2).pack(fill="x")
        news_items = [
            ("Sky Sports", f"{m.get('home','')} manager confirms starting XI for today."),
            ("BBC Sport",  f"{m.get('away','')} striker doubtful with hamstring concern."),
            ("The Guardian",f"Preview: Can {m.get('home','')} extend unbeaten run?"),
            ("ESPN",       "Referee appointments confirmed for Saturday's fixtures."),
            ("Transfermarkt","Latest injury and suspension updates."),
        ]
        for source, headline in news_items:
            card = tk.Frame(p, bg=PANEL_DARK,
                highlightbackground=BORDER, highlightthickness=1)
            card.pack(fill="x", pady=3)
            row = tk.Frame(card, bg=PANEL_DARK)
            row.pack(fill="x", padx=10, pady=6)
            tk.Label(row, text=f"[{source}]", bg=PANEL_DARK,
                fg=CYAN, font=FM, anchor="w", width=16).pack(side="left")
            tk.Label(row, text=headline, bg=PANEL_DARK,
                fg=TEXT, font=FS, anchor="w", wraplength=480,
                justify="left").pack(side="left", fill="x", expand=True)
        self._placeholder_tab(p, "DATA STATUS", [
            "• News feed: placeholder (mock data)",
            "• Connect real news API in next phase.",
            "• Supported sources: RSS, Sky Sports, BBC Sport, ESPN.",
        ])

    def _tab_weather(self, p, m):
        self._sec(p, f"MATCH CONDITIONS — {m.get('venue','Stadium')}")
        country = m.get("country","England")
        weather_data = {
            "England": ("11°C","Light rain","SW 12 km/h","78%","9 km"),
            "Spain":   ("17°C","Clear sky","NE 8 km/h","45%","20 km"),
            "Italy":   ("15°C","Partly cloudy","NW 10 km/h","60%","15 km"),
            "Germany": ("9°C","Overcast","W 18 km/h","82%","8 km"),
        }
        temp, cond, wind, humid, vis = weather_data.get(country,("14°C","Normal","10 km/h","65%","12 km"))

        metrics = [
            ("Temperature",  temp),
            ("Conditions",   cond),
            ("Wind",         wind),
            ("Humidity",     humid),
            ("Visibility",   vis),
            ("Pitch",        "Good"),
            ("Roof",         "Open air"),
        ]
        c = self._card(p)
        c.pack(fill="x", pady=4)
        for lbl, val in metrics:
            row = tk.Frame(c, bg=PANEL_DARK)
            row.pack(fill="x", padx=10, pady=3)
            tk.Label(row, text=lbl, bg=PANEL_DARK, fg=MUTED,
                font=FS, width=16, anchor="w").pack(side="left")
            tk.Label(row, text=val, bg=PANEL_DARK, fg=TEXT,
                font=FB, anchor="w").pack(side="left")
        self._placeholder_tab(p, "DATA STATUS", [
            "• Weather: mock data based on country.",
            "• Connect OpenWeather or similar API for live data.",
        ])

    def _tab_form(self, p, m):
        self._sec(p, "RECENT FORM GUIDE")
        for side, team, form, avg in [
            ("HOME", m.get("home",""), m.get("home_form",["?","?","?","?","?"]), m.get("home_avg",1.5)),
            ("AWAY", m.get("away",""), m.get("away_form",["?","?","?","?","?"]), m.get("away_avg",1.5)),
        ]:
            c = self._card(p)
            c.pack(fill="x", pady=4)
            top = tk.Frame(c, bg=PANEL_DARK)
            top.pack(fill="x", padx=10, pady=6)
            col = CYAN if side=="HOME" else ORANGE
            tk.Label(top, text=f"{side}: {team}", bg=PANEL_DARK,
                fg=col, font=FB, anchor="w").pack(side="left")
            tk.Label(top, text=f"{avg:.1f} goals/game",
                bg=PANEL_DARK, fg=MUTED, font=FS, anchor="e").pack(side="right")
            form_row = tk.Frame(c, bg=PANEL_DARK)
            form_row.pack(fill="x", padx=10, pady=(0,6))
            for result in form:
                fc = GREEN if result=="W" else ORANGE if result=="D" else RED
                tk.Label(form_row, text=result, bg=fc, fg=TEXT,
                    font=FB, width=3, pady=4).pack(side="left", padx=2)
        self._placeholder_tab(p, "DATA STATUS", [
            "• Form: last 5 results from match data.",
            "• Extended form history available via live API.",
        ])

    def _tab_players(self, p, m):
        self._sec(p, "PLAYERS & INJURIES")
        for side, team in [("HOME", m.get("home","")), ("AWAY", m.get("away",""))]:
            c = self._card(p)
            c.pack(fill="x", pady=4)
            col = CYAN if side=="HOME" else ORANGE
            tk.Label(c, text=f"{side}: {team}", bg=PANEL_DARK,
                fg=col, font=FB, padx=10, pady=6, anchor="w").pack(fill="x")
            players = [
                ("Available","Captain and usual starter","✓ FIT"),
                ("Questionable","Hamstring concern","⚠ DOUBT"),
                ("Out","Suspended — yellow card accumulation","✗ OUT"),
            ]
            for name, note, status in players:
                row = tk.Frame(c, bg=PANEL_DARK)
                row.pack(fill="x", padx=10, pady=2)
                sc = GREEN if "FIT" in status else YELLOW if "DOUBT" in status else RED
                tk.Label(row, text=status, bg=PANEL_DARK, fg=sc,
                    font=FM, width=8, anchor="w").pack(side="left")
                tk.Label(row, text=name, bg=PANEL_DARK, fg=TEXT,
                    font=FB, width=16, anchor="w").pack(side="left")
                tk.Label(row, text=note, bg=PANEL_DARK, fg=MUTED,
                    font=FS, anchor="w").pack(side="left")
        self._placeholder_tab(p, "DATA STATUS", [
            "• Player data: placeholder.",
            "• Connect live lineups/injuries API for real data.",
        ])

    def _tab_video(self, p, m):
        self._sec(p, "VIDEO LINKS")
        tk.Label(p,
            text="Video links open in your browser. No illegal streams or betting sites.",
            bg=PANEL, fg=MUTED, font=FS, anchor="w", pady=4).pack(fill="x")
        videos = [
            ("YouTube Preview",    f"{m.get('home','')} vs {m.get('away','')} — Match Preview",  "preview"),
            ("YouTube H2H",        "Head to Head History — Top Moments",                           "h2h"),
            ("YouTube Tactics",    f"{m.get('home','')} Tactical Breakdown",                      "tactics"),
            ("Press Conference",   f"{m.get('home','')} Manager Pre-Match Presser",               "presser"),
            ("Stats Video",        "Match Stats and Predictions Breakdown",                        "stats"),
        ]
        for label, title, vtype in videos:
            card = tk.Frame(p, bg=PANEL_DARK,
                highlightbackground=BORDER, highlightthickness=1)
            card.pack(fill="x", pady=3)
            row = tk.Frame(card, bg=PANEL_DARK)
            row.pack(fill="x", padx=10, pady=6)
            tk.Label(row, text=f"[{label}]", bg=PANEL_DARK, fg=CYAN,
                font=FM, width=20, anchor="w").pack(side="left")
            tk.Label(row, text=title, bg=PANEL_DARK, fg=TEXT,
                font=FS, anchor="w").pack(side="left", fill="x", expand=True)
            tk.Button(row, text="Open →", bg="#243244", fg=CYAN,
                activebackground="#334155", relief="flat", font=FS, padx=8,
                command=lambda t=title: self._open_youtube(t)).pack(side="right", padx=4)

    def _open_youtube(self, query):
        """Open YouTube search in browser."""
        import webbrowser, urllib.parse
        q = urllib.parse.quote_plus(query)
        webbrowser.open(f"https://www.youtube.com/results?search_query={q}")

    def _tab_trivia(self, p, m):
        """Interactive trivia with 4-choice questions."""
        self._sec(p, "SOCCER TRIVIA")
        if not hasattr(self, "_trivia_score"):
            self._trivia_score = {"correct": 0, "total": 0}
        if not hasattr(self, "_trivia_answered"):
            self._trivia_answered = {}
        if not hasattr(self, "_trivia_q_index"):
            self._trivia_q_index = 0

        questions = [
            ("Which club has won the most UEFA Champions League titles?",
             ["Real Madrid","Barcelona","Bayern Munich","AC Milan"], 0),
            (f"What is {m.get('home','Team')}'s nickname?",
             ["The Citizens","The Reds","The Gunners","The Blues"], 0),
            ("In which year was the FIFA World Cup first held?",
             ["1930","1934","1938","1950"], 0),
            ("Which country hosted the 2022 FIFA World Cup?",
             ["Russia","Brazil","Qatar","UAE"], 2),
            ("How many players are on a soccer team during a match?",
             ["10","11","12","9"], 1),
            ("What is the maximum number of substitutes allowed in modern soccer?",
             ["3","4","5","6"], 2),
            ("Which player has won the most Ballon d'Or awards?",
             ["Cristiano Ronaldo","Lionel Messi","Ronaldo Nazário","Zinedine Zidane"], 1),
            ("What does 'VAR' stand for?",
             ["Video Assistant Referee","Visual Accuracy Review","Verified Action Ruling","Video Analysis Room"], 0),
        ]

        # Score display
        sc_row = tk.Frame(p, bg=PANEL)
        sc_row.pack(fill="x", pady=(0,8))
        sc = self._trivia_score
        tk.Label(sc_row,
            text=f"Score: {sc['correct']}/{sc['total']}  ({int(sc['correct']/max(sc['total'],1)*100)}% correct)",
            bg=PANEL, fg=CYAN, font=FB, anchor="w").pack(side="left", padx=8)
        tk.Button(sc_row, text="Next Question →", bg=CYAN_DARK, fg=TEXT,
            relief="flat", font=FB, padx=10, pady=4,
            command=lambda: self._trivia_next(p, m, questions)).pack(side="right", padx=8)
        tk.Button(sc_row, text="Reset", bg=GRAY_BTN, fg=TEXT,
            relief="flat", font=FS, padx=8, pady=4,
            command=lambda: self._trivia_reset(p, m)).pack(side="right", padx=4)

        q_idx = self._trivia_q_index % len(questions)
        self._render_trivia_question(p, m, questions, q_idx)

    def _render_trivia_question(self, p, m, questions, q_idx):
        """Render one trivia question with 4 answer buttons."""
        # Clear only question area (not score row) — simple: just add below
        question, answers, correct = questions[q_idx]
        q_key = q_idx
        answered = self._trivia_answered.get(q_key)

        qc = self._card(p)
        qc.pack(fill="x", pady=4)
        tk.Label(qc, text=f"Q{q_idx+1}: {question}", bg=PANEL_DARK, fg=TEXT,
            font=FB, anchor="w", justify="left", padx=10, pady=8,
            wraplength=600).pack(fill="x")

        for i, ans in enumerate(answers):
            if answered is not None:
                if i == correct:
                    bg, fg = GREEN_DARK, TEXT
                elif i == answered and answered != correct:
                    bg, fg = RED_DARK, TEXT
                else:
                    bg, fg = "#1e293b", MUTED
            else:
                bg, fg = "#243244", TEXT
            tk.Button(qc, text=f"  {chr(65+i)}.  {ans}",
                bg=bg, fg=fg, activebackground="#334155",
                relief="flat", font=FS, anchor="w", padx=12, pady=6,
                command=lambda ci=i, qk=q_key: self._trivia_answer(p, m, questions, q_idx, ci, qk)
            ).pack(fill="x", padx=8, pady=2)

        if answered is not None:
            result_text = "✓ Correct!" if answered == correct else f"✗ Answer: {answers[correct]}"
            result_col  = GREEN if answered == correct else RED
            tk.Label(qc, text=result_text, bg=PANEL_DARK, fg=result_col,
                font=FB, padx=10, pady=6).pack(fill="x")

    def _trivia_answer(self, p, m, questions, q_idx, choice, q_key):
        _, _, correct = questions[q_idx]
        if q_key not in self._trivia_answered:
            self._trivia_answered[q_key] = choice
            self._trivia_score["total"] += 1
            if choice == correct:
                self._trivia_score["correct"] += 1
            # Refresh tab to show result
            self.set_tab("Trivia")

    def _trivia_next(self, p, m, questions):
        self._trivia_q_index = (self._trivia_q_index + 1) % len(questions)
        self.set_tab("Trivia")

    def _trivia_reset(self, p, m):
        self._trivia_score    = {"correct": 0, "total": 0}
        self._trivia_answered = {}
        self._trivia_q_index  = 0
        self.set_tab("Trivia")

    # ──────────────────────────────────────────
    # User Prediction Game (accessible from Chat tab / new button)
    # ──────────────────────────────────────────

    def _show_predictions_window(self):
        """Open prediction game as a popup window."""
        if hasattr(self, "_pred_win") and self._pred_win and self._pred_win.winfo_exists():
            self._pred_win.lift()
            return
        win = tk.Toplevel(self.root)
        win.title("User Predictions — Soccer Edge Engine")
        win.geometry("700x600")
        win.configure(bg=BG)
        self._pred_win = win
        self._build_predictions_ui(win)

    def _build_predictions_ui(self, win):
        """Build prediction game UI inside a window."""
        if not hasattr(self, "_user_preds"):
            self._user_preds = []

        tk.Label(win, text="USER PREDICTIONS", bg=BG, fg=CYAN,
            font=("Consolas",14,"bold"), anchor="w").pack(fill="x", padx=12, pady=8)
        tk.Label(win,
            text="Predict for fun — track your record against the engine. Paper only.",
            bg=BG, fg=MUTED, font=FS, anchor="w").pack(fill="x", padx=12)

        m = self.current_match
        tk.Label(win, text=f"Selected: {m.get('home','')} vs {m.get('away','')}",
            bg=PANEL_DARK, fg=TEXT, font=FB, anchor="w",
            padx=12, pady=6).pack(fill="x", pady=(8,4))

        # Prediction form
        form = tk.Frame(win, bg=PANEL)
        form.pack(fill="x", padx=12, pady=4)

        pred_var  = tk.StringVar(value="")
        score_var = tk.StringVar(value="")

        tk.Label(form, text="Your Pick:", bg=PANEL, fg=CYAN,
            font=FB, anchor="w").pack(fill="x", padx=8, pady=(8,2))
        picks = tk.Frame(form, bg=PANEL)
        picks.pack(fill="x", padx=8)
        for label in [m.get("home","Home"), "Draw", m.get("away","Away")]:
            tk.Radiobutton(picks, text=label, variable=pred_var, value=label,
                bg=PANEL, fg=TEXT, selectcolor=PANEL_DARK,
                activebackground=PANEL, font=FS).pack(side="left", padx=8)

        tk.Label(form, text="Exact Score (optional):", bg=PANEL, fg=CYAN,
            font=FB, anchor="w").pack(fill="x", padx=8, pady=(8,2))
        score_entry = tk.Entry(form, textvariable=score_var, bg=PANEL_DARK,
            fg=TEXT, insertbackground=TEXT, relief="flat", font=FS)
        score_entry.pack(fill="x", padx=8, pady=(0,8))

        def submit():
            pick = pred_var.get().strip()
            if not pick:
                return
            engine_rec = self._get_engine_pick(m)
            self._user_preds.append({
                "match":   f"{m.get('home','')} vs {m.get('away','')}",
                "pick":    pick,
                "score":   score_var.get().strip(),
                "engine":  engine_rec,
                "status":  "Pending",
                "correct": None,
            })
            score_var.set("")
            pred_var.set("")
            _refresh_log()

        tk.Button(form, text="Submit Prediction", bg=GREEN_DARK, fg=TEXT,
            activebackground=GREEN_DARK, relief="flat", font=FB,
            pady=8, command=submit).pack(fill="x", padx=8, pady=(0,8))

        # Prediction log
        tk.Label(win, text="YOUR PREDICTIONS", bg=BG, fg=CYAN,
            font=FB, anchor="w").pack(fill="x", padx=12, pady=(8,2))

        log_frame = tk.Frame(win, bg=PANEL_DARK)
        log_frame.pack(fill="both", expand=True, padx=12, pady=(0,8))

        def _refresh_log():
            for w in log_frame.winfo_children():
                w.destroy()
            if not self._user_preds:
                tk.Label(log_frame, text="No predictions yet.",
                    bg=PANEL_DARK, fg=MUTED, font=FS, pady=12).pack()
                return
            total   = len(self._user_preds)
            correct = sum(1 for p in self._user_preds if p["correct"] is True)
            tk.Label(log_frame,
                text=f"Total: {total}  Correct: {correct}  Win rate: {int(correct/max(total,1)*100)}%",
                bg=PANEL_DARK, fg=CYAN, font=FM, anchor="w",
                padx=8, pady=4).pack(fill="x")
            for pred in reversed(self._user_preds[-10:]):
                row = tk.Frame(log_frame, bg=ROW)
                row.pack(fill="x", pady=1)
                sc = GREEN if pred["correct"] else RED if pred["correct"] is False else MUTED
                tk.Label(row, text=pred["match"][:24], bg=ROW, fg=TEXT,
                    font=FS, width=24, anchor="w").pack(side="left", padx=4, pady=3)
                tk.Label(row, text=f"Pick: {pred['pick']}", bg=ROW, fg=CYAN,
                    font=FM, width=16, anchor="w").pack(side="left")
                tk.Label(row, text=f"Engine: {pred['engine']}", bg=ROW, fg=ORANGE,
                    font=FM, width=16, anchor="w").pack(side="left")
                tk.Label(row, text=pred["status"], bg=ROW, fg=sc,
                    font=FM, anchor="w").pack(side="left")

        _refresh_log()

    def _get_engine_pick(self, m):
        """Get current engine recommendation for a match."""
        odds = m.get("odds",(2.0,3.5,4.0))
        pred = m.get("pred",(33,33,34))
        h, d, a = pred
        if h >= d and h >= a:
            return m.get("home","Home")
        elif a >= d:
            return m.get("away","Away")
        return "Draw"

    # ──────────────────────────────────────────
    # Team vs Team Comparison Tool
    # ──────────────────────────────────────────

    def _show_team_comparison(self):
        """Open team comparison tool as a popup."""
        if hasattr(self, "_cmp_win") and self._cmp_win and self._cmp_win.winfo_exists():
            self._cmp_win.lift()
            return
        win = tk.Toplevel(self.root)
        win.title("Team vs Team Comparison — Soccer Edge Engine")
        win.geometry("800x650")
        win.configure(bg=BG)
        self._cmp_win = win
        self._build_comparison_ui(win)

    def _build_comparison_ui(self, win):
        tk.Label(win, text="TEAM vs TEAM COMPARISON", bg=BG, fg=CYAN,
            font=("Consolas",14,"bold"), anchor="w").pack(fill="x", padx=12, pady=8)
        tk.Label(win,
            text="Compare any two teams. Uses local data — real historical data in next phase.",
            bg=BG, fg=MUTED, font=FS, anchor="w").pack(fill="x", padx=12)

        # Search row
        search_f = tk.Frame(win, bg=PANEL)
        search_f.pack(fill="x", padx=12, pady=8)
        search_f.grid_columnconfigure(1, weight=1)
        search_f.grid_columnconfigure(3, weight=1)

        team_a_var = tk.StringVar(value=self.current_match.get("home","Team A"))
        team_b_var = tk.StringVar(value=self.current_match.get("away","Team B"))

        tk.Label(search_f, text="Team A:", bg=PANEL, fg=CYAN, font=FB,
            anchor="w").grid(row=0, column=0, padx=8, pady=8)
        tk.Entry(search_f, textvariable=team_a_var, bg=PANEL_DARK, fg=TEXT,
            insertbackground=TEXT, relief="flat", font=FS).grid(
            row=0, column=1, sticky="ew", padx=4)
        tk.Label(search_f, text="Team B:", bg=PANEL, fg=ORANGE, font=FB,
            anchor="w").grid(row=0, column=2, padx=8)
        tk.Entry(search_f, textvariable=team_b_var, bg=PANEL_DARK, fg=TEXT,
            insertbackground=TEXT, relief="flat", font=FS).grid(
            row=0, column=3, sticky="ew", padx=4)

        results_f = tk.Frame(win, bg=BG)
        results_f.pack(fill="both", expand=True, padx=12, pady=4)

        def compare():
            for w in results_f.winfo_children():
                w.destroy()
            a = team_a_var.get().strip() or "Team A"
            b = team_b_var.get().strip() or "Team B"
            m = self.current_match

            # Use match data if teams match, else generate mock stats
            if a == m.get("home","") and b == m.get("away",""):
                ha, hb = m.get("home_avg",1.5), m.get("away_avg",1.5)
                fa, fb = m.get("home_form",["W","D","L","W","D"]), m.get("away_form",["L","W","W","D","L"])
            else:
                import random
                random.seed(hash(a+b) % 9999)
                ha, hb = round(random.uniform(0.9,2.5),1), round(random.uniform(0.9,2.5),1)
                results = ["W","D","L"]
                fa = [random.choice(results) for _ in range(5)]
                fb = [random.choice(results) for _ in range(5)]

            # Header
            hdr = tk.Frame(results_f, bg=PANEL_DARK)
            hdr.pack(fill="x", pady=4)
            hdr.grid_columnconfigure(0, weight=1)
            hdr.grid_columnconfigure(2, weight=1)
            tk.Label(hdr, text=a, bg=PANEL_DARK, fg=CYAN, font=("Segoe UI",14,"bold"),
                anchor="center").grid(row=0, column=0, sticky="ew", pady=8)
            tk.Label(hdr, text="vs", bg=PANEL_DARK, fg=MUTED, font=FT,
                anchor="center").grid(row=0, column=1, padx=20)
            tk.Label(hdr, text=b, bg=PANEL_DARK, fg=ORANGE, font=("Segoe UI",14,"bold"),
                anchor="center").grid(row=0, column=2, sticky="ew", pady=8)

            # Stats rows
            stats_frame = tk.Frame(results_f, bg=BG)
            stats_frame.pack(fill="x", pady=4)

            def stat_row(label, va, vb, highlight=False):
                r = tk.Frame(stats_frame, bg=ROW if not highlight else "#1a2f1a")
                r.pack(fill="x", pady=1)
                r.grid_columnconfigure(0, weight=1)
                r.grid_columnconfigure(2, weight=1)
                ca = GREEN if str(va) > str(vb) else MUTED
                cb = GREEN if str(vb) > str(va) else MUTED
                tk.Label(r, text=str(va), bg=r.cget("bg"), fg=ca,
                    font=FB, anchor="e").grid(row=0, column=0, sticky="ew", padx=10, pady=6)
                tk.Label(r, text=label, bg=r.cget("bg"), fg=TEXT,
                    font=FS, anchor="center").grid(row=0, column=1, padx=20)
                tk.Label(r, text=str(vb), bg=r.cget("bg"), fg=cb,
                    font=FB, anchor="w").grid(row=0, column=2, sticky="ew", padx=10)

            stat_row("Goals per game", ha, hb, True)
            a_wins = fa.count("W"); b_wins = fb.count("W")
            stat_row("Recent wins (last 5)", a_wins, b_wins)
            a_pts = a_wins*3 + fa.count("D"); b_pts = b_wins*3 + fb.count("D")
            stat_row("Recent points", a_pts, b_pts)
            stat_row("Recent form",
                " ".join(fa), " ".join(fb))

            # H2H note
            note = tk.Label(results_f,
                text="Note: No direct head-to-head found. Showing statistical comparison from local data.",
                bg=PANEL_DARK, fg=MUTED, font=FS, anchor="w",
                padx=10, pady=8, wraplength=750, justify="left")
            note.pack(fill="x", pady=8)

        tk.Button(search_f, text="Compare →", bg=CYAN_DARK, fg=TEXT,
            activebackground=CYAN_DARK, relief="flat", font=FB, padx=12, pady=6,
            command=compare).grid(row=0, column=4, padx=(8,4))
        compare()  # auto-run on open

    # ──────────────────────────────────────────
    # Main loop
    # ──────────────────────────────────────────

    def mainloop(self):
        self.root.mainloop()


if __name__ == "__main__":
    SoccerEdgeApp().mainloop()
