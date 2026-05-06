"""
scanner_watchlist.py
AI Market Scanner dedicated watchlist.
Persists to data/ai_scanner_watchlist.json.
No trading. No real orders. Paper/analysis tracking only.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List

WATCHLIST_DIR  = Path(__file__).parent / "data"
WATCHLIST_FILE = WATCHLIST_DIR / "ai_scanner_watchlist.json"
WATCHLIST_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class WatchlistEntry:
    """One watched Kalshi market. All prices in cents (0-100)."""
    ticker:          str
    title:           str
    side:            str            # YES | NO
    signal:          str            # last known signal
    bid:             Optional[float]   # cents
    ask:             Optional[float]   # cents
    last:            Optional[float]   # cents
    category:        str
    source:          str
    time_added:      str
    expiration:      Optional[str]  = None
    target_price:    Optional[float] = None   # crypto target if parsed
    reference_price: Optional[float] = None   # BTC/ETH current
    status:          str            = "ACTIVE"   # ACTIVE | STALE | ALERT | AVOID | EXPIRED
    alert_note:      str            = ""
    last_seen:       Optional[str]  = None
    spread:          Optional[float] = None        # cents
    avoided:         bool            = False
    last_alert_at:   Optional[str]  = None
    last_alert_msg:  str            = ""
    score:           int             = 0
    alert_threshold_ask:  Optional[float] = None  # trigger alert when ask ≤ this
    # Per-market targets (Part B)
    target_yes_price:     Optional[float] = None  # cents — alert when YES ask ≤ this
    target_no_price:      Optional[float] = None  # cents — alert when NO ask ≤ this
    min_edge_cents:       Optional[float] = None  # alert when edge ≥ this
    max_spread_cents:     Optional[float] = None  # alert when spread ≤ this
    alert_when_signal:    Optional[str]   = None  # e.g. "POSSIBLE EDGE"
    user_note:            str             = ""     # plain-text user note

    @property
    def bid_str(self) -> str:
        return f"{self.bid:.0f}c" if self.bid else "N/A"

    @property
    def ask_str(self) -> str:
        return f"{self.ask:.0f}c" if self.ask else "N/A"

    @property
    def last_str(self) -> str:
        return f"{self.last:.0f}c" if self.last else "N/A"

    @property
    def target_str(self) -> str:
        return f"${self.target_price:,.0f}" if self.target_price else "N/A"


class ScannerWatchlist:
    """
    Manages the AI Scanner watchlist.
    Thread-safe for read; writes happen on main thread only.
    """

    def __init__(self, log_fn=None):
        self._log     = log_fn or print
        self._entries: List[WatchlistEntry] = []
        self._load()

    # ── CRUD ──────────────────────────────────────────────────────────────

    def add(self, entry: WatchlistEntry) -> bool:
        """Add entry. Returns False if already present (no duplicate)."""
        if any(e.ticker == entry.ticker for e in self._entries):
            self._log(f"Market already in watchlist: {entry.ticker}")
            return False
        self._entries.insert(0, entry)
        self._save()
        self._log(f"Added {entry.ticker} to AI Scanner Watchlist")
        return True

    def remove(self, ticker: str) -> bool:
        """Remove by ticker. Returns False if not found."""
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.ticker != ticker]
        if len(self._entries) == before:
            self._log(f"Not in watchlist: {ticker}")
            return False
        self._save()
        self._log(f"Removed {ticker} from AI Scanner Watchlist")
        return True

    def clear_stale(self) -> int:
        """Remove entries marked STALE or EXPIRED. Returns count removed."""
        before = len(self._entries)
        self._entries = [e for e in self._entries
                         if e.status not in ("STALE", "EXPIRED")]
        removed = before - len(self._entries)
        if removed:
            self._save()
            self._log(f"Cleared {removed} stale watchlist entries")
        return removed

    def all_entries(self) -> List[WatchlistEntry]:
        return list(self._entries)

    def get(self, ticker: str) -> Optional[WatchlistEntry]:
        return next((e for e in self._entries if e.ticker == ticker), None)

    def contains(self, ticker: str) -> bool:
        return any(e.ticker == ticker for e in self._entries)

    # ── Update from live market data ───────────────────────────────────────

    # Alert cooldown
    ALERT_COOLDOWN_SECS = 300   # 5 minutes

    def update_from_signals(self, signals: list) -> int:
        """
        Update watchlist entries from live signal data.
        Checks alert conditions. Marks STALE if market disappears.
        Returns (updated_count, alert_messages_list).
        """
        signal_map = {s.market_id: s for s in signals}
        updated = 0
        for entry in self._entries:
            if entry.avoided:
                # Keep avoided status, just update prices
                pass
            if entry.ticker in signal_map:
                sig = signal_map[entry.ticker]
                prev_signal = entry.signal
                entry.bid      = sig.bid_price   if sig.bid_price  else entry.bid
                entry.ask      = sig.ask_price   if sig.ask_price  else entry.ask
                entry.last     = sig.last_price  if sig.last_price else entry.last
                entry.spread   = sig.spread      if sig.spread     else entry.spread
                entry.signal   = sig.signal
                entry.last_seen = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if not entry.avoided:
                    entry.status = "ACTIVE"
                updated += 1
                # Alert checks
                self._check_alerts(entry, prev_signal)
            elif entry.status == "ACTIVE" and not entry.avoided:
                entry.status   = "STALE"
                entry.last_seen = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if updated:
            self._save()
        return updated

    def _check_alerts(self, entry, prev_signal: str) -> None:
        """Check alert conditions and update entry if triggered."""
        from datetime import datetime as _dt
        now = _dt.now()

        # Check cooldown
        if entry.last_alert_at:
            try:
                last = _dt.strptime(entry.last_alert_at, "%Y-%m-%d %H:%M:%S")
                if (now - last).total_seconds() < self.ALERT_COOLDOWN_SECS:
                    return
            except Exception:
                pass

        msg = None

        # Signal upgrade alert
        UPGRADE = {"DATA NEEDED", "NO TRADE", "AVOID"}
        if prev_signal in UPGRADE and entry.signal not in UPGRADE:
            msg = f"ALERT [{entry.ticker}]: Signal upgraded from {prev_signal} → {entry.signal}"

        # Price threshold alert
        if (entry.alert_threshold_ask is not None
                and entry.ask is not None
                and entry.ask <= entry.alert_threshold_ask):
            msg = (f"ALERT [{entry.ticker}]: Ask {entry.ask:.0f}c ≤ "
                   f"threshold {entry.alert_threshold_ask:.0f}c")

        # Stale alert
        if entry.status == "STALE" and prev_signal != "STALE":
            msg = f"ALERT [{entry.ticker}]: Market no longer visible — marked STALE"

        if msg:
            entry.last_alert_at  = now.strftime("%Y-%m-%d %H:%M:%S")
            entry.last_alert_msg = msg
            entry.status         = "ALERT"
            self._log(msg)

    def get_alert_messages(self) -> list:
        """Return all recent alert messages from watchlist entries."""
        msgs = []
        for entry in self._entries:
            if entry.last_alert_msg:
                msgs.append(entry.last_alert_msg)
        return msgs

    def save_note(self, ticker: str, note: str) -> bool:
        """Save a user note for a watched market."""
        entry = self.get(ticker)
        if not entry:
            return False
        entry.user_note = note[:500]   # cap at 500 chars
        self._save()
        self._log(f"Note saved for {ticker}")
        return True

    def mark_avoided(self, ticker: str, reason: str = "") -> bool:
        """Mark a market as user-avoided."""
        entry = self.get(ticker)
        if not entry:
            return False
        entry.avoided   = True
        entry.status    = "AVOID"
        entry.alert_note = reason or "User marked avoid"
        self._save()
        self._log(f"Marked AVOID: {ticker}")
        return True

    def unmark_avoided(self, ticker: str) -> bool:
        """Remove avoid status from a market."""
        entry = self.get(ticker)
        if not entry:
            return False
        entry.avoided    = False
        entry.status     = "ACTIVE"
        entry.alert_note = ""
        self._save()
        self._log(f"Unmarked AVOID: {ticker}")
        return True

    def update_reference_price(self, ticker: str,
                                ref_price: Optional[float]) -> None:
        """Update the crypto reference price for a watchlist entry."""
        entry = self.get(ticker)
        if entry:
            entry.reference_price = ref_price
            self._save()

    # ── Persistence ────────────────────────────────────────────────────────

    def _save(self):
        try:
            rows = [asdict(e) for e in self._entries]
            with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
                json.dump(rows, f, indent=2, default=str)
        except Exception as e:
            self._log(f"Watchlist save error: {e}")

    def _load(self):
        if not WATCHLIST_FILE.exists():
            self._entries = []
            return
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                rows = json.load(f)
            self._entries = []
            for row in rows:
                try:
                    self._entries.append(WatchlistEntry(**row))
                except Exception as e:
                    self._log(f"Watchlist entry skip: {e}")
            self._log(f"Loaded {len(self._entries)} watchlist entries")
        except Exception as e:
            # Corrupt file: back it up and start empty
            self._log(f"Watchlist corrupt — backing up and starting empty: {e}")
            try:
                backup = WATCHLIST_FILE.with_suffix(".json.bak")
                WATCHLIST_FILE.rename(backup)
                self._log(f"Backup saved to {backup.name}")
            except Exception as be:
                self._log(f"Backup failed: {be}")
            self._entries = []

    @staticmethod
    def file_path() -> str:
        return str(WATCHLIST_FILE)
