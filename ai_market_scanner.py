"""
ai_market_scanner.py  —  AI Market Scanner screen (paper mode only)
Fixed: blank page caused by PanedWindow sash race condition on first show.
Fix: removed apply_layout from __init__, call it only after frame is mapped.
AUTO TRADING = OFF always.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime

from market_scanner_engine import run_scanner, PaperTrade, RiskGuard, calculate_contracts_for_budget, calculate_kalshi_fee
from market_connectors import DataLayer
from market_models import format_price, format_cents
from crypto_price_connectors import CryptoPriceDataLayer, parse_crypto_market_title
from scanner_watchlist import ScannerWatchlist, WatchlistEntry
from paper_trade_engine import PaperTradeEngine, contracts_for_budget, kalshi_fee, breakeven_price
import scanner_config as cfg

# ── Theme ──────────────────────────────────────────────────────────────────
BG         = "#0b1120"
TOP        = "#111827"
PANEL      = "#1e293b"
PANEL_DARK = "#0f172a"
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

FS = ("Segoe UI", 9)
FB = ("Segoe UI", 10, "bold")
FM = ("Consolas", 9)

SIG_COLORS = {
    "STRONG ENTRY": {"bg": "#14532d", "fg": "#4ade80"},
    "ENTRY":        {"bg": "#166534", "fg": GREEN},
    "WATCH":        {"bg": "#78350f", "fg": YELLOW},
    "AVOID":        {"bg": "#7f1d1d", "fg": "#fca5a5"},
    "NO TRADE":     {"bg": "#1e293b", "fg": MUTED},
    "DATA NEEDED":  {"bg": "#1e2a3a", "fg": "#60a5fa"},
}

SCANNER_LAYOUTS = {
    "default":      (0.18, 0.73, 0.75),
    "focus_center": (0.10, 0.85, 0.75),
    "focus_left":   (0.30, 0.70, 0.75),
    "focus_right":  (0.15, 0.55, 0.75),
    "equal":        (0.25, 0.67, 0.67),
    "log_focus":    (0.18, 0.73, 0.50),
}

MODE_COLORS = {
    "MOCK":              CYAN,
    "KALSHI_PUBLIC":     GREEN,
    "KALSHI_AUTH_TEST":  "#10b981",   # emerald
    "HYBRID":            ORANGE,
    "KALSHI_AUTH":       GREEN,
    "MOCK (fallback)":   YELLOW,
    "MOCK (hybrid fallback)": YELLOW,
    "MOCK (error fallback)":  RED,
    "KALSHI_PUBLIC (auth fallback)": YELLOW,
}


class AIMarketScannerFrame(tk.Frame):
    """
    Drop-in scanner frame. Blank-page fix:
    - No layout calls in __init__.
    - apply_layout() called via bind("<Map>") = fires once when frame is first shown.
    - Fallback: if data load fails, shows error message in table.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)

        self.data_layer      = DataLayer(log_fn=self._safe_log)
        self.risk_guard      = RiskGuard()
        self.signals         = []
        self.paper_trades    = []
        self.selected_signal = None
        self.scan_job        = None
        self.scanning        = False
        self._layout_done    = False      # ← key: only apply layout once
        self._log_queue      = []         # buffer logs before widget exists
        self._log_text       = None       # widget ref, may be None early

        self._v_pane = None
        self._h_pane = None
        self._last_ob_status = "Not loaded"

        # Crypto reference
        self._crypto_layer   = CryptoPriceDataLayer(
            preferred=cfg.CRYPTO_PRICE_SOURCE, log_fn=self._safe_log)
        self._crypto_prices  = {}   # {symbol: CryptoPriceSnapshot}
        self._crypto_labels  = {}   # widget refs for crypto panel

        # Watchlist engine
        self._watchlist      = ScannerWatchlist(log_fn=self._safe_log)

        # Paper trade engine (replaces simple list)
        self._paper_engine   = PaperTradeEngine(log_fn=self._safe_log)
        self._perf_labels    = {}   # widget refs for performance panel
        self._selected_trade = None # currently selected paper trade id

        # Maximize / restore system
        self._maximized_panel = None      # name of currently maximized panel, or None
        self._max_frame       = None      # overlay frame (built lazily)
        self._panel_btns      = {}        # name → maximize button widget ref

        # Filter vars
        self.v_data_mode  = tk.StringVar(value=cfg.effective_mode())
        self.v_category   = tk.StringVar(value="All")
        self.v_timeframe  = tk.StringVar(value="Live")
        self.v_min_edge   = tk.DoubleVar(value=cfg.SCANNER_MIN_EDGE)
        self.v_max_spread = tk.DoubleVar(value=cfg.SCANNER_MAX_SPREAD)
        self.v_max_size   = tk.DoubleVar(value=cfg.SCANNER_MAX_TRADE_SIZE)
        self.v_daily_loss = tk.DoubleVar(value=cfg.SCANNER_DAILY_LOSS)

        self._status_labels = {}

        self._build()

        # Bind to Map event — fires when frame is first shown/mapped
        # This is the correct place to call layout and load data
        self.bind("<Map>", self._on_first_show)

    def _on_first_show(self, _event=None):
        """Called once when the frame is first made visible."""
        self.unbind("<Map>")       # fire only once
        self.after(50, self._startup)

    def _startup(self):
        """Delayed startup: apply layout then load data."""
        self.apply_layout("default")
        self.after(100, self._initial_load)

    # ── Layout ────────────────────────────────────────────────────────────

    def apply_layout(self, preset):
        if not self._h_pane or not self._v_pane:
            return
        try:
            self.update_idletasks()
            hw = self._h_pane.winfo_width()
            vh = self._v_pane.winfo_height()
            if hw <= 10 or vh <= 10:
                # Not ready yet — retry after more time
                self.after(150, lambda: self.apply_layout(preset))
                return
            lf, cf, vf = SCANNER_LAYOUTS.get(preset, SCANNER_LAYOUTS["default"])
            self._h_pane.sash_place(0, int(hw * lf), 0)
            self._h_pane.sash_place(1, int(hw * cf), 0)
            self._v_pane.sash_place(0, 0, int(vh * vf))
        except Exception as e:
            print(f"[scanner layout] {e}")

    # ── Build ─────────────────────────────────────────────────────────────

    def _build(self):
        self.grid_rowconfigure(0, weight=0)   # header fixed height
        self.grid_rowconfigure(1, weight=1)   # body expands
        self.grid_columnconfigure(0, weight=1)
        try:
            self._build_header()
            self._build_body()
        except Exception as exc:
            import traceback
            traceback.print_exc()
            # Show visible error panel instead of blank page
            err_frame = tk.Frame(self, bg="#1a0000",
                highlightbackground="#ef4444", highlightthickness=2)
            err_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
            tk.Label(err_frame,
                text="AI Scanner failed to load",
                bg="#1a0000", fg="#ef4444",
                font=("Segoe UI", 14, "bold"), pady=20).pack()
            tk.Label(err_frame,
                text=str(exc),
                bg="#1a0000", fg="#fca5a5",
                font=("Consolas", 9), wraplength=600,
                justify="left", padx=20).pack()
            tk.Label(err_frame,
                text="Check terminal for full traceback.",
                bg="#1a0000", fg="#94a3b8",
                font=("Segoe UI", 9), pady=10).pack()

    def _build_header(self):
        hdr = tk.Frame(self, bg=TOP)
        hdr.grid(row=0, column=0, sticky="ew")

        left = tk.Frame(hdr, bg=TOP)
        left.pack(side="left", padx=12, pady=8)
        tk.Label(left, text="AI MARKET SCANNER", bg=TOP, fg=CYAN,
            font=("Consolas", 14, "bold")).pack(anchor="w")
        tk.Label(left,
            text="Fee-adjusted edge scanner — paper mode only, auto trading OFF",
            bg=TOP, fg=MUTED, font=FS).pack(anchor="w")

        chips = tk.Frame(hdr, bg=TOP)
        chips.pack(side="right", padx=14, pady=8)

        self._mode_chip = tk.Label(chips,
            text=f"MODE: {cfg.effective_mode()}",
            bg=PANEL_DARK, fg=CYAN, font=FM, padx=10, pady=4,
            highlightbackground=BORDER, highlightthickness=1)
        self._mode_chip.pack(side="left", padx=4)

        for text, col in [
            ("AUTO TRADING: OFF", RED),
            ("PAPER ONLY", YELLOW),
            ("RISK GUARD: ON", GREEN),
        ]:
            tk.Label(chips, text=text, bg=PANEL_DARK, fg=col,
                font=FM, padx=10, pady=4,
                highlightbackground=BORDER, highlightthickness=1,
            ).pack(side="left", padx=4)

    def _build_body(self):
        self._v_pane = tk.PanedWindow(self, orient="vertical",
            bg="#22d3ee", sashwidth=8, sashrelief="raised",
            opaqueresize=True, showhandle=True, handlesize=12, handlepad=80)
        self._v_pane.grid(row=1, column=0, sticky="nsew")

        top_area    = tk.Frame(self._v_pane, bg=BG)
        bottom_area = tk.Frame(self._v_pane, bg=BG)
        self._v_pane.add(top_area,    minsize=200, sticky="nsew")
        self._v_pane.add(bottom_area, minsize=80,  sticky="nsew")

        top_area.grid_rowconfigure(0, weight=1)
        top_area.grid_columnconfigure(0, weight=1)

        self._h_pane = tk.PanedWindow(top_area, orient="horizontal",
            bg="#22d3ee", sashwidth=8, sashrelief="raised",
            opaqueresize=True, showhandle=True, handlesize=12, handlepad=80)
        self._h_pane.grid(row=0, column=0, sticky="nsew")

        lf = tk.Frame(self._h_pane, bg=BG)
        cf = tk.Frame(self._h_pane, bg=BG)
        rf = tk.Frame(self._h_pane, bg=BG)

        for f in (lf, cf, rf, bottom_area):
            f.grid_rowconfigure(0, weight=1)
            f.grid_columnconfigure(0, weight=1)

        self._h_pane.add(lf, minsize=150, sticky="nsew")
        self._h_pane.add(cf, minsize=300, sticky="nsew")
        self._h_pane.add(rf, minsize=160, sticky="nsew")

        self._build_left(lf)
        self._build_center(cf)
        self._build_right(rf)
        self._build_bottom(bottom_area)

    def _panel(self, parent, title, panel_key=None):
        """Create a titled panel with optional maximize button."""
        outer = tk.Frame(parent, bg=BG,
            highlightbackground=BORDER, highlightthickness=1)
        outer.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        outer.grid_rowconfigure(1, weight=1)
        outer.grid_columnconfigure(0, weight=1)
        # Header row
        hdr = tk.Frame(outer, bg=BG)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)
        tk.Label(hdr, text=title, bg=BG, fg=CYAN,
            font=FB, padx=8, pady=5, anchor="w").grid(row=0, column=0, sticky="w")
        if panel_key:
            self._max_btn(hdr, panel_key).grid(row=0, column=1, padx=4)
        body = tk.Frame(outer, bg=PANEL)
        body.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        return body

    # ── LEFT: Filters + status ─────────────────────────────────────────────

    def _build_left(self, p):
        body = self._panel(p, "FILTERS & SETTINGS", panel_key="filters_settings")
        body.grid_rowconfigure(99, weight=1)

        def row_w(label, widget_fn):
            f = tk.Frame(body, bg=PANEL)
            f.pack(fill="x", padx=8, pady=3)
            tk.Label(f, text=label, bg=PANEL, fg=CYAN, font=FS, anchor="w").pack(fill="x")
            widget_fn(f).pack(fill="x", pady=2)

        def combo(var, vals):
            return lambda par: ttk.Combobox(par, textvariable=var,
                values=vals, state="readonly", font=FS, height=8)

        def spin(var, lo, hi, inc):
            return lambda par: tk.Spinbox(par, textvariable=var,
                from_=lo, to=hi, increment=inc,
                bg=PANEL_DARK, fg=TEXT, buttonbackground=PANEL_DARK,
                insertbackground=TEXT, relief="flat", font=FS)

        row_w("Data Mode", combo(self.v_data_mode,
            ["MOCK", "KALSHI_PUBLIC", "KALSHI_AUTH_TEST", "HYBRID"]))
        self.v_data_mode.trace_add("write", self._on_mode_change)

        row_w("Category", combo(self.v_category,
            ["All","Crypto","Sports","Politics","Economics","Soccer","Watchlist"]))
        row_w("Timeframe", combo(self.v_timeframe,
            ["Live","15 min","1 hour","Today","Upcoming"]))

        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", padx=8, pady=6)

        row_w("Min Edge (cents)",    spin(self.v_min_edge,   0, 50,  1))
        row_w("Max Spread (cents)",  spin(self.v_max_spread, 0, 20,  1))
        row_w("Max Trade Size ($)",  spin(self.v_max_size,   1, 100, 1))
        row_w("Daily Loss Limit ($)",spin(self.v_daily_loss, 5, 200, 5))

        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", padx=8, pady=6)

        for text, bg, cmd in [
            ("Refresh Data",       CYAN_DARK,  self._refresh),
            ("Test Kalshi Auth",   "#0e7490",  self._test_auth),
            ("Load Orderbook",     PURPLE,     self._load_orderbook_for_selected),
            ("Start Paper Scan",   GREEN_DARK, self._start_scan),
            ("Stop Scan",          GRAY_BTN,   self._stop_scan),
            ("Reset Filters",      RED_DARK,   self._reset_filters),
        ]:
            tk.Button(body, text=text, bg=bg, fg=TEXT,
                activebackground=bg, relief="flat", font=FB,
                pady=6, command=cmd).pack(fill="x", padx=8, pady=2)

        # Status box
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", padx=8, pady=6)
        tk.Label(body, text="SOURCE STATUS", bg=PANEL, fg=CYAN,
            font=FB, anchor="w").pack(fill="x", padx=8, pady=2)

        sf = tk.Frame(body, bg=PANEL_DARK)
        sf.pack(fill="x", padx=8, pady=4)
        for lbl, key in [
            ("Data Mode",     "data_mode"),
            ("Kalshi Env",    "kalshi_env"),
            ("Last Update",   "last_update"),
            ("Market Data",   "market_data"),
            ("Kalshi Public", "kalshi_public"),
            ("Kalshi Auth",   "kalshi_auth_live"),
            ("Orderbook",     "orderbook_status"),
            ("Auto Trading",  "auto_trading"),
            ("Risk Guard",    "risk_guard"),
        ]:
            row = tk.Frame(sf, bg=PANEL_DARK)
            row.pack(fill="x", padx=6, pady=1)
            tk.Label(row, text=lbl, bg=PANEL_DARK, fg=MUTED,
                font=FS, width=13, anchor="w").pack(side="left")
            vl = tk.Label(row, text="—", bg=PANEL_DARK, fg=TEXT, font=FM, anchor="w")
            vl.pack(side="left")
            self._status_labels[key] = vl

        tk.Label(body,
            text="AUTO TRADING: OFF\nNo real orders.",
            bg=PANEL_DARK, fg=RED, font=FM,
            justify="left", padx=8, pady=6, anchor="w").pack(fill="x", padx=8, pady=6)

        # Crypto reference source selector
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", padx=8, pady=4)
        tk.Label(body, text="CRYPTO REF SOURCE", bg=PANEL, fg=CYAN,
            font=FB, anchor="w").pack(fill="x", padx=8, pady=2)
        self.v_crypto_src = tk.StringVar(value=cfg.CRYPTO_PRICE_SOURCE)
        for label, val in [
            ("Auto",      "auto"),
            ("Mock",      "mock"),
            ("CoinGecko", "coingecko"),
            ("Binance",   "binance"),
            ("Coinbase",  "coinbase"),
        ]:
            tk.Radiobutton(body, text=label, variable=self.v_crypto_src,
                value=val, bg=PANEL, fg=TEXT, selectcolor=PANEL_DARK,
                activebackground=PANEL, font=FS,
                command=self._on_crypto_src_change).pack(anchor="w", padx=16)
        tk.Button(body, text="Refresh Crypto Prices", bg="#0e7490", fg=TEXT,
            activebackground="#0e7490", relief="flat", font=FS,
            pady=4, command=self._refresh_crypto).pack(fill="x", padx=8, pady=4)

        # Category filter
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", padx=8, pady=4)
        tk.Label(body, text="CATEGORY FILTER", bg=PANEL, fg=CYAN,
            font=FB, anchor="w").pack(fill="x", padx=8, pady=2)
        self.v_category_filter = tk.StringVar(value="All")
        for label in ["All", "Crypto", "Economics", "Politics", "Weather", "Other"]:
            tk.Radiobutton(body, text=label, variable=self.v_category_filter,
                value=label, bg=PANEL, fg=TEXT, selectcolor=PANEL_DARK,
                activebackground=PANEL, font=FS,
                command=self._on_category_filter_change).pack(anchor="w", padx=16)

        # Signal filter
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", padx=8, pady=4)
        tk.Label(body, text="SIGNAL FILTER", bg=PANEL, fg=CYAN,
            font=FB, anchor="w").pack(fill="x", padx=8, pady=2)
        self.v_signal_filter = tk.StringVar(value="All")
        for label in ["All", "Watch+", "Possible Edge", "Data Needed", "Avoid"]:
            tk.Radiobutton(body, text=label, variable=self.v_signal_filter,
                value=label, bg=PANEL, fg=TEXT, selectcolor=PANEL_DARK,
                activebackground=PANEL, font=FS,
                command=self._on_signal_filter_change).pack(anchor="w", padx=16)

    def _update_status_box(self):
        try:
            st = self.data_layer.status()
            # Add extra derived fields
            n = self.data_layer._last_count
            st["market_data"] = f"Loaded {n} markets" if n > 0 else "Not loaded"
            st["orderbook_status"] = getattr(self, "_last_ob_status", "Not loaded")

            col_map = {
                "Connected": GREEN, "Ready": GREEN, "Configured": GREEN, "ON": GREEN,
                "No key": RED, "Missing key": RED, "Missing PEM file": RED,
                "PEM not found": RED, "Auth failed": RED, "OFF": RED,
                "Not tested": MUTED, "Not loaded": MUTED, "Not Used": MUTED,
                "Failed": RED,
            }
            for key, lbl in self._status_labels.items():
                val = str(st.get(key, "—"))
                if key == "data_mode":
                    col = MODE_COLORS.get(val, CYAN)
                elif val.startswith("Loaded"):
                    col = GREEN
                else:
                    col = col_map.get(val, TEXT)
                lbl.config(text=val, fg=col)
        except Exception:
            pass

    def _on_mode_change(self, *_):
        import os
        selected = self.v_data_mode.get()
        os.environ["DATA_MODE"] = selected
        # Also patch the module-level variable
        import scanner_config as _sc
        _sc.DATA_MODE = selected.upper()
        mode = cfg.effective_mode()
        self._mode_chip.config(text=f"MODE: {mode}",
            fg=MODE_COLORS.get(mode, CYAN))
        msgs = {
            "MOCK":            "Mock mode — local sample data.",
            "KALSHI_PUBLIC":   "Kalshi public mode — no auth required. Requesting markets…",
            "KALSHI_AUTH_TEST":"Kalshi auth mode — will test RSA credentials then load markets.",
            "HYBRID":          "Hybrid mode — Kalshi public + mock rows merged.",
        }
        self._safe_log(msgs.get(selected, f"Data mode: {selected}"))
        if selected in ("KALSHI_AUTH_TEST",) and not cfg.kalshi_auth_ready():
            self._safe_log("Warning: KALSHI_API_KEY_ID or KALSHI_PRIVATE_KEY_PATH not set.")
            self._safe_log("Add them to .env — falling back to public data.")
        self._update_status_box()

    # ── CENTER: Scanner table ──────────────────────────────────────────────

    def _build_center(self, p):
        p.grid_rowconfigure(0, weight=1)
        p.grid_columnconfigure(0, weight=1)

        # ── Top: Signal Scanner table ─────────────────────────────────
        top = tk.Frame(p, bg=BG,
            highlightbackground=BORDER, highlightthickness=1)
        top.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        top.grid_rowconfigure(1, weight=1)
        top.grid_columnconfigure(0, weight=1)

        top_hdr = tk.Frame(top, bg=BG)
        top_hdr.grid(row=0, column=0, sticky="ew")
        top_hdr.grid_columnconfigure(0, weight=1)
        tk.Label(top_hdr, text="SIGNAL SCANNER", bg=BG, fg=CYAN,
            font=FB, padx=8, pady=5, anchor="w").grid(row=0, column=0, sticky="w")
        self._max_btn(top_hdr, "scanner_table").grid(row=0, column=1, padx=4)

        tf = tk.Frame(top, bg=PANEL)
        tf.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        tf.grid_rowconfigure(0, weight=1)
        tf.grid_columnconfigure(0, weight=1)

        cols = ("Market","Side","Bid","Ask","Last","Fair","Edge","Spread",
                "Fee","Break","Signal","Size $","Exit","Source")
        col_w = {"Market":120,"Side":40,"Bid":40,"Ask":40,"Last":40,
                 "Fair":40,"Edge":50,"Spread":50,"Fee":40,"Break":50,
                 "Signal":90,"Size $":55,"Exit":45,"Source":60}

        style = ttk.Style()
        style.configure("Scanner.Treeview",
            background=PANEL_DARK, foreground=TEXT,
            fieldbackground=PANEL_DARK, rowheight=24, font=FM)
        style.configure("Scanner.Treeview.Heading",
            background=PANEL, foreground=ORANGE,
            font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Scanner.Treeview",
            background=[("selected", "#1e3a5f")],
            foreground=[("selected", TEXT)])

        self.tree = ttk.Treeview(tf, columns=cols, show="headings",
            style="Scanner.Treeview", selectmode="browse")
        for col in cols:
            self.tree.heading(col, text=col,
                command=lambda c=col: self._sort_tree(c))
            self.tree.column(col, width=col_w.get(col, 60),
                anchor="center", stretch=False)
        self.tree.column("Market", anchor="w", stretch=True)

        vsb = ttk.Scrollbar(tf, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal",  command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        for sig, colors in SIG_COLORS.items():
            self.tree.tag_configure(sig.replace(" ", "_"),
                background=colors["bg"], foreground=colors["fg"])

        # NOTE: Watchlist tabs removed from center column — 
        # they caused PanedWindow layout to break (row=1 with weight=0 
        # in a PanedWindow child frame). Watchlist accessible via 
        # Add to Watchlist button in Signal Detail.

    def _build_center_tabs(self, p):
        """Bottom-center tabbed area: Watchlist, Alerts, Paper Candidates."""
        style = ttk.Style()
        style.configure("ScannerTab.TNotebook",
            background=BG, borderwidth=0)
        style.configure("ScannerTab.TNotebook.Tab",
            background=PANEL, foreground=MUTED,
            padding=[8, 4], font=FS)
        style.map("ScannerTab.TNotebook.Tab",
            background=[("selected", PANEL_DARK)],
            foreground=[("selected", CYAN)])

        nb = ttk.Notebook(p, style="ScannerTab.TNotebook")
        nb.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0,4))
        p.grid_rowconfigure(1, minsize=140)

        # Tab 1: Watchlist
        wl_frame = tk.Frame(nb, bg=PANEL_DARK)
        nb.add(wl_frame, text="  Watchlist  ")
        self._build_watchlist_tab(wl_frame)

        # Tab 2: Alerts (placeholder)
        al_frame = tk.Frame(nb, bg=PANEL_DARK)
        nb.add(al_frame, text="  Alerts  ")
        tk.Label(al_frame,
            text="Alerts — coming next phase.",
            bg=PANEL_DARK, fg=MUTED, font=FS, pady=16).pack(expand=True)

        # Tab 3: Paper Candidates (placeholder)
        pc_frame = tk.Frame(nb, bg=PANEL_DARK)
        nb.add(pc_frame, text="  Paper Candidates  ")
        tk.Label(pc_frame,
            text="Paper candidates will be auto-populated from ENTRY signals.",
            bg=PANEL_DARK, fg=MUTED, font=FS, pady=16).pack(expand=True)

    def _build_watchlist_tab(self, p):
        """Watchlist table + action buttons."""
        p.grid_rowconfigure(0, weight=1)
        p.grid_columnconfigure(0, weight=1)

        # Button row
        btn_row = tk.Frame(p, bg=PANEL_DARK)
        btn_row.pack(fill="x", padx=4, pady=2)
        for text, bg, cmd in [
            ("Remove Selected",  RED_DARK,  self._wl_remove_selected),
            ("Clear Stale",      GRAY_BTN,  self._wl_clear_stale),
        ]:
            tk.Button(btn_row, text=text, bg=bg, fg=TEXT,
                activebackground=bg, relief="flat", font=FS, padx=8, pady=3,
                command=cmd).pack(side="left", padx=2)
        # Entry count label
        self._wl_count_lbl = tk.Label(btn_row, text="0 items",
            bg=PANEL_DARK, fg=MUTED, font=FS, anchor="e")
        self._wl_count_lbl.pack(side="right", padx=8)

        # Watchlist treeview
        wl_cols = ("Market","Side","Bid","Ask","Last","Signal",
                   "Spread","Target","Ref Price","Status","Updated")
        col_w   = {"Market":130,"Side":40,"Bid":40,"Ask":40,"Last":40,
                   "Signal":90,"Spread":50,"Target":65,"Ref Price":80,
                   "Status":55,"Updated":55}

        wf = tk.Frame(p, bg=PANEL_DARK)
        wf.pack(fill="both", expand=True, padx=4, pady=2)
        wf.grid_rowconfigure(0, weight=1)
        wf.grid_columnconfigure(0, weight=1)

        self.wl_tree = ttk.Treeview(wf, columns=wl_cols,
            show="headings", style="Scanner.Treeview",
            selectmode="browse", height=4)
        for col in wl_cols:
            self.wl_tree.heading(col, text=col)
            self.wl_tree.column(col, width=col_w.get(col,55),
                anchor="center", stretch=False)
        self.wl_tree.column("Market", anchor="w", stretch=True)
        self.wl_tree.tag_configure("stale", foreground=MUTED)
        self.wl_tree.tag_configure("active", foreground=GREEN)

        wvsb = ttk.Scrollbar(wf, orient="vertical",   command=self.wl_tree.yview)
        whsb = ttk.Scrollbar(wf, orient="horizontal", command=self.wl_tree.xview)
        self.wl_tree.configure(yscrollcommand=wvsb.set, xscrollcommand=whsb.set)
        self.wl_tree.grid(row=0, column=0, sticky="nsew")
        wvsb.grid(row=0, column=1, sticky="ns")
        whsb.grid(row=1, column=0, sticky="ew")

        self._refresh_wl_tree()

    def _build_right(self, p):
        # Vertical split: crypto ref (top fixed) + signal detail (expands)
        p.grid_rowconfigure(0, weight=0)
        p.grid_rowconfigure(1, weight=1)
        p.grid_columnconfigure(0, weight=1)

        # ── Crypto Reference Card ──────────────────────────────────────
        cref = tk.Frame(p, bg=BG,
            highlightbackground=BORDER, highlightthickness=1)
        cref.grid(row=0, column=0, sticky="ew", padx=4, pady=(4,0))
        cref.grid_columnconfigure(0, weight=1)

        tk.Label(cref, text="CRYPTO REFERENCE", bg=BG, fg=CYAN,
            font=FB, padx=8, pady=4, anchor="w").grid(row=0, column=0, sticky="ew")

        cbody = tk.Frame(cref, bg=PANEL_DARK)
        cbody.grid(row=1, column=0, sticky="ew", padx=4, pady=(0,4))

        for sym, col in [("BTC", ORANGE), ("ETH", "#818cf8")]:
            row = tk.Frame(cbody, bg=PANEL_DARK)
            row.pack(fill="x", padx=6, pady=2)
            tk.Label(row, text=sym, bg=PANEL_DARK, fg=col,
                font=FB, width=4, anchor="w").pack(side="left")
            lbl = tk.Label(row, text="—", bg=PANEL_DARK, fg=TEXT,
                font=FM, anchor="w")
            lbl.pack(side="left", fill="x", expand=True)
            self._crypto_labels[sym] = lbl

        src_row = tk.Frame(cbody, bg=PANEL_DARK)
        src_row.pack(fill="x", padx=6, pady=(0,4))
        tk.Label(src_row, text="Source:", bg=PANEL_DARK, fg=MUTED,
            font=FS, anchor="w").pack(side="left")
        self._crypto_labels["src"] = tk.Label(src_row, text="—",
            bg=PANEL_DARK, fg=MUTED, font=FS, anchor="w")
        self._crypto_labels["src"].pack(side="left", padx=4)
        self._crypto_labels["updated"] = tk.Label(src_row, text="",
            bg=PANEL_DARK, fg=MUTED, font=FS, anchor="e")
        self._crypto_labels["updated"].pack(side="right", padx=4)

        # ── Signal Detail (expands to fill remaining space) ────────────
        outer = tk.Frame(p, bg=BG,
            highlightbackground=BORDER, highlightthickness=1)
        outer.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        outer.grid_rowconfigure(1, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        hdr_row = tk.Frame(outer, bg=BG)
        hdr_row.grid(row=0, column=0, sticky="ew")
        hdr_row.grid_columnconfigure(0, weight=1)
        tk.Label(hdr_row, text="SIGNAL DETAIL", bg=BG, fg=CYAN,
            font=FB, padx=8, pady=5, anchor="w").grid(row=0, column=0, sticky="w")
        self._max_btn(hdr_row, "signal_detail").grid(row=0, column=1, padx=4)

        self._detail_body = tk.Frame(outer, bg=PANEL)
        self._detail_body.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        self._show_detail_placeholder()

    def _show_detail_placeholder(self):
        self._clear(self._detail_body)
        tk.Label(self._detail_body,
            text="Select a market row\nto see signal detail\nand trade plan.",
            bg=PANEL, fg=MUTED, font=FS,
            justify="center", pady=30).pack(expand=True)

    def _show_signal_detail(self, sig):
        if sig is None:
            self._show_detail_placeholder()
            return
        self._clear(self._detail_body)
        p = self._detail_body

        # Scrollable canvas for detail sections
        canvas = tk.Canvas(p, bg=PANEL, highlightthickness=0)
        vsb    = tk.Scrollbar(p, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        inner = tk.Frame(canvas, bg=PANEL)
        win_id = canvas.create_window((0,0), window=inner, anchor="nw")

        def _on_resize(event):
            canvas.itemconfig(win_id, width=event.width)
        canvas.bind("<Configure>", _on_resize)
        inner.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        sc = SIG_COLORS.get(sig.signal, SIG_COLORS["NO TRADE"])

        def _section(title):
            """Labeled section header."""
            tk.Label(inner, text=title, bg=PANEL_DARK, fg=CYAN,
                font=("Segoe UI", 9, "bold"), anchor="w",
                padx=8, pady=3).pack(fill="x", pady=(6,0))
            frame = tk.Frame(inner, bg=PANEL_DARK)
            frame.pack(fill="x", padx=4, pady=(0,4))
            return frame

        def _row(parent, label, value, val_color=None):
            r = tk.Frame(parent, bg=PANEL_DARK)
            r.pack(fill="x", padx=6, pady=1)
            tk.Label(r, text=label, bg=PANEL_DARK, fg=MUTED,
                font=FS, width=14, anchor="w").pack(side="left")
            tk.Label(r, text=str(value), bg=PANEL_DARK,
                fg=val_color or TEXT, font=FM, anchor="w").pack(side="left")

        # ── Signal badge ──────────────────────────────────────────────
        tk.Label(inner, text=sig.signal, bg=sc["bg"], fg=sc["fg"],
            font=("Segoe UI", 12, "bold"), pady=6).pack(fill="x")

        # ── 1. Market Overview ────────────────────────────────────────
        f1 = _section("1  MARKET OVERVIEW")
        # Get raw_data from the signal's underlying snapshot if available
        _rd = {}
        try:
            snap = self.data_layer.get_snapshot(sig.market_id)
            if snap and snap.raw_data:
                _rd = snap.raw_data
        except Exception:
            pass

        def _rd_str(key, default="N/A"):
            v = _rd.get(key)
            return str(v).strip() if v else default

        _row(f1, "Title",        sig.market_name, TEXT)
        _row(f1, "Ticker",       sig.market_id)
        _row(f1, "Category",     sig.category)
        _row(f1, "Status",       (_rd_str("status") or
                                  getattr(snap,"status","N/A") if snap else "N/A"))
        _row(f1, "Volume",       f"{sig.volume:,}" if sig.volume else "N/A")
        _row(f1, "Open interest",f"{_rd.get('open_interest','N/A')}")
        _row(f1, "Source",       self.data_layer._last_source or "—")

        # Expiration / close times
        exp_raw  = _rd_str("close_time") or _rd_str("expiration_time")
        sett_raw = _rd_str("expected_expiration_time") or _rd_str("settlement_time")
        _row(f1, "Closes",       exp_raw)
        _row(f1, "Settlement",   sett_raw)

        # Expiration countdown
        try:
            from datetime import datetime, timezone
            def _time_left(ts_str):
                if not ts_str or ts_str == "N/A":
                    return "N/A"
                for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z",
                            "%Y-%m-%d %H:%M:%S"):
                    try:
                        if fmt.endswith("Z"):
                            dt = datetime.strptime(ts_str, fmt).replace(
                                tzinfo=timezone.utc)
                        else:
                            dt = datetime.strptime(ts_str, fmt)
                            if dt.tzinfo is None:
                                dt = dt.replace(tzinfo=timezone.utc)
                        now = datetime.now(timezone.utc)
                        diff = dt - now
                        secs = diff.total_seconds()
                        if secs < 0:
                            return "CLOSED / EXPIRED"
                        mins = int(secs // 60)
                        hrs  = mins // 60
                        if hrs >= 24:
                            return f"{hrs//24}d {hrs%24}h remaining"
                        if hrs >= 1:
                            return f"{hrs}h {mins%60}m remaining"
                        if mins < 10:
                            return f"⚠ {mins}m {int(secs%60)}s — HIGH CAUTION"
                        if mins < 60:
                            return f"⚠ CLOSING SOON — {mins}m remaining"
                        return f"{mins}m remaining"
                    except Exception:
                        continue
                return "N/A"

            tl = _time_left(exp_raw)
            tl_col = RED if "HIGH CAUTION" in tl else YELLOW if ("SOON" in tl or "CLOSED" in tl) else TEXT
            _row(f1, "Time left",  tl, tl_col)
        except Exception:
            _row(f1, "Time left",  "N/A")

        # ── 2. Kalshi Quote ───────────────────────────────────────────
        # ── 1b. Settlement Rules ─────────────────────────────────
        f1b = _section("1b  SETTLEMENT RULES")
        try:
            rules_primary   = _rd_str("rules_primary", "")
            rules_secondary = _rd_str("rules_secondary", "")
            sett_source     = (_rd_str("settlement_source") or
                               _rd_str("expiration_value", "N/A"))
            can_close_early = _rd.get("can_close_early")
            result          = _rd_str("result", "")

            if rules_primary and rules_primary != "N/A":
                preview = rules_primary[:200] + ("…" if len(rules_primary) > 200 else "")
                tk.Label(f1b, text=preview, bg=PANEL_DARK, fg=TEXT,
                    font=FS, padx=8, pady=4, justify="left",
                    wraplength=260, anchor="w").pack(fill="x")
            else:
                _row(f1b, "Rules",
                     "Settlement rules not available from current market payload.")

            _row(f1b, "Sett. source", sett_source)
            if result and result not in ("N/A", ""):
                _row(f1b, "Result", result, CYAN)
            if can_close_early is not None:
                _row(f1b, "Early close", "Yes" if can_close_early else "No")

            tk.Label(f1b,
                text="⚠  Always verify rules before real trading. Paper mode only.",
                bg="#1a1a2e", fg=YELLOW, font=FS,
                padx=8, pady=4, justify="left", wraplength=255).pack(fill="x")
        except Exception as _re:
            _row(f1b, "Error", f"Could not parse rules: {str(_re)[:50]}", MUTED)

        f2 = _section("2  KALSHI QUOTE")

        # Prices are in CENTS (0-100) — use format_cents, never format_price
        def _fc(v):
            return format_cents(v) if (v is not None and v > 0) else "N/A"

        bid  = sig.bid_price  or None
        ask  = sig.ask_price  or None
        last = sig.last_price or None

        # Infer complementary prices: YES + NO = 100c in a binary market
        yes_bid = bid  if sig.side == "YES" else (round(100 - ask, 1)  if ask  else None)
        yes_ask = ask  if sig.side == "YES" else (round(100 - bid, 1)  if bid  else None)
        no_bid  = bid  if sig.side == "NO"  else (round(100 - ask, 1)  if ask  else None)
        no_ask  = ask  if sig.side == "NO"  else (round(100 - bid, 1)  if bid  else None)

        _row(f2, "Side",     sig.side, CYAN)
        _row(f2, "YES bid",  _fc(yes_bid))
        _row(f2, "YES ask",  (_fc(yes_ask) + " *") if sig.side == "NO" and yes_ask else _fc(yes_ask))
        _row(f2, "NO  bid",  _fc(no_bid))
        _row(f2, "NO  ask",  (_fc(no_ask) + " *") if sig.side == "YES" and no_ask else _fc(no_ask))
        _row(f2, "Last",     _fc(last))
        _row(f2, "Spread",   _fc(sig.spread) if sig.spread else "N/A")
        _row(f2, "Volume",   f"{sig.volume:,}" if sig.volume else "N/A")
        _row(f2, "Liquidity",sig.liquidity)
        _row(f2, "Data qual.",sig.data_quality)
        if sig.side in ("YES","NO") and (yes_ask or no_ask):
            tk.Label(f2, text="* = inferred from complementary side",
                bg=PANEL_DARK, fg=MUTED, font=FS, padx=6).pack(anchor="w")
        # ── 3. Crypto Reference ───────────────────────────────────────
        ctx = parse_crypto_market_title(sig.market_name)
        if ctx.asset != "UNKNOWN":
            f3 = _section(f"3  CRYPTO REFERENCE ({ctx.asset})")
            snap = self._crypto_prices.get(ctx.asset)
            cur  = snap.price if snap else None
            _row(f3, f"{ctx.asset} price", snap.price_str if snap and snap.price else "N/A",
                 GREEN if snap and snap.status == "ok" else YELLOW)
            if ctx.target_price:
                _row(f3, "Target",   f"${ctx.target_price:,.2f}")
                if cur:
                    dist     = cur - ctx.target_price
                    dist_pct = dist / ctx.target_price * 100
                    dcol = GREEN if (ctx.condition=="ABOVE" and dist>0) or                                    (ctx.condition=="BELOW" and dist<0) else RED
                    _row(f3, "Distance", f"${dist:+,.2f}  ({dist_pct:+.1f}%)", dcol)
            _row(f3, "Condition",  ctx.condition)
            if ctx.expiration_text:
                _row(f3, "Expires",  ctx.expiration_text)
            _row(f3, "Ref source", snap.source if snap else "N/A")
        else:
            f3 = _section("3  CRYPTO REFERENCE")
            _row(f3, "Market type", "Non-crypto — no reference data")

        # ── 4. Orderbook ─────────────────────────────────────────────
        f4ob = _section("4  ORDERBOOK")
        try:
            ob = self.data_layer.get_orderbook(sig.market_id,
                source=self.data_layer._last_source)
            if ob:
                _row(f4ob, "YES bid/ask",
                    f"{format_price(ob.yes_best_bid)} / {format_price(ob.yes_best_ask)}")
                _row(f4ob, "NO  bid/ask",
                    f"{format_price(ob.no_best_bid)} / {format_price(ob.no_best_ask)}")
                _row(f4ob, "Depth",    str(ob.total_yes_qty + ob.total_no_qty))
                _row(f4ob, "Liquidity", ob.liquidity)
            else:
                _row(f4ob, "Status", "Click 'Load Orderbook' to fetch", YELLOW)
        except Exception:
            _row(f4ob, "Status", "N/A", MUTED)

        # ── 5. Fee / Breakeven ────────────────────────────────────────
        f4 = _section("5  FEE / BREAKEVEN")
        ask = sig.ask_price or 0
        if ask > 0:
            from paper_trade_engine import contracts_for_budget, kalshi_fee, breakeven_price
            max_size     = self.v_max_size.get()
            n            = contracts_for_budget(max_size, ask)
            fee_c        = kalshi_fee(max(n, 1), ask)
            be_c         = breakeven_price(ask, max(n, 1))
            total_cost_c = ask * max(n, 1) + fee_c
            payout_c     = 100 * max(n, 1)
            max_profit_d = round((payout_c - total_cost_c) / 100, 4)
            _row(f4, "Side",        sig.side, CYAN)
            _row(f4, "Entry ask",   format_cents(ask))
            _row(f4, "Contracts",   str(n))
            _row(f4, "Buy fee",     f"{fee_c:.0f}c  (Kalshi 7% formula)")
            _row(f4, "Total cost",  f"${round(total_cost_c/100, 4):.4f}")
            _row(f4, "Payout",      f"${round(payout_c/100, 4):.4f}  (if 100c)")
            _row(f4, "Max profit",  f"${max_profit_d:+.4f}",
                 GREEN if max_profit_d > 0 else RED)
            _row(f4, "Breakeven",   f"{be_c:.1f}c")
            _row(f4, "Max risk",    f"${max_size:.0f}  (budget)")
            if sig.spread and sig.spread > 10:
                _row(f4, "⚠ Spread", format_cents(sig.spread) + " — wide", YELLOW)
        else:
            _row(f4, "Status", "Load Orderbook first to get ask price", YELLOW)
            _row(f4, "Note",   "Fee formula: 7% × n × p × (1-p) × 100", MUTED)

        # ── 6. Signal / Trade Plan ────────────────────────────────────
        f5 = _section("6  SIGNAL")
        _row(f5, "Signal",  sig.signal, sc["fg"])
        if sig.raw_edge and sig.ask_price:
            _row(f5, "Raw edge",   f"{sig.raw_edge:+.1f}c",
                 GREEN if sig.raw_edge > 0 else RED)
            _row(f5, "Fee-adj",    f"{sig.fee_adj_edge:+.1f}c")
        else:
            _row(f5, "Edge", "N/A (no prices yet)")

        reason_lbl = tk.Label(inner, text=sig.reason, bg=PANEL_DARK,
            fg=MUTED, font=FS, padx=10, pady=6,
            justify="left", wraplength=240, anchor="w")
        reason_lbl.pack(fill="x", padx=4)

        if not cfg.ENABLE_FAIR_PRICE_MODEL:
            tk.Label(inner,
                text=("Fair price model OFF — signal stays DATA NEEDED.\n"
                      "Set ENABLE_FAIR_PRICE_MODEL=true to enable."),
                bg="#1a1a2e", fg=YELLOW, font=FS, padx=8, pady=4,
                justify="left", wraplength=240).pack(fill="x", padx=4, pady=4)

        # ── 7. Why / Explanation ──────────────────────────────────────
        f7 = _section("7  WHY / EXPLANATION")
        try:
            from market_scanner_engine import score_market
            # parse_crypto_market_title is already imported at module level
            ctx   = parse_crypto_market_title(sig.market_name)
            extra = {}
            if ctx.asset != "UNKNOWN":
                snap = self._crypto_prices.get(ctx.asset)
                if snap and snap.price and ctx.target_price:
                    dist_pct = (snap.price - ctx.target_price) / ctx.target_price * 100
                    extra["distance_pct"] = dist_pct

            scored = score_market(
                signal       = sig.signal,
                spread_cents = sig.spread or 0,
                liquidity    = sig.liquidity,
                bid          = sig.bid_price or 0,
                ask          = sig.ask_price or 0,
                fair         = sig.fair_price or 0,
                volume       = sig.volume or 0,
                extra        = extra,
            )
            # Score bar
            bar_frame = tk.Frame(f7, bg=PANEL_DARK)
            bar_frame.pack(fill="x", padx=6, pady=4)
            score_col = GREEN if scored["score"] >= 60 else YELLOW if scored["score"] >= 30 else RED
            tk.Label(bar_frame, text=f"Score: {scored['score']}/100",
                bg=PANEL_DARK, fg=score_col, font=FB, anchor="w").pack(side="left")
            tk.Label(bar_frame, text=f"  Tier: {scored['tier']}",
                bg=PANEL_DARK, fg=CYAN, font=FM, anchor="w").pack(side="left")

            def _reason_block(title, items, col):
                if not items: return
                tk.Label(f7, text=title, bg=PANEL_DARK, fg=col,
                    font=("Segoe UI", 8, "bold"), padx=6, pady=2,
                    anchor="w").pack(fill="x")
                for item in items:
                    tk.Label(f7, text=f"  • {item}", bg=PANEL_DARK, fg=MUTED,
                        font=FS, padx=8, anchor="w",
                        wraplength=255).pack(fill="x")

            _reason_block("Reasons:",      scored["reasons"],     GREEN)
            _reason_block("Risks:",        scored["risks"],       YELLOW)
            _reason_block("Data issues:",  scored["data_issues"], RED)

            tk.Label(f7, text=f"→  {scored['suggested']}",
                bg=PANEL_DARK, fg=CYAN, font=FS,
                padx=8, pady=4, anchor="w",
                wraplength=255).pack(fill="x")

        except Exception as _exc:
            reason_text = sig.reason or "No explanation available."
            tk.Label(f7, text=reason_text,
                bg=PANEL_DARK, fg=MUTED, font=FS,
                padx=8, pady=6, justify="left",
                wraplength=260, anchor="w").pack(fill="x")

        if not cfg.ENABLE_FAIR_PRICE_MODEL:
            tk.Label(f7,
                text=("Fair price model: OFF  |  Signal stays DATA NEEDED  |  "
                      "Set ENABLE_FAIR_PRICE_MODEL=true in .env to enable."),
                bg="#1a1a2e", fg=YELLOW, font=FS,
                padx=8, pady=4, justify="left",
                wraplength=260).pack(fill="x", pady=4)

        # ── 7b. Risk / Warnings ───────────────────────────────────
        f_risk = _section("7b  RISK / WARNINGS")
        try:
            warnings = []
            # Market status check
            mkt_status = _rd_str("status", "").lower()
            if mkt_status in ("closed", "settled", "finalized"):
                warnings.append(f"⛔ Market is {mkt_status.upper()} — no new positions")
            elif "soon" in tl.lower() if 'tl' in dir() else False:
                warnings.append("⚠ Market closing soon")

            # Price checks
            if not sig.ask_price or sig.ask_price <= 0:
                warnings.append("Missing ask price — load orderbook first")
            if not sig.bid_price or sig.bid_price <= 0:
                warnings.append("Missing bid price")
            if sig.spread and sig.spread > 10:
                warnings.append(f"Wide spread ({sig.spread:.0f}c) — unfavorable entry")
            if sig.liquidity == "Low":
                warnings.append("Low liquidity — fill risk")
            if sig.volume == 0:
                warnings.append("No volume data available")

            # Model
            if not sig.fair_price or sig.fair_price <= 0:
                warnings.append("Fair price model unavailable — cannot calculate edge")

            # Settlement
            rules_txt = _rd.get("rules_primary", "")
            if not rules_txt:
                warnings.append("Settlement rules not available in payload")

            # Watchlist avoid
            if self._watchlist.contains(sig.market_id):
                wl_entry = self._watchlist.get(sig.market_id)
                if wl_entry and wl_entry.avoided:
                    warnings.append("User marked this market as AVOID")

            # Crypto reference
            ctx_check = parse_crypto_market_title(sig.market_name)
            if ctx_check.asset != "UNKNOWN" and ctx_check.asset not in self._crypto_prices:
                warnings.append(f"Crypto reference ({ctx_check.asset}) not loaded")

            if warnings:
                for w in warnings:
                    col = RED if w.startswith("⛔") else YELLOW
                    tk.Label(f_risk, text=f"  • {w}", bg=PANEL_DARK, fg=col,
                        font=FS, padx=8, anchor="w", wraplength=255).pack(fill="x")
            else:
                tk.Label(f_risk, text="  No major scanner warnings.",
                    bg=PANEL_DARK, fg=GREEN, font=FS,
                    padx=8, pady=4, anchor="w").pack(fill="x")
        except Exception as _we:
            _row(f_risk, "Error", f"Warning check failed: {str(_we)[:50]}", MUTED)

        # ── 7c. Watchlist Status ───────────────────────────────────
        f_wl = _section("7c  WATCHLIST STATUS")
        try:
            if self._watchlist.contains(sig.market_id):
                wle = self._watchlist.get(sig.market_id)
                _row(f_wl, "Status",     "★ WATCHING",  CYAN)
                _row(f_wl, "Added at",   wle.time_added or "N/A")
                _row(f_wl, "Signal",     wle.signal)
                _row(f_wl, "User status",wle.status,
                     RED if wle.avoided else YELLOW if wle.status=="ALERT" else GREEN)
                if wle.last_alert_msg:
                    _row(f_wl, "Last alert", wle.last_alert_msg[:40] or "None")
                if wle.alert_note:
                    _row(f_wl, "Note",      wle.alert_note[:40])
            else:
                _row(f_wl, "Status", "Not in watchlist")
        except Exception as _wle:
            _row(f_wl, "Error", str(_wle)[:50], MUTED)

                # ── 8. Action buttons ──────────────────────────────────────────
        bf = tk.Frame(inner, bg=PANEL)
        bf.pack(fill="x", padx=4, pady=4)
        in_wl = self._watchlist.contains(sig.market_id)
        for text, bg, cmd in [
            ("Add to Watchlist"    if not in_wl else "★ In Watchlist",
             PURPLE                if not in_wl else "#1a3a5a",
             lambda s=sig: self._add_watchlist(s)),
            ("Remove from Watchlist", "#374151",  lambda s=sig: self._wl_remove(s)),
            ("Create Paper Trade", GREEN_DARK, lambda s=sig: self._paper_trade(s)),
            ("Exit Paper Trade",   "#0e7490",  self._exit_selected_paper_trade),
            ("Load Orderbook",     "#1e3a5f",  self._load_orderbook_for_selected),
            ("Mark as Avoid",      RED_DARK,   lambda s=sig: self._mark_avoid(s)),
            ("Export Signal",      GRAY_BTN,   lambda s=sig: self._export_signal(s)),
        ]:
            tk.Button(bf, text=text, bg=bg, fg=TEXT,
                activebackground=bg, relief="flat", font=FS,
                pady=5, command=cmd).pack(fill="x", pady=1)

        tk.Label(inner, text="AUTO TRADING: OFF — Paper only",
            bg="#1a0000", fg=RED, font=FS, pady=3).pack(fill="x")

    def _build_bottom(self, p):
        """
        Bottom workspace: four panels in a single horizontal row.
        No tabs. No 2x2 grid. One line, left to right:

          Paper Trades | Scanner Messages | Performance | Crypto Prices
        """
        outer = tk.Frame(p, bg=BG,
            highlightbackground=BORDER, highlightthickness=1)
        outer.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        outer.grid_rowconfigure(0, weight=1)
        # Column weights — Paper Trades and Messages wider, Perf and Crypto compact
        outer.grid_columnconfigure(0, weight=3)   # Paper Trades
        outer.grid_columnconfigure(1, weight=3)   # Scanner Messages
        outer.grid_columnconfigure(2, weight=2)   # Performance
        outer.grid_columnconfigure(3, weight=2)   # Crypto Prices

        # ── shared card builder ────────────────────────────────────────
        def _card(col, title, title_col=CYAN, panel_key=None):
            """Create one labelled panel card in the horizontal row."""
            f = tk.Frame(outer, bg=BG,
                highlightbackground=BORDER, highlightthickness=1)
            f.grid(row=0, column=col, sticky="nsew", padx=3, pady=3)
            f.grid_rowconfigure(1, weight=1)
            f.grid_columnconfigure(0, weight=1)
            hdr = tk.Frame(f, bg=BG)
            hdr.grid(row=0, column=0, sticky="ew")
            hdr.grid_columnconfigure(0, weight=1)
            tk.Label(hdr, text=title, bg=BG, fg=title_col,
                font=("Segoe UI", 8, "bold"), anchor="w",
                padx=6, pady=3).grid(row=0, column=0, sticky="w")
            if panel_key:
                self._max_btn(hdr, panel_key).grid(row=0, column=1, padx=2)
            body = tk.Frame(f, bg=PANEL_DARK)
            body.grid(row=1, column=0, sticky="nsew", padx=3, pady=(0,3))
            body.grid_rowconfigure(0, weight=1)
            body.grid_columnconfigure(0, weight=1)
            return body

        # ── Col 0: Paper Trades ────────────────────────────────────────
        pt_body = _card(0, "PAPER TRADES",   panel_key="paper_trades")
        lf = tk.Frame(pt_body, bg=PANEL_DARK)
        lf.grid(row=0, column=0, sticky="nsew")
        lf.grid_rowconfigure(1, weight=1)
        lf.grid_columnconfigure(0, weight=1)

        # Quick export button in card header
        pt_btns = tk.Frame(lf, bg=PANEL_DARK)
        pt_btns.grid(row=0, column=0, columnspan=2, sticky="ew", padx=2, pady=1)
        def _quick_export():
            try:
                path = self._paper_engine.export_csv()
                if path:
                    self._safe_log(f"Trades exported → {path}")
            except Exception as _xe:
                self._safe_log(f"Export error: {_xe}")
        tk.Button(pt_btns, text="Export CSV", bg=PANEL, fg=CYAN,
            relief="flat", font=("Segoe UI",7), padx=4, pady=1,
            command=_quick_export).pack(side="right", padx=2)
        tk.Button(pt_btns, text="Close Selected", bg=PANEL, fg=CYAN,
            relief="flat", font=("Segoe UI",7), padx=4, pady=1,
            command=self._exit_selected_paper_trade).pack(side="right", padx=2)

        pt_cols = ("Time","Market","Side","Entry","Exit","Current","Contr","Fee","P/L","Status")
        self.pt_tree = ttk.Treeview(lf, columns=pt_cols,
            show="headings", style="Scanner.Treeview", height=5)
        pt_w = {"Time":58,"Market":120,"Side":36,"Entry":40,"Exit":40,
                "Current":46,"Contr":38,"Fee":36,"P/L":52,"Status":50}
        for col in pt_cols:
            self.pt_tree.heading(col, text=col)
            self.pt_tree.column(col, width=pt_w.get(col, 50),
                anchor="center", stretch=False)
        self.pt_tree.column("Market", anchor="w", stretch=True)
        vsb2 = ttk.Scrollbar(lf, orient="vertical", command=self.pt_tree.yview)
        self.pt_tree.configure(yscrollcommand=vsb2.set)
        self.pt_tree.grid(row=0, column=0, sticky="nsew")
        vsb2.grid(row=0, column=1, sticky="ns")

        # ── Col 1: Scanner Messages ────────────────────────────────────
        msg_body = _card(1, "SCANNER MESSAGES", panel_key="scanner_messages")
        rf = tk.Frame(msg_body, bg=PANEL_DARK)
        rf.grid(row=0, column=0, sticky="nsew")
        rf.grid_rowconfigure(0, weight=1)
        rf.grid_columnconfigure(0, weight=1)

        self._log_text = tk.Text(rf, bg=PANEL_DARK, fg=GREEN,
            font=FM, state="disabled", wrap="word",
            insertbackground=TEXT, relief="flat")
        lsb = tk.Scrollbar(rf, command=self._log_text.yview)
        self._log_text.configure(yscrollcommand=lsb.set)
        self._log_text.grid(row=0, column=0, sticky="nsew")
        lsb.grid(row=0, column=1, sticky="ns")

        # ── Col 2: Performance ─────────────────────────────────────────
        perf_body = _card(2, "PERFORMANCE", title_col="#818cf8", panel_key="performance")
        self._build_perf_inline(perf_body)

        # ── Col 3: Crypto Prices ───────────────────────────────────────
        crypto_body = _card(3, "CRYPTO PRICES", title_col=ORANGE, panel_key="crypto_prices")
        self._build_crypto_inline(crypto_body)

        # Flush buffered logs after widgets exist
        for msg in self._log_queue:
            self._write_log(msg)
        self._log_queue.clear()

    def _build_crypto_inline(self, p):
        """Compact crypto price display — horizontal bottom card."""
        p.grid_rowconfigure(0, weight=1)
        p.grid_columnconfigure(0, weight=1)
        p.grid_columnconfigure(1, weight=1)

        for col_i, (sym, col) in enumerate([("BTC", ORANGE), ("ETH", "#818cf8")]):
            card = tk.Frame(p, bg=PANEL)
            card.grid(row=0, column=col_i, sticky="nsew", padx=3, pady=3)
            tk.Label(card, text=sym, bg=PANEL, fg=col, font=FB,
                pady=4, padx=6).pack(fill="x")
            keys = [
                ("Price",   f"{sym.lower()}_price"),
                ("Bid",     f"{sym.lower()}_bid"),
                ("Ask",     f"{sym.lower()}_ask"),
                ("1m chg",  f"{sym.lower()}_1m"),
                ("5m chg",  f"{sym.lower()}_5m"),
                ("Source",  f"{sym.lower()}_src"),
                ("Updated", f"{sym.lower()}_ts"),
            ]
            for label, key in keys:
                row = tk.Frame(card, bg=PANEL)
                row.pack(fill="x", padx=6, pady=1)
                tk.Label(row, text=label, bg=PANEL, fg=MUTED,
                    font=FS, width=7, anchor="w").pack(side="left")
                lbl = tk.Label(row, text="—", bg=PANEL, fg=TEXT, font=FM, anchor="w")
                lbl.pack(side="left")
                self._crypto_labels[key] = lbl

    def _build_perf_inline(self, p):
        """Compact performance stats — shown in bottom horizontal card."""
        p.grid_rowconfigure(0, weight=1)
        p.grid_columnconfigure(0, weight=1)

        stats = [
            ("Total",       "total"),
            ("Open",        "open"),
            ("Closed",      "closed"),
            ("Wins",        "wins"),
            ("Win rate",    "win_rate"),
            ("Realized P/L","total_pl"),
            ("Unrealized",  "unrealized"),
            ("Avg P/L",     "avg_pl"),
            ("Best",        "best_trade"),
            ("Worst",       "worst_trade"),
            ("Updated",     "perf_updated"),
        ]
        sf = tk.Frame(p, bg=PANEL)
        sf.grid(row=0, column=0, sticky="nsew", padx=3, pady=3)
        for label, key in stats:
            row = tk.Frame(sf, bg=PANEL)
            row.pack(fill="x", padx=6, pady=1)
            tk.Label(row, text=label, bg=PANEL, fg=MUTED,
                font=FS, width=12, anchor="w").pack(side="left")
            lbl = tk.Label(row, text="—", bg=PANEL, fg=TEXT, font=FM, anchor="w")
            lbl.pack(side="left")
            self._perf_labels[key] = lbl




    def _initial_load(self):
        self._safe_log(f"Scanner starting — mode: {cfg.effective_mode()}")
        self._safe_log(f"Kalshi: {'Ready' if cfg.kalshi_ready() else 'No key — mock mode'}")
        self._safe_log("Auto trading: OFF (hardcoded safe)")
        self._safe_log(f"Fair price model: {'ON' if cfg.ENABLE_FAIR_PRICE_MODEL else 'OFF — signals will be DATA NEEDED'}")
        self._refresh()
        self._seed_paper_trades()
        self._refresh_crypto()   # load crypto reference prices

    def _refresh(self):
        try:
            cat = self.v_category.get()
            raw_dicts, source, error = self.data_layer.fetch(category_filter=cat)

            if error:
                self._safe_log(f"Warning: {error}")

            if not raw_dicts:
                self._safe_log("No markets — falling back to mock data.")
                # Emergency fallback: load mock directly
                from market_connectors import MockMarketConnector
                mock = MockMarketConnector()
                raw_dicts = [s.to_connector_dict() for s in mock.get_markets()]
                source = "MOCK (emergency)"

            self.signals = run_scanner(
                raw_dicts,
                min_edge   = self.v_min_edge.get(),
                max_spread = self.v_max_spread.get(),
                max_size   = self.v_max_size.get())

            self._populate_tree()
            self._update_status_box()

            ec = sum(1 for s in self.signals if s.signal in ("ENTRY","STRONG ENTRY"))
            self._safe_log(f"Loaded {len(self.signals)} markets from {source} — {ec} signals.")

            # Update paper trade current prices from refreshed market data
            price_map = {s.market_id: s.bid_price for s in self.signals if s.bid_price}
            self._paper_engine.update_prices(price_map)
            self._update_pt_tree()
            self._update_performance()

            # Update watchlist from live signal data (returns alert messages)
            self._watchlist.update_from_signals(self.signals)
            self._refresh_wl_tree()
            # Route any watchlist alerts to Scanner Messages
            for alert_msg in self._watchlist.get_alert_messages():
                self._safe_log(alert_msg)

            # Refresh crypto reference in background
            self._refresh_crypto()

        except Exception as e:
            self._safe_log(f"Refresh error: {e}")
            self._update_status_box()

    def _populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        signals = self._filtered_signals()
        if not signals:
            return
        data_src = self.data_layer._last_source or "mock"
        for sig in signals:
            tag = sig.signal.replace(" ", "_")
            # MarketSignal stores prices in CENTS (0-100) — use format_cents()
            # format_price() is for dollar floats (0.0-1.0) from MarketSnapshot only
            bid_str  = format_cents(sig.bid_price)  if sig.bid_price  else "N/A"
            ask_str  = format_cents(sig.ask_price)  if sig.ask_price  else "N/A"
            last_str = format_cents(sig.last_price) if sig.last_price else "N/A"
            fair_str = format_cents(sig.fair_price) if sig.fair_price else "N/A"
            edge_str = f"{sig.raw_edge:+.0f}c"      if sig.ask_price  else "N/A"
            sprd_str = format_cents(sig.spread)     if sig.spread     else "N/A"
            fee_str  = f"{sig.fee_est:.0f}c"        if sig.ask_price  else "N/A"
            bkev_str = f"{sig.breakeven:.0f}c"      if sig.breakeven  else "N/A"
            size_str = f"${sig.suggested_size:.0f}" if sig.suggested_size else "$0"
            exit_str = f"{sig.exit_target:.0f}c"    if sig.exit_target else "—"
            self.tree.insert("", "end", values=(
                sig.market_name[:28], sig.side,
                bid_str, ask_str, last_str, fair_str,
                edge_str, sprd_str, fee_str, bkev_str,
                sig.signal, size_str, exit_str,
                data_src[:8],
            ), tags=(tag,), iid=sig.market_id)

    def _seed_paper_trades(self):
        """Paper trades and watchlist loaded from disk on startup."""
        self._update_pt_tree()
        self._update_performance()
        self._refresh_wl_tree()   # watchlist already loaded by ScannerWatchlist.__init__



    def _start_scan(self):
        if self.scanning:
            return
        self.scanning = True
        interval = cfg.SCANNER_REFRESH_SEC
        self._safe_log(f"Paper scan started — refresh every {interval}s.")
        self._scan_tick()

    def _scan_tick(self):
        if not self.scanning:
            return
        self._refresh()
        self.scan_job = self.after(cfg.SCANNER_REFRESH_SEC * 1000, self._scan_tick)

    def _stop_scan(self):
        self.scanning = False
        if self.scan_job:
            self.after_cancel(self.scan_job)
            self.scan_job = None
        self._safe_log("Scan stopped.")

    def _on_select(self, _event=None):
        try:
            sel = self.tree.selection()
            if not sel:
                return
            sig = next((s for s in self.signals if s.market_id == sel[0]), None)
            if sig:
                self.selected_signal = sig
                self._show_signal_detail(sig)
        except Exception as e:
            print(f"[scanner select] {e}")

    def _sort_tree(self, col):
        try:
            items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
            items.sort()
            for i, (_, k) in enumerate(items):
                self.tree.move(k, "", i)
        except Exception:
            pass

    def _add_watchlist(self, sig):
        """Add selected signal to the AI Scanner watchlist."""
        # parse_crypto_market_title imported at module level
        ctx = parse_crypto_market_title(sig.market_name)
        btc_snap = self._crypto_prices.get("BTC")
        ref_price = btc_snap.price if (ctx.asset == "BTC" and btc_snap) else None
        if ctx.asset == "ETH":
            eth_snap = self._crypto_prices.get("ETH")
            ref_price = eth_snap.price if eth_snap else None

        entry = WatchlistEntry(
            ticker          = sig.market_id,
            title           = sig.market_name,
            side            = sig.side,
            signal          = sig.signal,
            bid             = sig.bid_price   if sig.bid_price  else None,
            ask             = sig.ask_price   if sig.ask_price  else None,
            last            = sig.last_price  if sig.last_price else None,
            category        = sig.category,
            source          = self.data_layer._last_source or "kalshi",
            time_added      = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            target_price    = ctx.target_price,
            reference_price = ref_price,
            status          = "ACTIVE",
        )
        self._watchlist.add(entry)
        self._refresh_wl_tree()

    def _wl_remove_selected(self):
        """Remove selected watchlist item."""
        sel = self.wl_tree.selection()
        if not sel:
            self._safe_log("Select a watchlist row first.")
            return
        ticker = sel[0]
        self._watchlist.remove(ticker)
        self._refresh_wl_tree()

    def _wl_remove(self, sig):
        """Remove a signal from watchlist via Signal Detail panel."""
        removed = self._watchlist.remove(sig.market_id)
        if removed:
            try:
                self._refresh_wl_tree()
            except AttributeError:
                pass   # wl_tree may not exist if watchlist tab is not shown
        # Refresh detail panel to update Add/Remove button label
        self._show_signal_detail(sig)

    def _wl_clear_stale(self):
        """Clear STALE/EXPIRED watchlist entries."""
        self._watchlist.clear_stale()
        self._refresh_wl_tree()

    def _refresh_wl_tree(self):
        """Rebuild watchlist treeview from engine. Safe if wl_tree not built yet."""
        if not hasattr(self, 'wl_tree') or self.wl_tree is None:
            return
        try:
            self.wl_tree.delete(*self.wl_tree.get_children())
            entries = self._watchlist.all_entries()
            for e in entries:
                # Color tags by status
                if e.avoided or e.status == "AVOID":
                    tag = "avoid"
                elif e.status == "ALERT":
                    tag = "alert"
                elif e.status in ("STALE", "EXPIRED"):
                    tag = "stale"
                else:
                    tag = "active"
                ref_str  = f"${e.reference_price:,.0f}" if e.reference_price else "N/A"
                spread_s = f"{e.spread:.0f}c" if e.spread else "N/A"
                seen_s   = e.last_seen[11:16] if e.last_seen else "N/A"
                self.wl_tree.insert("", "end", iid=e.ticker, values=(
                    e.title[:22], e.side,
                    e.bid_str, e.ask_str, e.last_str,
                    e.signal, spread_s,
                    e.target_str, ref_str, e.status, seen_s,
                ), tags=(tag,))
            # Configure tag colors
            self.wl_tree.tag_configure("stale",  foreground=MUTED)
            self.wl_tree.tag_configure("active", foreground=GREEN)
            self.wl_tree.tag_configure("alert",  foreground=YELLOW)
            self.wl_tree.tag_configure("avoid",  foreground=RED)
            if hasattr(self, '_wl_count_lbl'):
                self._wl_count_lbl.config(
                    text=f"{len(entries)} item{'s' if len(entries) != 1 else ''}")
        except Exception as ex:
            print(f"[wl_tree] {ex}")



    def _mark_avoid(self, sig):
        """Mark selected market as avoid. Saves to watchlist."""
        if not self._watchlist.contains(sig.market_id):
            from scanner_watchlist import WatchlistEntry
            from datetime import datetime
            e = WatchlistEntry(
                ticker=sig.market_id, title=sig.market_name,
                side=sig.side, signal="AVOID",
                bid=sig.bid_price or None, ask=sig.ask_price or None,
                last=sig.last_price or None,
                category=sig.category, source="kalshi",
                time_added=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                avoided=True, status="AVOID", alert_note="User marked avoid")
            self._watchlist.add(e)
        else:
            self._watchlist.mark_avoided(sig.market_id, "User marked avoid")
        self._refresh_wl_tree()
        self._safe_log(f"Marked AVOID: {sig.market_name}")

    def _export_signal(self, sig):
        self._safe_log(f"Exported: {sig.market_name} | {sig.signal} | Edge {sig.raw_edge:+.0f}c")

    def _reset_filters(self):
        self.v_min_edge.set(cfg.SCANNER_MIN_EDGE)
        self.v_max_spread.set(cfg.SCANNER_MAX_SPREAD)
        self.v_max_size.set(cfg.SCANNER_MAX_TRADE_SIZE)
        self.v_daily_loss.set(cfg.SCANNER_DAILY_LOSS)
        self.v_category.set("All")
        self.v_timeframe.set("Live")
        self._safe_log("Filters reset.")
        self._refresh()

    # ── Kalshi actions ─────────────────────────────────────────────────────

    def _test_auth(self):
        """Test Kalshi RSA auth. Read-only — no orders placed."""
        self._safe_log("Auth test requested…")
        self._safe_log("Auto trading remains OFF — no orders will be placed.")
        try:
            ok, msg = self.data_layer.test_kalshi_auth()
            self._safe_log(msg)
            if not ok:
                self._safe_log("Check .env: KALSHI_API_KEY_ID and KALSHI_PRIVATE_KEY_PATH")
        except Exception as e:
            self._safe_log(f"Auth test error: {e}")
        self._update_status_box()

    def _load_orderbook_for_selected(self):
        """Load orderbook for selected row. Read-only — no orders."""
        if not self.selected_signal:
            self._safe_log("Select a market row first, then click Load Orderbook.")
            return
        ticker = self.selected_signal.market_id
        self._safe_log(f"Fetching orderbook for {ticker}…")
        try:
            ob = self.data_layer.get_orderbook(ticker,
                source=self.data_layer._last_source)
            if ob:
                yb = format_price(ob.yes_best_bid)
                ya = format_price(ob.yes_best_ask)
                nb = format_price(ob.no_best_bid)
                na = format_price(ob.no_best_ask)
                depth = ob.total_yes_qty + ob.total_no_qty
                self._safe_log(
                    f"OB {ticker}: YES {yb}/{ya}  NO {nb}/{na}  "
                    f"liq={ob.liquidity}  depth={depth}")
                sig = self.selected_signal
                # Pick side and get dollar prices for engine
                oya, ona = ob.yes_best_ask, ob.no_best_ask
                if oya is not None and ona is not None:
                    ob_side = "YES" if oya <= ona else "NO"
                elif oya is not None: ob_side = "YES"
                elif ona is not None: ob_side = "NO"
                else:                ob_side = sig.side
                bid_d = ob.yes_best_bid if ob_side == "YES" else ob.no_best_bid
                ask_d = ob.yes_best_ask if ob_side == "YES" else ob.no_best_ask
                raw = {
                    "market_id":        sig.market_id,
                    "market_name":      sig.market_name,
                    "category":         sig.category,
                    "side":             ob_side,
                    "bid_price":        bid_d,        # dollars → engine converts to cents
                    "ask_price":        ask_d,
                    "last_price":       sig.last_price/100.0 if sig.last_price else None,
                    "model_fair_price": sig.fair_price/100.0 if sig.fair_price else None,
                    "volume":           sig.volume,
                    "liquidity":        ob.liquidity,
                }
                from market_scanner_engine import analyse_market
                updated = analyse_market(raw)
                for i, s in enumerate(self.signals):
                    if s.market_id == ticker:
                        self.signals[i] = updated
                        self.selected_signal = updated
                        break
                tag = updated.signal.replace(" ", "_")
                try:
                    self.tree.item(ticker, values=(
                        updated.market_name[:28], updated.side,
                        format_cents(updated.bid_price)  if updated.bid_price  else "N/A",
                        format_cents(updated.ask_price)  if updated.ask_price  else "N/A",
                        format_cents(updated.last_price) if updated.last_price else "N/A",
                        format_cents(updated.fair_price) if updated.fair_price else "N/A",
                        f"{updated.raw_edge:+.0f}c"   if updated.ask_price  else "N/A",
                        format_cents(updated.spread)  if updated.spread     else "N/A",
                        f"{updated.fee_est:.0f}c"      if updated.ask_price  else "N/A",
                        f"{updated.breakeven:.0f}c"    if updated.breakeven  else "N/A",
                        updated.signal,
                        f"${updated.suggested_size:.0f}" if updated.suggested_size else "$0",
                        f"{updated.exit_target:.0f}c"    if updated.exit_target    else "—",
                        self.data_layer._last_source[:8],
                    ), tags=(tag,))
                except Exception:
                    self._populate_tree()
                self._show_signal_detail(updated)
                self._last_ob_status = f"Loaded (depth={depth})"
            else:
                self._safe_log("No orderbook prices available for this market.")
                self._last_ob_status = "Not available"
        except Exception as e:
            self._safe_log(f"Orderbook error: {e}")
            self._last_ob_status = "Failed"
        self._update_status_box()

    # ── Crypto reference ───────────────────────────────────────────────────

    def _on_crypto_src_change(self):
        src = self.v_crypto_src.get()
        self._crypto_layer.set_preferred(src)
        self._safe_log(f"Crypto source: {src}")
        self._refresh_crypto()

    def _refresh_crypto(self):
        """Fetch BTC and ETH reference prices in background thread."""
        import threading
        threading.Thread(target=self._fetch_crypto_bg, daemon=True).start()

    def _fetch_crypto_bg(self):
        """Background crypto price fetch — never blocks UI."""
        try:
            prices = self._crypto_layer.fetch_all()
            self._crypto_prices = prices
            self.after(0, self._update_crypto_labels)
        except Exception as e:
            self._safe_log(f"Crypto fetch error: {e}")

    def _update_crypto_labels(self):
        """Update all crypto labels — right-panel card and bottom inline card."""
        try:
            btc = self._crypto_prices.get("BTC")
            eth = self._crypto_prices.get("ETH")

            # Right-panel summary labels (BTC/ETH price + source)
            for sym, snap in [("BTC", btc), ("ETH", eth)]:
                lbl = self._crypto_labels.get(sym)
                if lbl:
                    if snap and snap.price:
                        lbl.config(text=snap.price_str,
                            fg=GREEN if snap.status == "ok" else YELLOW)
                    else:
                        lbl.config(text="N/A", fg=MUTED)
            any_snap = btc or eth
            if any_snap:
                if self._crypto_labels.get("src"):
                    self._crypto_labels["src"].config(text=any_snap.source)
                if self._crypto_labels.get("updated"):
                    self._crypto_labels["updated"].config(
                        text=any_snap.timestamp[11:16] if any_snap.timestamp else "")

            # Bottom inline card labels
            def _upd(key, value, col=None):
                lbl = self._crypto_labels.get(key)
                if lbl:
                    lbl.config(text=(value or "N/A"), fg=(col or TEXT))

            if btc:
                _upd("btc_price", btc.price_str,
                     GREEN if btc.status == "ok" else YELLOW)
                _upd("btc_bid",   f"${btc.bid:,.2f}"    if btc.bid  else "N/A")
                _upd("btc_ask",   f"${btc.ask:,.2f}"    if btc.ask  else "N/A")
                _upd("btc_1m",    "— (placeholder)")
                _upd("btc_5m",    "— (placeholder)")
                _upd("btc_src",   btc.source)
                _upd("btc_ts",    btc.timestamp[11:16]   if btc.timestamp else "N/A")
            if eth:
                _upd("eth_price", eth.price_str,
                     GREEN if eth.status == "ok" else YELLOW)
                _upd("eth_bid",   f"${eth.bid:,.2f}"    if eth.bid  else "N/A")
                _upd("eth_ask",   f"${eth.ask:,.2f}"    if eth.ask  else "N/A")
                _upd("eth_1m",    "— (placeholder)")
                _upd("eth_5m",    "— (placeholder)")
                _upd("eth_src",   eth.source)
                _upd("eth_ts",    eth.timestamp[11:16]   if eth.timestamp else "N/A")

        except Exception as e:
            print(f"[crypto labels] {e}")

    # ── Enhanced signal detail with crypto context ─────────────────────────

    def _build_crypto_context_section(self, p, sig):
        """Add crypto reference context to signal detail panel."""
        ctx = parse_crypto_market_title(sig.market_name)
        if ctx.asset == "UNKNOWN":
            return   # not a crypto market

        snap = self._crypto_prices.get(ctx.asset)
        current_price = snap.price if snap else None

        tk.Frame(p, bg=BORDER, height=1).pack(fill="x", padx=6, pady=4)
        tk.Label(p, text=f"CRYPTO REFERENCE ({ctx.asset})", bg=PANEL_DARK,
            fg=CYAN, font=FB, padx=8, pady=3, anchor="w").pack(fill="x")

        rows = []
        if current_price:
            rows.append((f"{ctx.asset} price", f"${current_price:,.2f}"))
        if ctx.target_price:
            rows.append(("Target price", f"${ctx.target_price:,.2f}"))
            if current_price:
                dist = current_price - ctx.target_price
                dist_pct = dist / ctx.target_price * 100
                rows.append(("Distance", f"${dist:+,.2f}  ({dist_pct:+.1f}%)"))
        rows.append(("Condition", ctx.condition))
        if ctx.expiration_text:
            rows.append(("Expires", ctx.expiration_text))
        rows.append(("Source", snap.source if snap else "N/A"))

        cf = tk.Frame(p, bg=PANEL_DARK)
        cf.pack(fill="x", padx=6, pady=4)
        for lbl, val in rows:
            row = tk.Frame(cf, bg=PANEL_DARK)
            row.pack(fill="x", padx=6, pady=1)
            tk.Label(row, text=lbl, bg=PANEL_DARK, fg=MUTED,
                font=FS, width=14, anchor="w").pack(side="left")
            # Color distance rows
            col = TEXT
            if "Distance" in lbl and "+" in val:
                col = GREEN if ctx.condition == "ABOVE" else RED
            elif "Distance" in lbl and "-" in val:
                col = RED if ctx.condition == "ABOVE" else GREEN
            tk.Label(row, text=val, bg=PANEL_DARK, fg=col,
                font=FM, anchor="w").pack(side="left")

        # Fair price model note
        if not cfg.ENABLE_FAIR_PRICE_MODEL:
            tk.Label(p,
                text=("Fair price model: OFF (DATA NEEDED)\n"
                      "Set ENABLE_FAIR_PRICE_MODEL=true in .env to enable."),
                bg="#1a1a2e", fg=YELLOW, font=FS, padx=8, pady=4,
                justify="left", wraplength=260).pack(fill="x", padx=6, pady=4)

    # ── Paper trade engine integration ────────────────────────────────────

    def _paper_trade(self, sig):
        """
        Create paper trade locally. Does NOT call any Kalshi order endpoint.
        No real orders. No account balance used.
        Blocks if ask price missing or market closed.
        """
        # Check if market is closed
        try:
            snap = self.data_layer.get_snapshot(sig.market_id)
            if snap:
                status = getattr(snap, "status", "open") or "open"
                if status.lower() in ("closed", "settled", "finalized"):
                    self._safe_log(
                        f"Paper trade blocked: {sig.market_id} is {status.upper()}. "
                        f"Cannot enter a closed market.")
                    return
            raw_data = snap.raw_data if snap and snap.raw_data else {}
            rules_txt = raw_data.get("rules_primary", "")
            if not rules_txt:
                self._safe_log(
                    f"Paper trade created without settlement rules available "
                    f"for {sig.market_id}. Paper mode only — no real order placed.")
        except Exception:
            pass

        if not sig.ask_price or sig.ask_price <= 0:
            self._safe_log(
                f"Paper trade blocked for {sig.market_id}: "
                f"no valid entry price (ask = N/A). "
                f"Click 'Load Orderbook' first to fetch live bid/ask prices. "
                f"No real order was placed.")
            return
        try:
            _ = self._paper_engine
        except AttributeError:
            self._safe_log("Paper trade system not ready yet.")
            return
        max_size = self.v_max_size.get()
        trade = self._paper_engine.create_trade(
            ticker       = sig.market_id,
            title        = sig.market_name,
            side         = sig.side,
            entry_cents  = sig.ask_price,
            max_size_dollars = max_size,
            source       = self.data_layer._last_source or "kalshi",
            reason       = sig.reason[:100],
        )
        if trade:
            self._update_pt_tree()
            self._update_performance()

    def _exit_selected_paper_trade(self):
        """
        Close the selected paper trade at current bid price.
        Tries live market bid first, falls back to last known price.
        No real orders placed.
        """
        if not self._selected_trade:
            self._safe_log("Select a paper trade row first to close it.")
            return
        trade_id = self._selected_trade
        trade = self._paper_engine._find(trade_id)
        if trade is None:
            self._safe_log(f"Paper trade {trade_id} not found.")
            return
        if trade.status != "OPEN":
            self._safe_log(f"Paper trade {trade_id} is already {trade.status}.")
            return

        # Try to get live current bid from loaded signals
        live_bid = None
        for sig in self.signals:
            if sig.market_id == trade.ticker:
                live_bid = sig.bid_price or None
                break

        if live_bid and live_bid > 0:
            exit_price = live_bid
            self._safe_log(
                f"Closing {trade.ticker} at live bid {exit_price:.0f}c. "
                f"NO REAL ORDER PLACED.")
        elif trade.current_price and trade.current_price > 0:
            exit_price = trade.current_price
            self._safe_log(
                f"Closing {trade.ticker} at last known price {exit_price:.0f}c "
                f"(no live bid found). NO REAL ORDER PLACED.")
        else:
            self._safe_log(
                f"Cannot close paper trade {trade_id}: "
                f"current price unavailable. Load orderbook first.")
            return

        closed = self._paper_engine.exit_trade(
            trade_id, exit_price, reason="Manual close")
        if closed:
            self._safe_log(
                f"Paper trade closed: {closed.ticker} {closed.side} "
                f"P/L {closed.pl_str}  — LOCAL ONLY, NO REAL ORDER.")
        self._update_pt_tree()
        self._update_performance()

    def _update_pt_tree(self):
        """Refresh paper trade log from engine. Shows OPEN trades in compact card."""
        try:
            self.pt_tree.delete(*self.pt_tree.get_children())
            for t in reversed(self._paper_engine.all_trades()):
                pl_str = t.pl_str
                # Color tags
                if t.status == "CLOSED":
                    tag = "closed_win" if "$+" in pl_str else "closed_loss"
                else:
                    tag = "open"
                display_name = t.title[:22] if t.title else t.ticker[:22]
                exit_s = f"{t.exit_price:.0f}c" if t.exit_price else "—"
                cur_s  = f"{t.current_price:.0f}c" if t.current_price else "N/A"
                self.pt_tree.insert("", "end", iid=t.trade_id, values=(
                    t.time_opened[11:19],
                    display_name,
                    t.side,
                    f"{t.entry_price:.0f}c",
                    exit_s,
                    cur_s,
                    str(t.contracts),
                    f"{t.buy_fee:.0f}c",
                    pl_str,
                    t.status,
                ), tags=(tag,))
            # Color tags
            self.pt_tree.tag_configure("open",        foreground=TEXT)
            self.pt_tree.tag_configure("closed_win",  foreground=GREEN)
            self.pt_tree.tag_configure("closed_loss", foreground=RED)
            self.pt_tree.bind("<<TreeviewSelect>>", self._on_pt_select)
        except Exception as e:
            print(f"[pt_tree] {e}")

    def _on_pt_select(self, _event=None):
        try:
            sel = self.pt_tree.selection()
            if sel:
                self._selected_trade = sel[0]
        except Exception:
            pass

    def _update_performance(self):
        """Refresh performance summary labels with colors and last-updated timestamp."""
        try:
            from datetime import datetime
            perf = self._paper_engine.performance_summary()
            # Add last updated timestamp
            perf["perf_updated"] = datetime.now().strftime("%H:%M:%S")
            # Set zero values explicitly (don't leave "—" when we have real data)
            for zero_key in ("total","open","closed","wins"):
                if perf.get(zero_key) == 0:
                    perf[zero_key] = "0"
            for key, lbl in self._perf_labels.items():
                val = str(perf.get(key, "—"))
                col = TEXT
                if val.startswith("$+"):   col = GREEN
                elif val.startswith("$-"): col = RED
                elif key == "win_rate" and val not in ("—", "0.0%"):
                    try:
                        pct = float(val.replace("%",""))
                        col = GREEN if pct >= 50 else RED
                    except Exception:
                        pass
                lbl.config(text=val, fg=col)
        except Exception as e:
            print(f"[perf] {e}")

    # ── Source change handler ──────────────────────────────────────────────

    # ── Maximize / Restore system ────────────────────────────────────────────

    def _maximize_panel(self, panel_name: str):
        """
        Expand panel_name into a full-scanner overlay workspace.
        Hides the normal body (PanedWindow), shows the overlay frame.
        Preserves selected market, watchlist, paper trades.
        """
        if self._maximized_panel == panel_name:
            self._restore_panel()
            return

        # Build overlay frame lazily on first use
        if self._max_frame is None:
            self._max_frame = tk.Frame(self, bg=BG)
            self._max_frame.grid_rowconfigure(0, weight=0)
            self._max_frame.grid_rowconfigure(1, weight=1)
            self._max_frame.grid_columnconfigure(0, weight=1)

        self._maximized_panel = panel_name

        # Hide normal body, show overlay
        try:
            self._v_pane.grid_remove()
        except Exception:
            pass
        self._max_frame.grid(row=1, column=0, sticky="nsew")

        # Update button labels
        self._update_max_buttons()

        # Render the expanded content
        try:
            self._render_maximized(panel_name)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            # Show error inside overlay
            for w in self._max_frame.winfo_children():
                w.destroy()
            hdr = tk.Frame(self._max_frame, bg=TOP)
            hdr.grid(row=0, column=0, sticky="ew", padx=8, pady=4)
            tk.Label(hdr, text=f"Failed to maximize: {panel_name}",
                bg=TOP, fg=RED, font=FB).pack(side="left")
            tk.Button(hdr, text="↩ Restore", bg=PANEL, fg=CYAN,
                font=FM, relief="flat", padx=8, pady=4,
                command=self._restore_panel).pack(side="right")
            tk.Label(self._max_frame, text=str(exc),
                bg=BG, fg=MUTED, font=FS, wraplength=600,
                justify="left").grid(row=1, column=0, padx=20, pady=20)

    def _restore_panel(self):
        """Return to the normal scanner layout.
        Preserves selected signal, watchlist, paper trades, and filters.
        """
        self._maximized_panel = None
        if self._max_frame:
            self._max_frame.grid_remove()
            # Clear maximize content to free memory
            for w in self._max_frame.winfo_children():
                try:
                    w.destroy()
                except Exception:
                    pass
        try:
            self._v_pane.grid(row=1, column=0, sticky="nsew")
        except Exception:
            pass
        self._update_max_buttons()
        # Refresh normal panels with current state (no API reload)
        try:
            self._update_pt_tree()
            self._update_performance()
            self._refresh_wl_tree()
            self._update_crypto_labels()
        except Exception:
            pass

    def _update_max_buttons(self):
        """Update all maximize button labels based on current state."""
        for name, btn in self._panel_btns.items():
            try:
                if self._maximized_panel == name:
                    btn.config(text="↩", fg=YELLOW)
                else:
                    btn.config(text="⛶", fg=MUTED)
            except Exception:
                pass

    def _max_btn(self, parent, panel_name: str) -> "tk.Button":
        """
        Create a small maximize button for a panel header.
        Stores ref in self._panel_btns.
        """
        btn = tk.Button(parent, text="⛶", bg=TOP, fg=MUTED,
            activebackground=TOP, relief="flat",
            font=("Segoe UI", 9), padx=4, pady=1,
            command=lambda n=panel_name: self._maximize_panel(n))
        self._panel_btns[panel_name] = btn
        return btn

    def _render_maximized(self, panel_name: str):
        """Render expanded content for a given panel into _max_frame."""
        # Clear previous content
        for w in self._max_frame.winfo_children():
            w.destroy()

        # ── Header with title + restore button ────────────────────────
        hdr = tk.Frame(self._max_frame, bg=TOP)
        hdr.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        titles = {
            "signal_detail":    "SIGNAL DETAIL — MARKET DEEP DIVE",
            "scanner_table":    "SIGNAL SCANNER TABLE",
            "watchlist":        "WATCHLIST",
            "paper_trades":     "PAPER TRADES",
            "scanner_messages": "SCANNER MESSAGES",
            "performance":      "PERFORMANCE",
            "crypto_prices":    "CRYPTO PRICES",
        }
        tk.Label(hdr, text=titles.get(panel_name, panel_name.upper()),
            bg=TOP, fg=CYAN, font=FB).pack(side="left", padx=8)
        tk.Button(hdr, text="↩ Restore Normal Layout",
            bg=PANEL, fg=CYAN, activebackground=PANEL,
            relief="flat", font=FM, padx=10, pady=4,
            command=self._restore_panel).pack(side="right", padx=8)

        # ── Body ──────────────────────────────────────────────────────
        body = tk.Frame(self._max_frame, bg=BG)
        body.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)

        if panel_name == "signal_detail":
            self._render_max_signal_detail(body)
        elif panel_name == "scanner_table":
            self._render_max_scanner_table(body)
        elif panel_name == "watchlist":
            self._render_max_watchlist(body)
        elif panel_name == "paper_trades":
            self._render_max_paper_trades(body)
        elif panel_name == "scanner_messages":
            self._render_max_messages(body)
        elif panel_name == "performance":
            self._render_max_performance(body)
        elif panel_name == "crypto_prices":
            self._render_max_crypto(body)
        elif panel_name == "filters_settings":
            self._render_max_filters(body)
        else:
            tk.Label(body, text=f"No expanded view for: {panel_name}",
                bg=BG, fg=MUTED, font=FM).pack(expand=True)

    # ── Expanded panel renderers ──────────────────────────────────────────

    def _render_max_signal_detail(self, parent):
        """Expanded Signal Detail — full detail with scrollable sections."""
        if not self.selected_signal:
            tk.Label(parent, text="No market selected. Select a market and try again.",
                bg=BG, fg=MUTED, font=FM).grid(row=0, column=0)
            return
        # Reuse the existing _show_signal_detail inside a scrollable canvas
        canvas = tk.Canvas(parent, bg=BG, highlightthickness=0)
        vsb    = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        inner = tk.Frame(canvas, bg=BG)
        win   = canvas.create_window((0,0), window=inner, anchor="nw")
        canvas.bind("<Configure>",
            lambda e: canvas.itemconfig(win, width=e.width))
        inner.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        # Render full detail into inner
        detail_body = tk.Frame(inner, bg=PANEL)
        detail_body.pack(fill="both", expand=True, padx=8, pady=8)
        orig = self._detail_body
        self._detail_body = detail_body
        try:
            self._show_signal_detail(self.selected_signal)
        finally:
            self._detail_body = orig

    def _render_max_scanner_table(self, parent):
        """Expanded scanner table with more columns."""
        from tkinter import ttk
        parent.grid_rowconfigure(0, weight=0)
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        # Toolbar
        tb = tk.Frame(parent, bg=TOP)
        tb.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        tk.Label(tb, text=f"{len(self.signals)} markets loaded",
            bg=TOP, fg=MUTED, font=FS).pack(side="left", padx=8)
        tk.Button(tb, text="↻ Refresh", bg=PANEL, fg=CYAN,
            relief="flat", font=FS, padx=8,
            command=self._refresh).pack(side="right", padx=4)

        # Table
        cols = ("Market","Side","Signal","Bid","Ask","Spread",
                "Liquidity","Volume","Fair","Edge","Category","Source")
        col_w = {"Market":180,"Side":40,"Signal":100,"Bid":45,"Ask":45,
                 "Spread":50,"Liquidity":65,"Volume":60,"Fair":45,
                 "Edge":55,"Category":80,"Source":70}
        tf = tk.Frame(parent, bg=PANEL)
        tf.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        tf.grid_rowconfigure(0, weight=1)
        tf.grid_columnconfigure(0, weight=1)
        tree = ttk.Treeview(tf, columns=cols, show="headings",
            style="Scanner.Treeview")
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=col_w.get(col,60), anchor="center", stretch=False)
        tree.column("Market", anchor="w", stretch=True)
        vsb = ttk.Scrollbar(tf, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        # Populate
        for sig in self._filtered_signals():
            tag = sig.signal.replace(" ","_")
            tree.insert("", "end", iid=sig.market_id+"_max", values=(
                sig.market_name[:35], sig.side, sig.signal,
                format_cents(sig.bid_price)  if sig.bid_price  else "N/A",
                format_cents(sig.ask_price)  if sig.ask_price  else "N/A",
                format_cents(sig.spread)     if sig.spread     else "N/A",
                sig.liquidity, f"{sig.volume:,}" if sig.volume else "N/A",
                format_cents(sig.fair_price) if sig.fair_price else "N/A",
                f"{sig.raw_edge:+.1f}c"      if sig.ask_price  else "N/A",
                sig.category, self.data_layer._last_source[:8],
            ), tags=(tag,))
        for sig_tier, colors in SIG_COLORS.items():
            tree.tag_configure(sig_tier.replace(" ","_"),
                background=colors["bg"], foreground=colors["fg"])

    def _render_max_watchlist(self, parent):
        """Expanded watchlist with full columns."""
        from tkinter import ttk
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        # Toolbar
        tb = tk.Frame(parent, bg=TOP)
        tb.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        tk.Button(tb, text="Remove Selected", bg=RED_DARK, fg=TEXT,
            relief="flat", font=FS, padx=8,
            command=self._wl_remove_selected).pack(side="left", padx=2)
        tk.Button(tb, text="Clear Stale", bg=GRAY_BTN, fg=TEXT,
            relief="flat", font=FS, padx=8,
            command=self._wl_clear_stale).pack(side="left", padx=2)
        tk.Label(tb, text=f"{len(self._watchlist.all_entries())} items",
            bg=TOP, fg=MUTED, font=FS).pack(side="right", padx=8)
        # Table
        cols = ("Market","Side","Bid","Ask","Last","Signal","Score",
                "Spread","Time Left","Target","Ref Price","Status","Updated")
        col_w = {"Market":160,"Side":40,"Bid":42,"Ask":42,"Last":42,"Signal":90,
                 "Score":45,"Spread":50,"Time Left":80,"Target":70,
                 "Ref Price":80,"Status":60,"Updated":60}
        tf = tk.Frame(parent, bg=PANEL)
        tf.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        tf.grid_rowconfigure(0, weight=1)
        tf.grid_columnconfigure(0, weight=1)
        tree = ttk.Treeview(tf, columns=cols, show="headings",
            style="Scanner.Treeview")
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=col_w.get(col,55), anchor="center", stretch=False)
        tree.column("Market", anchor="w", stretch=True)
        vsb = ttk.Scrollbar(tf, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree.tag_configure("stale",  foreground=MUTED)
        tree.tag_configure("active", foreground=GREEN)
        tree.tag_configure("alert",  foreground=YELLOW)
        tree.tag_configure("avoid",  foreground=RED)
        # Store ref so toolbar buttons work
        self._max_wl_tree = tree
        for e in self._watchlist.all_entries():
            tag = "avoid" if e.avoided else ("alert" if e.status=="ALERT" else
                  "stale" if e.status in ("STALE","EXPIRED") else "active")
            ref = f"${e.reference_price:,.0f}" if e.reference_price else "N/A"
            tree.insert("", "end", iid=e.ticker+"_wmax", values=(
                e.title[:25], e.side, e.bid_str, e.ask_str, e.last_str,
                e.signal, str(e.score),
                f"{e.spread:.0f}c" if e.spread else "N/A",
                "N/A",   # time left — not stored per-entry yet
                e.target_str, ref, e.status,
                e.last_seen[11:16] if e.last_seen else "N/A",
            ), tags=(tag,))

    def _render_max_paper_trades(self, parent):
        """Expanded paper trades log with filter, close, and export."""
        from tkinter import ttk
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        # Toolbar
        tb = tk.Frame(parent, bg=TOP)
        tb.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        trades = self._paper_engine.all_trades()

        # Filter var
        _filter_var = tk.StringVar(value="All")

        def _apply_filter():
            fv = _filter_var.get()
            return [t for t in trades if fv == "All" or t.status == fv]

        def _export_trades():
            try:
                path = self._paper_engine.export_csv()
                if path:
                    self._safe_log(f"Paper trades exported → {path}")
                else:
                    self._safe_log("Export failed — check terminal.")
            except Exception as exc:
                self._safe_log(f"Export error: {exc}")

        def _export_perf():
            try:
                path = self._paper_engine.export_performance_csv()
                if path:
                    self._safe_log(f"Performance exported → {path}")
            except Exception as exc:
                self._safe_log(f"Perf export error: {exc}")

        tk.Label(tb, text=f"{len(trades)} trades",
            bg=TOP, fg=MUTED, font=FS).pack(side="left", padx=8)

        # Filter radio buttons
        for label in ["All", "OPEN", "CLOSED"]:
            tk.Radiobutton(tb, text=label, variable=_filter_var,
                value=label, bg=TOP, fg=TEXT, selectcolor=TOP,
                activebackground=TOP, font=FS,
                command=lambda: _rebuild_tree(_apply_filter())
            ).pack(side="left", padx=3)

        tk.Button(tb, text="Close Selected", bg="#0e7490", fg=TEXT,
            relief="flat", font=FS, padx=8,
            command=self._exit_selected_paper_trade).pack(side="right", padx=4)
        tk.Button(tb, text="Export CSV", bg=PANEL, fg=CYAN,
            relief="flat", font=FS, padx=8,
            command=_export_trades).pack(side="right", padx=2)
        tk.Button(tb, text="Export Perf", bg=PANEL, fg=CYAN,
            relief="flat", font=FS, padx=8,
            command=_export_perf).pack(side="right", padx=2)
        cols = ("Opened","Closed","Market","Side","Entry","Exit",
                "Current","Contracts","Real P/L","Unreal P/L","Status","Notes")
        col_w = {"Opened":70,"Closed":70,"Market":160,"Side":38,"Entry":42,
                 "Exit":42,"Current":48,"Contracts":50,
                 "Real P/L":70,"Unreal P/L":70,"Status":55,"Notes":80}
        tf = tk.Frame(parent, bg=PANEL)
        tf.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        tf.grid_rowconfigure(0, weight=1)
        tf.grid_columnconfigure(0, weight=1)
        tree = ttk.Treeview(tf, columns=cols, show="headings",
            style="Scanner.Treeview")
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=col_w.get(col,60), anchor="center", stretch=False)
        tree.column("Market", anchor="w", stretch=True)
        tree.tag_configure("open",        foreground=TEXT)
        tree.tag_configure("closed_win",  foreground=GREEN)
        tree.tag_configure("closed_loss", foreground=RED)
        vsb = ttk.Scrollbar(tf, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        self._max_pt_tree = tree

        def _rebuild_tree(filtered_trades):
            tree.delete(*tree.get_children())
            for t in reversed(filtered_trades):
                unreal = f"${t.unrealized_pl_dollars:+.4f}" if t.status == "OPEN"    else "—"
                real   = f"${t.realized_pl_dollars:+.4f}"   if t.status == "CLOSED"  else "—"
                exit_s = f"{t.exit_price:.0f}c" if t.exit_price else "—"
                tag    = "open" if t.status == "OPEN" else (
                         "closed_win" if (t.realized_pl_dollars or 0) > 0 else "closed_loss")
                iid = t.trade_id + "_max"
                tree.insert("", "end", iid=iid, values=(
                    t.time_opened[5:16],
                    t.time_closed[5:16] if t.time_closed else "—",
                    t.title[:25] if t.title else t.ticker[:25],
                    t.side,
                    f"{t.entry_price:.0f}c",
                    exit_s,
                    f"{t.current_price:.0f}c",
                    str(t.contracts),
                    real, unreal, t.status,
                    (t.notes or "")[:20],
                ), tags=(tag,))

        def _on_tree_select(_e=None):
            sel = tree.selection()
            if sel:
                # Strip _max suffix to get real trade_id
                raw = sel[0]
                self._selected_trade = raw[:-4] if raw.endswith("_max") else raw

        tree.bind("<<TreeviewSelect>>", _on_tree_select)
        _rebuild_tree(trades)   # initial populate

    def _render_max_messages(self, parent):
        """Expanded scanner messages log."""
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        tb = tk.Frame(parent, bg=TOP)
        tb.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        tk.Button(tb, text="Clear", bg=PANEL, fg=MUTED,
            relief="flat", font=FS, padx=8,
            command=lambda: self._max_msg_text.configure(state="normal") or
                self._max_msg_text.delete("1.0","end") or
                self._max_msg_text.configure(state="disabled")
                if hasattr(self,"_max_msg_text") else None
            ).pack(side="right", padx=4)
        mf = tk.Frame(parent, bg=PANEL)
        mf.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        mf.grid_rowconfigure(0, weight=1)
        mf.grid_columnconfigure(0, weight=1)
        txt = tk.Text(mf, bg=PANEL_DARK, fg=GREEN, font=FM,
            state="disabled", wrap="word", relief="flat")
        vsb = tk.Scrollbar(mf, command=txt.yview)
        txt.configure(yscrollcommand=vsb.set)
        txt.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        self._max_msg_text = txt
        # Copy existing log content
        try:
            existing = self._log_text.get("1.0", "end")
            txt.configure(state="normal")
            txt.insert("end", existing)
            txt.configure(state="disabled")
            txt.see("end")
        except Exception:
            pass

    def _render_max_performance(self, parent):
        """Expanded performance panel with export button."""
        parent.grid_rowconfigure(0, weight=0)
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        # Toolbar
        tb = tk.Frame(parent, bg=TOP)
        tb.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        def _export_perf():
            try:
                path = self._paper_engine.export_performance_csv()
                if path:
                    self._safe_log(f"Performance exported → {path}")
                else:
                    self._safe_log("Performance export failed.")
            except Exception as exc:
                self._safe_log(f"Export error: {exc}")
        tk.Button(tb, text="Export Performance CSV", bg=PANEL, fg=CYAN,
            relief="flat", font=FS, padx=10, pady=4,
            command=_export_perf).pack(side="right", padx=4)

        pf = tk.Frame(parent, bg=PANEL)
        pf.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        try:
            perf = self._paper_engine.performance_summary()
            stats = [
                ("Total paper trades",  perf.get("total","—")),
                ("Open trades",         perf.get("open","—")),
                ("Closed trades",       perf.get("closed","—")),
                ("Wins",                perf.get("wins","—")),
                ("Win rate",            perf.get("win_rate","—")),
                ("Realized P/L",        perf.get("total_pl","—")),
                ("Unrealized P/L",      perf.get("unrealized","—")),
                ("Avg P/L",             perf.get("avg_pl","—")),
                ("Best trade",          perf.get("best_trade","—")),
                ("Worst trade",         perf.get("worst_trade","—")),
            ]
            tk.Label(pf, text="PAPER PERFORMANCE", bg=PANEL, fg=CYAN,
                font=("Segoe UI", 12, "bold"), pady=12, anchor="w",
                padx=16).pack(fill="x")
            for label, val in stats:
                row = tk.Frame(pf, bg=PANEL)
                row.pack(fill="x", padx=16, pady=3)
                tk.Label(row, text=label, bg=PANEL, fg=MUTED,
                    font=FS, width=20, anchor="w").pack(side="left")
                col = TEXT
                val_s = str(val)
                if "$+" in val_s: col = GREEN
                elif "$-" in val_s: col = RED
                tk.Label(row, text=val_s, bg=PANEL, fg=col,
                    font=("Consolas", 11, "bold"), anchor="w").pack(side="left")
        except Exception as exc:
            tk.Label(pf, text=f"Performance error: {exc}",
                bg=PANEL, fg=RED, font=FS, padx=16).pack()

    def _render_max_filters(self, parent):
        """Expanded Filters & Settings — read-only view of current scanner state."""
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=0)
        parent.grid_columnconfigure(1, weight=1)

        def _section_header(p, text):
            tk.Label(p, text=text, bg=PANEL, fg=CYAN,
                font=("Segoe UI", 9, "bold"), anchor="w",
                padx=8, pady=4).pack(fill="x")

        def _info_row(p, label, val, col=None):
            row = tk.Frame(p, bg=PANEL)
            row.pack(fill="x", padx=12, pady=2)
            tk.Label(row, text=label, bg=PANEL, fg=MUTED,
                font=FS, width=22, anchor="w").pack(side="left")
            tk.Label(row, text=str(val), bg=PANEL, fg=(col or TEXT),
                font=FM, anchor="w").pack(side="left")

        lf = tk.Frame(parent, bg=PANEL)
        lf.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        import scanner_config as cfg_mod

        _section_header(lf, "DATA & CONNECTION")
        _info_row(lf, "Data mode",        cfg_mod.effective_mode())
        _info_row(lf, "Kalshi env",        cfg_mod.KALSHI_ENV)
        _info_row(lf, "Kalshi ready",      "YES" if cfg_mod.kalshi_auth_ready() else "NO")
        _info_row(lf, "Auth status",       self.data_layer._last_source or "—")

        tk.Frame(lf, bg=BORDER, height=1).pack(fill="x", padx=6, pady=6)
        _section_header(lf, "SAFETY STATUS")
        _info_row(lf, "Auto trading",      "OFF (hardcoded)", RED)
        _info_row(lf, "Paper mode",        "ON", GREEN)
        _info_row(lf, "Risk guard",        "ON", GREEN)

        tk.Frame(lf, bg=BORDER, height=1).pack(fill="x", padx=6, pady=6)
        _section_header(lf, "CURRENT FILTERS")
        _info_row(lf, "Signal filter",
            getattr(self, "v_signal_filter", None) and
            self.v_signal_filter.get() or "All")
        _info_row(lf, "Category filter",
            getattr(self, "v_category_filter", None) and
            self.v_category_filter.get() or "All")
        _info_row(lf, "Data mode sel.",
            getattr(self, "v_data_mode", None) and
            self.v_data_mode.get() or "—")
        _info_row(lf, "Max trade size",
            f"${getattr(self, 'v_max_size', None) and self.v_max_size.get() or 0:.0f}")
        _info_row(lf, "Min edge",
            f"{getattr(self, 'v_min_edge', None) and self.v_min_edge.get() or 0:.1f}c")
        _info_row(lf, "Max spread",
            f"{getattr(self, 'v_max_spread', None) and self.v_max_spread.get() or 0:.1f}c")
        _info_row(lf, "Crypto source",
            getattr(self, "v_crypto_src", None) and
            self.v_crypto_src.get() or "auto")

        tk.Frame(lf, bg=BORDER, height=1).pack(fill="x", padx=6, pady=6)
        _section_header(lf, "SCANNER STATE")
        _info_row(lf, "Markets loaded",   str(len(self.signals)))
        _info_row(lf, "Last source",      self.data_layer._last_source or "—")
        _info_row(lf, "Last update",      self.data_layer._last_update or "—")
        _info_row(lf, "Watchlist items",  str(len(self._watchlist.all_entries())))
        open_trades = len(self._paper_engine.open_trades())
        _info_row(lf, "Open paper trades",str(open_trades))

        tk.Label(lf,
            text=("Settings are read-only in maximized view.\n"
                  "Change settings in the normal left panel."),
            bg="#1a1a2e", fg=YELLOW, font=FS,
            padx=10, pady=8, justify="left").pack(fill="x", padx=4, pady=8)

    def _render_max_crypto(self, parent):
        """Expanded crypto prices panel."""
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)
        for col_i, (sym, col) in enumerate([("BTC", ORANGE), ("ETH", "#818cf8")]):
            card = tk.Frame(parent, bg=PANEL)
            card.grid(row=0, column=col_i, sticky="nsew", padx=8, pady=8)
            snap = self._crypto_prices.get(sym)
            tk.Label(card, text=sym, bg=PANEL, fg=col,
                font=("Segoe UI", 24, "bold"), pady=16).pack()
            if snap and snap.price:
                tk.Label(card, text=snap.price_str,
                    bg=PANEL, fg=GREEN if snap.status=="ok" else YELLOW,
                    font=("Consolas", 20, "bold")).pack()
                for label, val in [
                    ("Bid",     f"${snap.bid:,.2f}" if snap.bid else "N/A"),
                    ("Ask",     f"${snap.ask:,.2f}" if snap.ask else "N/A"),
                    ("Source",  snap.source),
                    ("Updated", snap.timestamp[11:16] if snap.timestamp else "N/A"),
                    ("Status",  snap.status),
                    ("1m chg",  "— (not tracked yet)"),
                    ("5m chg",  "— (not tracked yet)"),
                ]:
                    row = tk.Frame(card, bg=PANEL)
                    row.pack(fill="x", padx=20, pady=2)
                    tk.Label(row, text=label, bg=PANEL, fg=MUTED,
                        font=FS, width=10, anchor="w").pack(side="left")
                    tk.Label(row, text=val, bg=PANEL, fg=TEXT,
                        font=FM, anchor="w").pack(side="left")
            else:
                tk.Label(card, text="N/A", bg=PANEL, fg=MUTED,
                    font=("Consolas", 20, "bold")).pack()
                tk.Label(card, text="Mock/placeholder prices",
                    bg=PANEL, fg=MUTED, font=FS).pack(pady=8)
            tk.Button(card, text="↻ Refresh", bg="#0e7490", fg=TEXT,
                relief="flat", font=FS, padx=12, pady=4,
                command=self._refresh_crypto).pack(pady=12)

    def _on_signal_filter_change(self):
        """Re-populate tree when signal filter changes."""
        self._populate_tree()

    def _on_category_filter_change(self):
        """Re-populate tree when category filter changes."""
        self._populate_tree()

    def _filtered_signals(self):
        """Return signals filtered by signal and category filter dropdowns."""
        f    = self.v_signal_filter.get()   if hasattr(self, 'v_signal_filter')   else "All"
        cat  = self.v_category_filter.get() if hasattr(self, 'v_category_filter') else "All"
        sigs = self.signals

        # Apply category filter first
        if cat and cat != "All":
            CRYPTO_CATS = {"Crypto", "BTC", "ETH", "Bitcoin", "Ethereum"}
            if cat == "Crypto":
                sigs = [s for s in sigs if s.category in CRYPTO_CATS or
                        any(x in s.market_name.upper() for x in ("BTC","ETH","BITCOIN","ETHEREUM","CRYPTO"))]
            elif cat == "Other":
                known = {"Economics","Politics","Weather","Crypto","BTC","ETH"}
                sigs = [s for s in sigs if s.category not in known and
                        not any(x in s.market_name.upper() for x in ("BTC","ETH","BITCOIN"))]
            else:
                sigs = [s for s in sigs if s.category == cat]

        # Apply signal filter
        if f == "All":
            return sigs
        WATCH_PLUS  = {"WATCH","PAPER ONLY","POSSIBLE EDGE","ENTRY","STRONG ENTRY"}
        POSS_EDGE   = {"POSSIBLE EDGE","ENTRY","STRONG ENTRY"}
        DATA_NEEDED = {"DATA NEEDED"}
        AVOID       = {"AVOID","NO TRADE"}
        if f == "Watch+":       return [s for s in sigs if s.signal in WATCH_PLUS]
        if f == "Possible Edge":return [s for s in sigs if s.signal in POSS_EDGE]
        if f == "Data Needed":  return [s for s in sigs if s.signal in DATA_NEEDED]
        if f == "Avoid":        return [s for s in sigs if s.signal in AVOID]
        return sigs

    def _safe_log(self, msg: str):
        """Log safely — buffers if widget not built yet."""
        if self._log_text is None:
            self._log_queue.append(msg)
        else:
            self._write_log(msg)

    def _write_log(self, msg: str):
        try:
            ts = datetime.now().strftime("%H:%M:%S")
            self._log_text.configure(state="normal")
            self._log_text.insert("end", f"[{ts}] {msg}\n")
            self._log_text.see("end")
            self._log_text.configure(state="disabled")
        except Exception:
            pass

    def _clear(self, widget):
        for w in widget.winfo_children():
            w.destroy()

