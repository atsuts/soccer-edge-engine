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
    status:          str            = "ACTIVE"   # ACTIVE | STALE | EXPIRED
    alert_note:      str            = ""

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

    def update_from_signals(self, signals: list) -> int:
        """
        Update watchlist entries from a fresh list of MarketSignal objects.
        Marks entries as STALE if their ticker no longer appears.
        Returns count updated.
        """
        signal_map = {s.market_id: s for s in signals}
        updated = 0
        for entry in self._entries:
            if entry.ticker in signal_map:
                sig = signal_map[entry.ticker]
                entry.bid    = sig.bid_price   if sig.bid_price  else entry.bid
                entry.ask    = sig.ask_price   if sig.ask_price  else entry.ask
                entry.last   = sig.last_price  if sig.last_price else entry.last
                entry.signal = sig.signal
                entry.status = "ACTIVE"
                updated += 1
            elif entry.status == "ACTIVE":
                entry.status = "STALE"
        if updated:
            self._save()
        return updated

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
