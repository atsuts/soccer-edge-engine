"""
ai_market_scanner.py
AI Market Scanner screen — resizable panels, paper trading only.
Uses DataLayer for all market data (mock or live).
AUTO TRADING is always OFF.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime

from market_scanner_engine import (
    RiskGuard, run_scanner, PaperTrade,
    calculate_contracts, calculate_kalshi_fee,
)
from market_connectors import DataLayer
import scanner_config as cfg

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
    "MOCK":             CYAN,
    "KALSHI_LIVE":      GREEN,
    "HYBRID":           ORANGE,
    "MOCK (fallback)":  YELLOW,
    "MOCK (error fallback)": RED,
}


class AIMarketScannerFrame(tk.Frame):

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)

        self.data_layer      = DataLayer(log_fn=self._log)
        self.risk_guard      = RiskGuard()
        self.signals         = []
        self.paper_trades    = []
        self.selected_signal = None
        self.scan_job        = None
        self.scanning        = False

        self._v_pane = None
        self._h_pane = None

        # Filter / settings vars
        self.v_data_mode   = tk.StringVar(value=cfg.effective_mode())
        self.v_category    = tk.StringVar(value="All")
        self.v_timeframe   = tk.StringVar(value="Live")
        self.v_min_edge    = tk.DoubleVar(value=cfg.SCANNER_MIN_EDGE)
        self.v_max_spread  = tk.DoubleVar(value=cfg.SCANNER_MAX_SPREAD)
        self.v_max_size    = tk.DoubleVar(value=cfg.SCANNER_MAX_TRADE_SIZE)
        self.v_daily_loss  = tk.DoubleVar(value=cfg.SCANNER_DAILY_LOSS)

        # Status label refs (set during build)
        self._status_labels = {}

        self._build()
        self.after(350, lambda: self.apply_layout("default"))
        self.after(150, self._initial_load)

    # ── Layout ────────────────────────────────────────────────────────────

    def apply_layout(self, preset):
        if not self._h_pane or not self._v_pane:
            return
        try:
            self.update_idletasks()
            hw = self._h_pane.winfo_width()
            vh = self._v_pane.winfo_height()
            if hw <= 1 or vh <= 1:
                self.after(120, lambda: self.apply_layout(preset))
                return
            lf, cf, vf = SCANNER_LAYOUTS.get(preset, SCANNER_LAYOUTS["default"])
            self._h_pane.sash_place(0, int(hw * lf), 0)
            self._h_pane.sash_place(1, int(hw * cf), 0)
            self._v_pane.sash_place(0, 0, int(vh * vf))
        except Exception as e:
            print(f"[scanner layout] {e}")

    # ── Build ─────────────────────────────────────────────────────────────

    def _build(self):
        self.grid_rowconfigure(1, weight=1)
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
            text="Fee-adjusted edge scanner — Kalshi binary, soccer odds, crypto signals",
            bg=TOP, fg=MUTED, font=FS).pack(anchor="w")

        chips = tk.Frame(hdr, bg=TOP)
        chips.pack(side="right", padx=14, pady=8)

        # Data mode chip (dynamic)
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
        # Vertical PanedWindow: top dashboard | bottom log
        self._v_pane = tk.PanedWindow(self, orient="vertical",
            bg="#22d3ee", sashwidth=8, sashrelief="raised",
            opaqueresize=True, showhandle=True, handlesize=12, handlepad=80)
        self._v_pane.grid(row=1, column=0, sticky="nsew")

        top_area    = tk.Frame(self._v_pane, bg=BG)
        bottom_area = tk.Frame(self._v_pane, bg=BG)
        self._v_pane.add(top_area,    minsize=250, sticky="nsew")
        self._v_pane.add(bottom_area, minsize=100, sticky="nsew")

        # Horizontal PanedWindow: left | center | right
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

        self._h_pane.add(lf, minsize=160, sticky="nsew")
        self._h_pane.add(cf, minsize=350, sticky="nsew")
        self._h_pane.add(rf, minsize=180, sticky="nsew")

        self._build_left(lf)
        self._build_center(cf)
        self._build_right(rf)
        self._build_bottom(bottom_area)

    # ── LEFT: Filters + status ────────────────────────────────────────────

    def _build_left(self, p):
        outer = tk.Frame(p, bg=BG,
            highlightbackground=BORDER, highlightthickness=1)
        outer.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        outer.grid_rowconfigure(1, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        tk.Label(outer, text="FILTERS & SETTINGS", bg=BG, fg=CYAN,
            font=FB, padx=8, pady=5, anchor="w").grid(row=0, column=0, sticky="ew")

        body = tk.Frame(outer, bg=PANEL)
        body.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

        def row_w(label, widget_fn):
            f = tk.Frame(body, bg=PANEL)
            f.pack(fill="x", padx=8, pady=3)
            tk.Label(f, text=label, bg=PANEL, fg=CYAN,
                font=FS, anchor="w").pack(fill="x")
            widget_fn(f).pack(fill="x", pady=2)

        def combo(var, vals):
            return lambda par: ttk.Combobox(par, textvariable=var,
                values=vals, state="readonly", font=FS, height=8)

        def spin(var, lo, hi, inc):
            return lambda par: tk.Spinbox(par, textvariable=var,
                from_=lo, to=hi, increment=inc,
                bg=PANEL_DARK, fg=TEXT, buttonbackground=PANEL_DARK,
                insertbackground=TEXT, relief="flat", font=FS)

        # Data mode selector
        row_w("Data Mode", combo(self.v_data_mode,
            ["MOCK", "KALSHI_LIVE", "HYBRID"]))
        self.v_data_mode.trace_add("write", self._on_mode_change)

        row_w("Category", combo(self.v_category,
            ["All","Crypto","Sports","Politics","Economics","Soccer","Watchlist"]))
        row_w("Timeframe", combo(self.v_timeframe,
            ["Live","15 min","1 hour","Today","Upcoming"]))

        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", padx=8, pady=6)

        row_w("Min Edge (cents)",    spin(self.v_min_edge, 0, 50, 1))
        row_w("Max Spread (cents)",  spin(self.v_max_spread, 0, 20, 1))
        row_w("Max Trade Size ($)",  spin(self.v_max_size, 1, 100, 1))
        row_w("Daily Loss Limit ($)",spin(self.v_daily_loss, 5, 200, 5))

        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", padx=8, pady=6)

        for text, bg, cmd in [
            ("Refresh Data",     CYAN_DARK,  self._refresh),
            ("Start Paper Scan", GREEN_DARK, self._start_scan),
            ("Stop Scan",        GRAY_BTN,   self._stop_scan),
            ("Reset Filters",    RED_DARK,   self._reset_filters),
        ]:
            tk.Button(body, text=text, bg=bg, fg=TEXT,
                activebackground=bg, relief="flat", font=FB,
                pady=6, command=cmd).pack(fill="x", padx=8, pady=2)

        # ── Source status box ──────────────────────────────────────────
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", padx=8, pady=6)
        tk.Label(body, text="SOURCE STATUS", bg=PANEL, fg=CYAN,
            font=FB, anchor="w").pack(fill="x", padx=8, pady=2)

        status_frame = tk.Frame(body, bg=PANEL_DARK)
        status_frame.pack(fill="x", padx=8, pady=4)

        status_rows = [
            ("Data Mode",     "data_mode"),
            ("Last Update",   "last_update"),
            ("Kalshi",        "kalshi"),
            ("Odds API",      "odds_api"),
            ("Football API",  "football_api"),
            ("Auto Trading",  "auto_trading"),
            ("Risk Guard",    "risk_guard"),
        ]
        for lbl, key in status_rows:
            row = tk.Frame(status_frame, bg=PANEL_DARK)
            row.pack(fill="x", padx=6, pady=1)
            tk.Label(row, text=lbl, bg=PANEL_DARK, fg=MUTED,
                font=FS, width=13, anchor="w").pack(side="left")
            val_lbl = tk.Label(row, text="—", bg=PANEL_DARK, fg=TEXT,
                font=FM, anchor="w")
            val_lbl.pack(side="left")
            self._status_labels[key] = val_lbl

        tk.Label(body,
            text="AUTO TRADING: OFF\nPaper mode only. No real orders.",
            bg=PANEL_DARK, fg=RED, font=FM,
            justify="left", padx=8, pady=6, anchor="w").pack(
            fill="x", padx=8, pady=6)

        self._update_status_box()

    def _update_status_box(self):
        """Refresh the source status labels."""
        try:
            st = self.data_layer.status()
            colors = {
                "Ready": GREEN, "ON": GREEN,
                "No key": RED, "OFF": RED,
                "Never": MUTED,
            }
            for key, lbl in self._status_labels.items():
                val = str(st.get(key, "—"))
                col = colors.get(val, CYAN if key == "data_mode" else TEXT)
                lbl.config(text=val, fg=col)
        except Exception:
            pass

    def _on_mode_change(self, *_):
        """Called when user changes Data Mode dropdown."""
        selected = self.v_data_mode.get()
        os_key   = "DATA_MODE"
        import os
        os.environ[os_key] = selected
        mode = cfg.effective_mode()
        self._mode_chip.config(
            text=f"MODE: {mode}",
            fg=MODE_COLORS.get(mode, CYAN))
        if selected == "KALSHI_LIVE" and not cfg.kalshi_ready():
            self._log("Kalshi live selected but API key not configured.")
            self._log("Add KALSHI_API_KEY and KALSHI_PRIVATE_KEY_PATH to .env")
            self._log("Falling back to MOCK data.")
        elif selected == "KALSHI_LIVE":
            self._log("Kalshi live mode selected.")
        else:
            self._log(f"Data mode set to: {selected}")

    # ── CENTER: Scanner table ─────────────────────────────────────────────

    def _build_center(self, p):
        outer = tk.Frame(p, bg=BG,
            highlightbackground=BORDER, highlightthickness=1)
        outer.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        outer.grid_rowconfigure(1, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        tk.Label(outer, text="SIGNAL SCANNER", bg=BG, fg=CYAN,
            font=FB, padx=8, pady=5, anchor="w").grid(row=0, column=0, sticky="ew")

        tf = tk.Frame(outer, bg=PANEL)
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
            background=[("selected","#1e3a5f")],
            foreground=[("selected",TEXT)])

        self.tree = ttk.Treeview(tf, columns=cols, show="headings",
            style="Scanner.Treeview", selectmode="browse")
        for col in cols:
            self.tree.heading(col, text=col,
                command=lambda c=col: self._sort_tree(c))
            self.tree.column(col, width=col_w.get(col,60),
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
            self.tree.tag_configure(sig.replace(" ","_"),
                background=colors["bg"], foreground=colors["fg"])

    # ── RIGHT: Signal detail ──────────────────────────────────────────────

    def _build_right(self, p):
        outer = tk.Frame(p, bg=BG,
            highlightbackground=BORDER, highlightthickness=1)
        outer.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
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

        sc = SIG_COLORS.get(sig.signal, SIG_COLORS["NO TRADE"])
        tk.Label(p, text=sig.signal, bg=sc["bg"], fg=sc["fg"],
            font=("Segoe UI",12,"bold"), pady=6).pack(fill="x")
        tk.Label(p, text=sig.market_name, bg=PANEL_DARK, fg=TEXT,
            font=FB, padx=8, pady=4,
            anchor="w", wraplength=240).pack(fill="x")

        metrics = [
            ("Side",          sig.side),
            ("YES Bid/Ask",   f"{sig.bid_price}c / {sig.ask_price}c"),
            ("Last",          f"{sig.last_price}c"),
            ("Model Fair",    f"{sig.fair_price:.0f}c"),
            ("Raw Edge",      f"{sig.raw_edge:+.1f}c"),
            ("Fee (est)",     f"{sig.fee_est:.0f}c"),
            ("Fee-adj Edge",  f"{sig.fee_adj_edge:+.1f}c"),
            ("Breakeven",     f"{sig.breakeven:.1f}c"),
            ("Spread",        f"{sig.spread:.0f}c"),
            ("Liquidity",     sig.liquidity),
        ]
        # Fetch live orderbook detail for this market
        try:
            ob = self.data_layer.get_orderbook(
                sig.market_id,
                source=self.data_layer._last_source)
            if ob:
                metrics += [
                    ("─── Orderbook ───", ""),
                    ("YES best bid",  f"{ob.yes_best_bid:.0f}c" if ob.yes_best_bid else "N/A"),
                    ("YES best ask",  f"{ob.yes_best_ask:.0f}c" if ob.yes_best_ask else "N/A"),
                    ("NO best bid",   f"{ob.no_best_bid:.0f}c"  if ob.no_best_bid  else "N/A"),
                    ("NO best ask",   f"{ob.no_best_ask:.0f}c"  if ob.no_best_ask  else "N/A"),
                    ("YES spread",    f"{ob.yes_spread:.0f}c"   if ob.yes_spread   else "N/A"),
                    ("NO spread",     f"{ob.no_spread:.0f}c"    if ob.no_spread    else "N/A"),
                    ("Book depth",    str(ob.total_yes_qty + ob.total_no_qty)),
                    ("OB liquidity",  ob.liquidity),
                ]
        except Exception as e:
            print(f"[orderbook detail] {e}")
        mf = tk.Frame(p, bg=PANEL_DARK)
        mf.pack(fill="x", padx=6, pady=4)
        for lbl, val in metrics:
            # Separator row
            if lbl.startswith("─"):
                sep = tk.Frame(mf, bg=BORDER, height=1)
                sep.pack(fill="x", padx=4, pady=4)
                tk.Label(mf, text=lbl.strip("─ "), bg=PANEL_DARK,
                    fg=CYAN, font=FS, anchor="w").pack(
                    fill="x", padx=6, pady=1)
                continue
            # Skip empty separators
            if not lbl:
                continue
            row = tk.Frame(mf, bg=PANEL_DARK)
            row.pack(fill="x", padx=6, pady=1)
            tk.Label(row, text=lbl, bg=PANEL_DARK, fg=MUTED,
                font=FS, width=14, anchor="w").pack(side="left")
            col = GREEN if ("+" in str(val) and "Edge" in lbl) else \
                  RED   if ("-" in str(val) and "Edge" in lbl) else \
                  CYAN  if any(x in lbl for x in ("YES","NO","bid","ask","Book","OB")) else TEXT
            tk.Label(row, text=val, bg=PANEL_DARK, fg=col,
                font=FB, anchor="w").pack(side="left")

        if sig.signal in ("ENTRY","STRONG ENTRY"):
            tk.Label(p, text="TRADE PLAN", bg=PANEL_DARK, fg=CYAN,
                font=FB, padx=8, pady=4, anchor="w").pack(fill="x")
            plan = tk.Frame(p, bg="#0d1f2d",
                highlightbackground=CYAN_DARK, highlightthickness=1)
            plan.pack(fill="x", padx=6, pady=4)
            # Use orderbook-derived entry/exit if available
            ob = self.data_layer.get_orderbook(sig.market_id,
                source=self.data_layer._last_source)
            entry_p = sig.ask_price
            exit_p  = sig.exit_target
            if ob:
                if sig.side == "YES" and ob.yes_best_ask is not None:
                    entry_p = ob.yes_best_ask
                elif sig.side == "NO" and ob.no_best_ask is not None:
                    entry_p = ob.no_best_ask
            for line in [
                f"Entry:      Buy {sig.side} at {entry_p:.0f}c or better",
                f"Breakeven:  ~{sig.breakeven:.0f}c",
                f"First exit: {exit_p:.0f}c",
                f"Strong exit:{sig.fair_price:.0f}c",
                f"Avoid above:{entry_p+3:.0f}c",
                f"Max risk:   ${sig.suggested_size:.0f}",
                f"Mode:       Paper only — no real orders",
            ]:
                tk.Label(plan, text=line, bg="#0d1f2d", fg=TEXT,
                    font=FM, anchor="w", padx=8, pady=1).pack(fill="x")

        tk.Label(p, text="WHY", bg=PANEL_DARK, fg=CYAN,
            font=FB, padx=8, pady=4, anchor="w").pack(fill="x")
        tk.Label(p, text=sig.reason, bg=PANEL_DARK, fg=MUTED,
            font=FS, padx=8, pady=4, anchor="w",
            wraplength=240, justify="left").pack(fill="x")

        bf = tk.Frame(p, bg=PANEL)
        bf.pack(fill="x", padx=6, pady=4)
        for text, bg, cmd in [
            ("Add to Watchlist",  PURPLE,    lambda s=sig: self._add_watchlist(s)),
            ("Create Paper Trade",GREEN_DARK, lambda s=sig: self._paper_trade(s)),
            ("Mark as Avoid",     RED_DARK,   lambda s=sig: self._mark_avoid(s)),
            ("Export Signal",     GRAY_BTN,   lambda s=sig: self._export_signal(s)),
        ]:
            tk.Button(bf, text=text, bg=bg, fg=TEXT,
                activebackground=bg, relief="flat", font=FS,
                pady=5, command=cmd).pack(fill="x", pady=1)

    # ── BOTTOM: Paper trades + log ────────────────────────────────────────

    def _build_bottom(self, p):
        outer = tk.Frame(p, bg=BG,
            highlightbackground=BORDER, highlightthickness=1)
        outer.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        outer.grid_rowconfigure(1, weight=1)
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_columnconfigure(1, weight=2)

        tk.Label(outer, text="PAPER TRADE LOG & SCANNER MESSAGES",
            bg=BG, fg=CYAN, font=FB, padx=8, pady=4,
            anchor="w").grid(row=0, column=0, columnspan=2, sticky="ew")

        lf = tk.Frame(outer, bg=PANEL)
        lf.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
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

        rf = tk.Frame(outer, bg=PANEL)
        rf.grid(row=1, column=1, sticky="nsew", padx=4, pady=4)
        rf.grid_rowconfigure(0, weight=1)
        rf.grid_columnconfigure(0, weight=1)

        self._log_text = tk.Text(rf, bg=PANEL_DARK, fg=GREEN,
            font=FM, state="disabled", wrap="word",
            insertbackground=TEXT, relief="flat")
        lsb = tk.Scrollbar(rf, command=self._log_text.yview)
        self._log_text.configure(yscrollcommand=lsb.set)
        self._log_text.grid(row=0, column=0, sticky="nsew")
        lsb.grid(row=0, column=1, sticky="ns")

    # ── Data loading ──────────────────────────────────────────────────────

    def _initial_load(self):
        self._log(f"Data mode: {cfg.effective_mode()}")
        self._log(f"Kalshi: {'Ready' if cfg.kalshi_ready() else 'No key — using mock'}")
        self._log(f"Auto trading: OFF (hardcoded)")
        self._refresh()
        self._seed_paper_trades()

    def _refresh(self):
        """Fetch markets via DataLayer and run scanner engine."""
        try:
            category = self.v_category.get()
            raw_dicts, source, error = self.data_layer.fetch(
                category_filter=category)

            if error:
                self._log(f"Warning: {error}")

            if not raw_dicts:
                self._log("No markets returned — check data mode and filters.")
                self.signals = []
                self._populate_tree()
                self._update_status_box()
                return

            self.signals = run_scanner(
                raw_dicts,
                min_edge   = self.v_min_edge.get(),
                max_spread = self.v_max_spread.get(),
                max_size   = self.v_max_size.get())

            self._populate_tree()
            self._update_status_box()

            ec = sum(1 for s in self.signals if s.signal in ("ENTRY","STRONG ENTRY"))
            self._log(f"Loaded {len(self.signals)} markets from {source} — {ec} signals.")

        except Exception as e:
            self._log(f"Refresh error: {e}")
            self._update_status_box()

    def _populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        src = self.data_layer._last_source or "?"
        for sig in self.signals:
            tag = sig.signal.replace(" ","_")
            self.tree.insert("", "end", values=(
                sig.market_name[:28], sig.side,
                f"{sig.bid_price}c", f"{sig.ask_price}c",
                f"{sig.last_price}c", f"{sig.fair_price:.0f}c",
                f"{sig.raw_edge:+.0f}c", f"{sig.spread:.0f}c",
                f"{sig.fee_est:.0f}c", f"{sig.breakeven:.0f}c",
                sig.signal,
                f"${sig.suggested_size:.0f}" if sig.suggested_size else "$0",
                f"{sig.exit_target:.0f}c" if sig.exit_target else "—",
                src[:8],
            ), tags=(tag,), iid=sig.market_id)

    def _seed_paper_trades(self):
        self.paper_trades = [
            PaperTrade("12:28:11","BTC NO — $76k","NO",44,22,40,52,47,"OPEN"),
            PaperTrade("12:15:03","SOC — Man City","YES",51,9,42,58,54,"OPEN"),
            PaperTrade("11:44:22","ETH YES — $3.1k","YES",41,18,38,50,45,"CLOSED"),
        ]
        self._update_pt_tree()

    def _update_pt_tree(self):
        self.pt_tree.delete(*self.pt_tree.get_children())
        for pt in self.paper_trades:
            pl     = pt.unrealized_pl
            pl_str = f"${pl:+.2f}" if pl != 0 else "—"
            self.pt_tree.insert("", "end", values=(
                pt.time, pt.market[:20], pt.side,
                f"{pt.entry_price}c", str(pt.contracts),
                f"{pt.fee_paid}c", f"{pt.target_exit}c",
                f"{pt.current_price}c", pl_str, pt.status,
            ))

    # ── Scan loop ─────────────────────────────────────────────────────────

    def _start_scan(self):
        if self.scanning: return
        self.scanning = True
        interval = cfg.SCANNER_REFRESH_SEC
        self._log(f"Paper scan started — refreshing every {interval}s.")
        self._scan_tick()

    def _scan_tick(self):
        if not self.scanning: return
        self._refresh()
        self.scan_job = self.after(cfg.SCANNER_REFRESH_SEC * 1000, self._scan_tick)

    def _stop_scan(self):
        self.scanning = False
        if self.scan_job:
            self.after_cancel(self.scan_job)
            self.scan_job = None
        self._log("Scan stopped.")

    # ── Row selection ─────────────────────────────────────────────────────

    def _on_select(self, _event=None):
        try:
            sel = self.tree.selection()
            if not sel: return
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

    # ── Paper trade actions ───────────────────────────────────────────────

    def _add_watchlist(self, sig):
        self._log(f"Added to watchlist: {sig.market_name}")

    def _paper_trade(self, sig):
        if sig.signal not in ("ENTRY","STRONG ENTRY"):
            self._log(f"Signal is {sig.signal} — no paper trade created.")
            return
        contracts = calculate_contracts(sig.suggested_size, sig.ask_price)
        fee       = calculate_kalshi_fee(max(contracts,1), sig.ask_price)
        pt = PaperTrade(
            time=datetime.now().strftime("%H:%M:%S"),
            market=sig.market_name[:22], side=sig.side,
            entry_price=sig.ask_price, contracts=contracts,
            fee_paid=fee, target_exit=sig.exit_target,
            current_price=sig.last_price, status="OPEN")
        self.paper_trades.insert(0, pt)
        self._update_pt_tree()
        self._log(f"Paper trade: {sig.side} {sig.market_name[:24]} "
                  f"@ {sig.ask_price}c x{contracts}. Fee ~{fee:.0f}c. "
                  f"NO REAL ORDER PLACED.")

    def _mark_avoid(self, sig):
        self._log(f"Marked AVOID: {sig.market_name}")

    def _export_signal(self, sig):
        self._log(f"Exported: {sig.market_name} | {sig.signal} | "
                  f"Edge {sig.raw_edge:+.0f}c")

    def _reset_filters(self):
        self.v_min_edge.set(cfg.SCANNER_MIN_EDGE)
        self.v_max_spread.set(cfg.SCANNER_MAX_SPREAD)
        self.v_max_size.set(cfg.SCANNER_MAX_TRADE_SIZE)
        self.v_daily_loss.set(cfg.SCANNER_DAILY_LOSS)
        self.v_category.set("All")
        self.v_timeframe.set("Live")
        self._log("Filters reset to defaults.")
        self._refresh()

    # ── Helpers ───────────────────────────────────────────────────────────

    def _log(self, msg):
        try:
            ts = datetime.now().strftime("%H:%M:%S")
            self._log_text.configure(state="normal")
            self._log_text.insert("end", f"[{ts}] {msg}\n")
            self._log_text.see("end")
            self._log_text.configure(state="disabled")
        except Exception:
            print(f"[log] {msg}")

    def _clear(self, widget):
        for w in widget.winfo_children():
            w.destroy()
