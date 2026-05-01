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
        self._build_header()
        self._build_body()

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

    def _panel(self, parent, title):
        outer = tk.Frame(parent, bg=BG,
            highlightbackground=BORDER, highlightthickness=1)
        outer.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        outer.grid_rowconfigure(1, weight=1)
        outer.grid_columnconfigure(0, weight=1)
        tk.Label(outer, text=title, bg=BG, fg=CYAN,
            font=FB, padx=8, pady=5, anchor="w").grid(row=0, column=0, sticky="ew")
        body = tk.Frame(outer, bg=PANEL)
        body.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        return body

    # ── LEFT: Filters + status ─────────────────────────────────────────────

    def _build_left(self, p):
        body = self._panel(p, "FILTERS & SETTINGS")
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
        p.grid_rowconfigure(1, weight=0)
        p.grid_columnconfigure(0, weight=1)

        # ── Top: Signal Scanner table ─────────────────────────────────
        top = tk.Frame(p, bg=BG,
            highlightbackground=BORDER, highlightthickness=1)
        top.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        top.grid_rowconfigure(1, weight=1)
        top.grid_columnconfigure(0, weight=1)

        tk.Label(top, text="SIGNAL SCANNER", bg=BG, fg=CYAN,
            font=FB, padx=8, pady=5, anchor="w").grid(row=0, column=0, sticky="ew")

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

        # ── Bottom-center: Watchlist / Alerts / Candidates tabs ───────
        self._build_center_tabs(p)

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
                   "Expiry","Target","Ref Price","Status")
        col_w   = {"Market":130,"Side":40,"Bid":40,"Ask":40,"Last":40,
                   "Signal":90,"Expiry":80,"Target":65,"Ref Price":80,"Status":55}

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

        tk.Label(outer, text="SIGNAL DETAIL", bg=BG, fg=CYAN,
            font=FB, padx=8, pady=5, anchor="w").grid(row=0, column=0, sticky="ew")

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
        _row(f1, "Title",    sig.market_name, TEXT)
        _row(f1, "Ticker",   sig.market_id)
        _row(f1, "Category", sig.category)
        _row(f1, "Source",   self.data_layer._last_source or "—")
        _row(f1, "Volume",   f"{sig.volume:,}" if sig.volume else "N/A")

        # ── 2. Kalshi Quote ───────────────────────────────────────────
        f2 = _section("2  KALSHI QUOTE")
        _row(f2, "Side",     sig.side, CYAN)
        _row(f2, "Bid",      format_cents(sig.bid_price)  if sig.bid_price  else "N/A")
        _row(f2, "Ask",      format_cents(sig.ask_price)  if sig.ask_price  else "N/A")
        _row(f2, "Last",     format_cents(sig.last_price) if sig.last_price else "N/A")
        _row(f2, "Spread",   format_cents(sig.spread)     if sig.spread     else "N/A")
        _row(f2, "Liquidity",sig.liquidity)
        _row(f2, "Data Qual.",sig.data_quality)

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

        # ── 4. Fee / Breakeven ────────────────────────────────────────
        f4 = _section("4  FEE / BREAKEVEN")
        ask = sig.ask_price or 0
        if ask > 0:
            from paper_trade_engine import contracts_for_budget, kalshi_fee, breakeven_price
            max_size = self.v_max_size.get()
            n      = contracts_for_budget(max_size, ask)
            fee    = kalshi_fee(max(n,1), ask)
            be     = breakeven_price(ask, max(n,1))
            _row(f4, "Entry ask",  format_cents(ask))
            _row(f4, "Contracts",  str(n))
            _row(f4, "Buy fee",    f"{fee:.0f}c")
            _row(f4, "Breakeven",  f"{be:.1f}c")
            _row(f4, "Max risk",   f"${max_size:.0f}")
        else:
            _row(f4, "Status", "Load Orderbook to see prices", YELLOW)

        # ── 5. Signal / Trade Plan ────────────────────────────────────
        f5 = _section("5  SIGNAL")
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

        # ── 6. Action buttons ─────────────────────────────────────────
        bf = tk.Frame(inner, bg=PANEL)
        bf.pack(fill="x", padx=4, pady=4)
        for text, bg, cmd in [
            ("Add to Watchlist",   PURPLE,    lambda s=sig: self._add_watchlist(s)),
            ("Create Paper Trade", GREEN_DARK, lambda s=sig: self._paper_trade(s)),
            ("Exit Paper Trade",   "#0e7490",  self._exit_selected_paper_trade),
            ("Mark as Avoid",      RED_DARK,   lambda s=sig: self._mark_avoid(s)),
            ("Export Signal",      GRAY_BTN,   lambda s=sig: self._export_signal(s)),
        ]:
            tk.Button(bf, text=text, bg=bg, fg=TEXT,
                activebackground=bg, relief="flat", font=FS,
                pady=5, command=cmd).pack(fill="x", pady=1)

        tk.Label(inner, text="AUTO TRADING: OFF — Paper only",
            bg="#1a0000", fg=RED, font=FS, pady=3).pack(fill="x")

    def _build_bottom(self, p):
        """Bottom area: tabbed — Paper Trades | Scanner Messages | Crypto Prices | Performance."""
        outer = tk.Frame(p, bg=BG,
            highlightbackground=BORDER, highlightthickness=1)
        outer.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        outer.grid_rowconfigure(1, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        tk.Label(outer, text="WORKSPACE", bg=BG, fg=CYAN,
            font=FB, padx=8, pady=4, anchor="w").grid(row=0, column=0, sticky="ew")

        # Tab notebook
        style = ttk.Style()
        style.configure("Bottom.TNotebook", background=BG, borderwidth=0)
        style.configure("Bottom.TNotebook.Tab",
            background=PANEL, foreground=MUTED, padding=[8,3], font=FS)
        style.map("Bottom.TNotebook.Tab",
            background=[("selected", PANEL_DARK)],
            foreground=[("selected", CYAN)])

        nb = ttk.Notebook(outer, style="Bottom.TNotebook")
        nb.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

        # ── Tab 1: Paper Trades ────────────────────────────────────────
        pt_frame = tk.Frame(nb, bg=PANEL_DARK)
        nb.add(pt_frame, text="  Paper Trades  ")
        pt_frame.grid_rowconfigure(0, weight=1)
        pt_frame.grid_columnconfigure(0, weight=1)

        lf = tk.Frame(pt_frame, bg=PANEL)
        lf.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        lf.grid_rowconfigure(0, weight=1)
        lf.grid_columnconfigure(0, weight=1)

        pt_cols = ("Time","Market","Side","Entry","Contr","Fee",
                   "Target","Current","P/L","Status")
        self.pt_tree = ttk.Treeview(lf, columns=pt_cols,
            show="headings", style="Scanner.Treeview", height=5)
        pt_w = {"Time":65,"Market":140,"Side":40,"Entry":45,"Contr":45,
                "Fee":40,"Target":50,"Current":55,"P/L":55,"Status":55}
        for col in pt_cols:
            self.pt_tree.heading(col, text=col)
            self.pt_tree.column(col, width=pt_w.get(col,60),
                anchor="center", stretch=False)
        self.pt_tree.column("Market", anchor="w", stretch=True)
        vsb2 = ttk.Scrollbar(lf, orient="vertical", command=self.pt_tree.yview)
        self.pt_tree.configure(yscrollcommand=vsb2.set)
        self.pt_tree.grid(row=0, column=0, sticky="nsew")
        vsb2.grid(row=0, column=1, sticky="ns")

        # ── Tab 2: Scanner Messages ────────────────────────────────────
        msg_frame = tk.Frame(nb, bg=PANEL_DARK)
        nb.add(msg_frame, text="  Scanner Messages  ")
        msg_frame.grid_rowconfigure(0, weight=1)
        msg_frame.grid_columnconfigure(0, weight=1)

        rf = tk.Frame(msg_frame, bg=PANEL)
        rf.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        rf.grid_rowconfigure(0, weight=1)
        rf.grid_columnconfigure(0, weight=1)

        self._log_text = tk.Text(rf, bg=PANEL_DARK, fg=GREEN,
            font=FM, state="disabled", wrap="word",
            insertbackground=TEXT, relief="flat")
        lsb = tk.Scrollbar(rf, command=self._log_text.yview)
        self._log_text.configure(yscrollcommand=lsb.set)
        self._log_text.grid(row=0, column=0, sticky="nsew")
        lsb.grid(row=0, column=1, sticky="ns")

        # ── Tab 3: Crypto Prices ───────────────────────────────────────
        crypto_frame = tk.Frame(nb, bg=PANEL_DARK)
        nb.add(crypto_frame, text="  Crypto Prices  ")
        self._build_crypto_tab(crypto_frame)

        # ── Tab 4: Performance ─────────────────────────────────────────
        perf_frame = tk.Frame(nb, bg=PANEL_DARK)
        nb.add(perf_frame, text="  Performance  ")
        self._build_perf_tab(perf_frame)

        # Flush buffered logs after widgets exist
        for msg in self._log_queue:
            self._write_log(msg)
        self._log_queue.clear()

    def _build_crypto_tab(self, p):
        """Crypto Prices tab content."""
        p.grid_rowconfigure(0, weight=1)
        p.grid_columnconfigure(0, weight=1)
        p.grid_columnconfigure(1, weight=1)

        for col_i, (sym, entries, col) in enumerate([
            ("BTC", [("Price","btc_price"),("Bid","btc_bid"),("Ask","btc_ask"),
                     ("Source","btc_src"),("Updated","btc_ts")], ORANGE),
            ("ETH", [("Price","eth_price"),("Bid","eth_bid"),("Ask","eth_ask"),
                     ("Source","eth_src"),("Updated","eth_ts")], "#818cf8"),
        ]):
            card = tk.Frame(p, bg=PANEL)
            card.grid(row=0, column=col_i, sticky="nsew", padx=6, pady=6)
            tk.Label(card, text=sym, bg=PANEL, fg=col, font=FB,
                pady=6, padx=8).pack(fill="x")
            for label, key in entries:
                row = tk.Frame(card, bg=PANEL)
                row.pack(fill="x", padx=8, pady=2)
                tk.Label(row, text=label, bg=PANEL, fg=MUTED,
                    font=FS, width=10, anchor="w").pack(side="left")
                lbl = tk.Label(row, text="—", bg=PANEL, fg=TEXT,
                    font=FM, anchor="w")
                lbl.pack(side="left")
                self._crypto_labels[key] = lbl

    def _build_perf_tab(self, p):
        """Performance tab content."""
        p.grid_rowconfigure(0, weight=1)
        p.grid_columnconfigure(0, weight=1)
        p.grid_columnconfigure(1, weight=1)

        stats = [
            ("Total trades", "total"),     ("Open",        "open"),
            ("Closed",       "closed"),    ("Win rate",    "win_rate"),
            ("Total P/L",    "total_pl"),  ("Unrealized",  "unrealized"),
            ("Avg P/L",      "avg_pl"),    ("Best trade",  "best_trade"),
            ("Worst trade",  "worst_trade"),
        ]
        lf = tk.Frame(p, bg=PANEL)
        lf.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=6, pady=6)
        tk.Label(lf, text="PAPER PERFORMANCE", bg=PANEL, fg=CYAN,
            font=FB, anchor="w", padx=8, pady=6).pack(fill="x")
        for label, key in stats:
            row = tk.Frame(lf, bg=PANEL)
            row.pack(fill="x", padx=8, pady=2)
            tk.Label(row, text=label, bg=PANEL, fg=MUTED,
                font=FS, width=14, anchor="w").pack(side="left")
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

            # Update watchlist from live signal data
            self._watchlist.update_from_signals(self.signals)
            self._refresh_wl_tree()

            # Refresh crypto reference in background
            self._refresh_crypto()

        except Exception as e:
            self._safe_log(f"Refresh error: {e}")
            self._update_status_box()

    def _populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        if not self.signals:
            return
        data_src = self.data_layer._last_source or "mock"
        for sig in self.signals:
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
        from crypto_price_connectors import parse_crypto_market_title
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

    def _wl_clear_stale(self):
        """Clear STALE/EXPIRED watchlist entries."""
        self._watchlist.clear_stale()
        self._refresh_wl_tree()

    def _refresh_wl_tree(self):
        """Rebuild watchlist treeview from engine."""
        try:
            self.wl_tree.delete(*self.wl_tree.get_children())
            entries = self._watchlist.all_entries()
            for e in entries:
                tag = "stale" if e.status in ("STALE","EXPIRED") else "active"
                ref_str = f"${e.reference_price:,.0f}" if e.reference_price else "N/A"
                self.wl_tree.insert("", "end", iid=e.ticker, values=(
                    e.title[:22], e.side,
                    e.bid_str, e.ask_str, e.last_str,
                    e.signal, e.expiration or "N/A",
                    e.target_str, ref_str, e.status,
                ), tags=(tag,))
            if hasattr(self, '_wl_count_lbl'):
                self._wl_count_lbl.config(
                    text=f"{len(entries)} item{'s' if len(entries) != 1 else ''}")
        except Exception as ex:
            print(f"[wl_tree] {ex}")



    def _mark_avoid(self, sig):
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
        """Update all crypto labels — right-panel card and bottom tab."""
        try:
            btc = self._crypto_prices.get("BTC")
            eth = self._crypto_prices.get("ETH")

            # Right-panel summary labels
            for sym, snap in [("BTC", btc), ("ETH", eth)]:
                lbl = self._crypto_labels.get(sym)
                if lbl:
                    if snap and snap.price:
                        lbl.config(text=snap.price_str,
                            fg=GREEN if snap.status=="ok" else YELLOW)
                    else:
                        lbl.config(text="N/A", fg=MUTED)
            any_snap = btc or eth
            if any_snap:
                if self._crypto_labels.get("src"):
                    self._crypto_labels["src"].config(text=any_snap.source)
                if self._crypto_labels.get("updated"):
                    self._crypto_labels["updated"].config(
                        text=any_snap.timestamp[11:16] if any_snap.timestamp else "")

            # Bottom crypto tab detailed labels
            def _upd(key, value, col=None):
                lbl = self._crypto_labels.get(key)
                if lbl:
                    lbl.config(text=value or "N/A")
                    if col:
                        lbl.config(fg=col)

            if btc:
                _upd("btc_price", btc.price_str,
                     GREEN if btc.status == "ok" else YELLOW)
                _upd("btc_bid",   f"${btc.bid:,.2f}"  if btc.bid  else "N/A")
                _upd("btc_ask",   f"${btc.ask:,.2f}"  if btc.ask  else "N/A")
                _upd("btc_src",   btc.source)
                _upd("btc_ts",    btc.timestamp[11:16] if btc.timestamp else "N/A")
            if eth:
                _upd("eth_price", eth.price_str,
                     GREEN if eth.status == "ok" else YELLOW)
                _upd("eth_bid",   f"${eth.bid:,.2f}"  if eth.bid  else "N/A")
                _upd("eth_ask",   f"${eth.ask:,.2f}"  if eth.ask  else "N/A")
                _upd("eth_src",   eth.source)
                _upd("eth_ts",    eth.timestamp[11:16] if eth.timestamp else "N/A")

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
        """Create paper trade via PaperTradeEngine. No real orders."""
        if sig.ask_price <= 0:
            self._safe_log("Cannot create paper trade — no valid entry price (ask = N/A).")
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
        """Exit the selected paper trade at current bid."""
        if not self._selected_trade:
            self._safe_log("Select a paper trade row first to exit it.")
            return
        trade_id = self._selected_trade
        # Find the trade and use current bid as exit price
        trade = self._paper_engine._find(trade_id)
        if trade is None:
            return
        exit_price = trade.current_price   # use last known price as exit
        self._paper_engine.exit_trade(trade_id, exit_price, reason="Manual exit")
        self._update_pt_tree()
        self._update_performance()

    def _update_pt_tree(self):
        """Refresh paper trade log from engine."""
        try:
            self.pt_tree.delete(*self.pt_tree.get_children())
            for t in reversed(self._paper_engine.all_trades()):
                pl = t.pl_str
                pl_col = "win" if "+" in pl else "loss" if "-" in pl else "neutral"
                self.pt_tree.insert("", "end", iid=t.trade_id, values=(
                    t.time_opened[11:19],  # time HH:MM:SS
                    t.market[:20] if hasattr(t,'market') else t.ticker[:20],
                    t.side,
                    f"{t.entry_price:.0f}c",
                    str(t.contracts),
                    f"{t.buy_fee:.0f}c",
                    f"{t.target_exit:.0f}c",
                    f"{t.current_price:.0f}c",
                    pl,
                    t.status,
                ))
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
        """Refresh performance summary labels."""
        try:
            perf = self._paper_engine.performance_summary()
            col_map = {"+": GREEN, "-": RED}
            for key, lbl in self._perf_labels.items():
                val = str(perf.get(key, "—"))
                col = TEXT
                if val.startswith("$+"):  col = GREEN
                elif val.startswith("$-"): col = RED
                lbl.config(text=val, fg=col)
        except Exception as e:
            print(f"[perf] {e}")

    # ── Source change handler ──────────────────────────────────────────────

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
