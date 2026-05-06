"""
paper_trade_engine.py
Paper trading engine — NO real orders, NO account access, NO execution.
Tracks hypothetical trades for analysis and UI feedback only.

AUTO_TRADING_ENABLED = False (hardcoded — never reads from env)
"""

import csv
import json
import math
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List


# Paper trades directory
PAPER_DIR = Path(__file__).parent / "data" / "paper_trades"
PAPER_DIR.mkdir(parents=True, exist_ok=True)
PAPER_CSV = PAPER_DIR / "paper_trades.csv"

# Safety constants
AUTO_TRADING_ENABLED = False   # hardcoded — never change
PAPER_MODE           = True


# ── Paper trade record ─────────────────────────────────────────────────────

@dataclass
class PaperTradeRecord:
    """
    One paper trade. All prices in cents (0-100) for Kalshi binary markets.
    No real money is involved. No orders are sent.
    """
    trade_id:       str
    time_opened:    str
    source:         str            # "kalshi" | "mock"
    ticker:         str
    title:          str
    side:           str            # "YES" | "NO"
    entry_price:    float          # cents
    contracts:      int
    buy_fee:        float          # cents (total)
    target_exit:    float          # cents
    current_price:  float          # cents (updated on refresh)
    exit_price:     Optional[float] = None   # cents (set when closed)
    sell_fee:       Optional[float] = None   # cents
    time_closed:    Optional[str]   = None
    status:         str             = "OPEN"    # OPEN | CLOSED | AVOIDED
    reason:         str             = ""
    notes:          str             = ""

    @property
    def unrealized_pl_cents(self) -> float:
        """Unrealized P/L in cents. Positive = profit."""
        if self.status != "OPEN":
            return 0.0
        gain = (self.current_price - self.entry_price) * self.contracts
        return round(gain - self.buy_fee, 2)

    @property
    def unrealized_pl_dollars(self) -> float:
        return round(self.unrealized_pl_cents / 100.0, 4)

    @property
    def realized_pl_cents(self) -> Optional[float]:
        """Realized P/L in cents after both fees."""
        if self.status != "CLOSED" or self.exit_price is None:
            return None
        gain     = (self.exit_price - self.entry_price) * self.contracts
        total_fee = self.buy_fee + (self.sell_fee or 0.0)
        return round(gain - total_fee, 2)

    @property
    def realized_pl_dollars(self) -> Optional[float]:
        pl = self.realized_pl_cents
        return round(pl / 100.0, 4) if pl is not None else None

    @property
    def pl_str(self) -> str:
        if self.status == "CLOSED":
            pl = self.realized_pl_dollars
            return f"${pl:+.4f}" if pl is not None else "N/A"
        return f"${self.unrealized_pl_dollars:+.4f}"

    @property
    def cost_dollars(self) -> float:
        """Total cost to enter: entry * contracts + buy_fee (all in dollars)."""
        return round((self.entry_price * self.contracts + self.buy_fee) / 100.0, 4)


# ── Kalshi fee calculation ─────────────────────────────────────────────────

def kalshi_fee(contracts: int, price_cents: float) -> float:
    """
    Official Kalshi fee formula (in cents):
    fee = ceil(0.07 × contracts × price_dollars × (1 - price_dollars))
    Returns total fee in cents.
    """
    if contracts <= 0 or price_cents <= 0:
        return 0.0
    p = price_cents / 100.0
    return float(math.ceil(0.07 * contracts * p * (1 - p) * 100))


def contracts_for_budget(budget_dollars: float, price_cents: float) -> int:
    """Conservative contract count for a given budget."""
    if price_cents <= 0 or budget_dollars <= 0:
        return 0
    p = price_cents / 100.0
    fee_per = 0.07 * p * (1 - p)
    cost_per = p + fee_per
    return max(0, int(budget_dollars / cost_per))


def breakeven_price(entry_cents: float, contracts: int) -> float:
    """Minimum exit price to cover entry + buy fee + sell fee estimate."""
    if contracts <= 0 or entry_cents <= 0:
        return 0.0
    buy_f   = kalshi_fee(contracts, entry_cents)
    est_sell = entry_cents + buy_f / max(contracts, 1)
    sell_f   = kalshi_fee(contracts, est_sell)
    total    = entry_cents * contracts + buy_f + sell_f
    return round(total / contracts, 1)


# ── Paper trade engine ────────────────────────────────────────────────────

class PaperTradeEngine:
    """
    Manages paper trade lifecycle.
    No real orders. No account access. Paper only.
    """

    def __init__(self, log_fn=None):
        self._log    = log_fn or print
        self._trades: List[PaperTradeRecord] = []
        self._id_counter = 0
        self._load_from_disk()

    def _next_id(self) -> str:
        self._id_counter += 1
        return f"PT{datetime.now().strftime('%Y%m%d%H%M%S')}-{self._id_counter:04d}"

    # ── Create ──────────────────────────────────────────────────────────────

    def create_trade(
        self,
        ticker:       str,
        title:        str,
        side:         str,
        entry_cents:  float,
        max_size_dollars: float = 10.0,
        source:       str       = "kalshi",
        reason:       str       = "",
    ) -> Optional[PaperTradeRecord]:
        """
        Create a paper trade from a scanner signal.
        Returns None if entry_cents is 0 or invalid.
        No real orders are placed.
        """
        if not entry_cents or entry_cents <= 0:
            self._log("Cannot create paper trade — no valid entry price (ask = 0 or N/A).")
            return None

        n        = contracts_for_budget(max_size_dollars, entry_cents)
        buy_f    = kalshi_fee(max(n, 1), entry_cents)
        target   = round(entry_cents + (100 - entry_cents) * 0.4, 1)  # 40% of way to 100c

        trade = PaperTradeRecord(
            trade_id      = self._next_id(),
            time_opened   = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            source        = source,
            ticker        = ticker,
            title         = title[:60],
            side          = side,
            entry_price   = entry_cents,
            contracts     = n,
            buy_fee       = buy_f,
            target_exit   = target,
            current_price = entry_cents,
            status        = "OPEN",
            reason        = reason,
        )
        self._trades.append(trade)
        self._save_to_disk()
        self._log(
            f"Paper trade created: {side} {ticker} @ {entry_cents:.0f}c "
            f"× {n} contracts. Fee ~{buy_f:.0f}c. "
            f"NO REAL ORDER PLACED."
        )
        return trade

    # ── Update current prices ───────────────────────────────────────────────

    def update_prices(self, price_map: dict):
        """
        Update current_price for open trades.
        price_map: {ticker: current_price_cents}
        """
        changed = 0
        for t in self._trades:
            if t.status == "OPEN" and t.ticker in price_map:
                t.current_price = price_map[t.ticker]
                changed += 1
        if changed:
            self._save_to_disk()

    # ── Exit trade ─────────────────────────────────────────────────────────

    def exit_trade(
        self,
        trade_id:   str,
        exit_cents: float,
        reason:     str = "Manual exit",
    ) -> Optional[PaperTradeRecord]:
        """
        Close a paper trade at the given exit price.
        Calculates sell fee and realized P/L.
        No real orders.
        """
        trade = self._find(trade_id)
        if trade is None:
            self._log(f"Paper trade {trade_id} not found.")
            return None
        if trade.status != "OPEN":
            self._log(f"Paper trade {trade_id} is already {trade.status}.")
            return trade

        sell_f         = kalshi_fee(trade.contracts, exit_cents)
        trade.exit_price  = exit_cents
        trade.sell_fee    = sell_f
        trade.time_closed = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        trade.status      = "CLOSED"
        trade.notes       = reason

        self._save_to_disk()
        pl = trade.realized_pl_dollars
        self._log(
            f"Paper trade closed: {trade.ticker} {trade.side} "
            f"exit {exit_cents:.0f}c → P/L {pl:+.4f}  NO REAL ORDER."
        )
        # Save performance snapshot after each close
        try:
            self.save_performance_snapshot()
        except Exception:
            pass
        return trade

    # ── Avoid ──────────────────────────────────────────────────────────────

    def mark_avoid(self, ticker: str, reason: str = "") -> None:
        self._log(f"Marked AVOID: {ticker}. {reason}")

    # ── Query ──────────────────────────────────────────────────────────────

    def open_trades(self) -> List[PaperTradeRecord]:
        return [t for t in self._trades if t.status == "OPEN"]

    def closed_trades(self) -> List[PaperTradeRecord]:
        return [t for t in self._trades if t.status == "CLOSED"]

    def all_trades(self) -> List[PaperTradeRecord]:
        return list(self._trades)

    def trades_for_ticker(self, ticker: str) -> List[PaperTradeRecord]:
        return [t for t in self._trades if t.ticker == ticker]

    def _find(self, trade_id: str) -> Optional[PaperTradeRecord]:
        return next((t for t in self._trades if t.trade_id == trade_id), None)

    # ── Performance summary ─────────────────────────────────────────────────

    def performance_summary(self) -> dict:
        """Return performance metrics for the UI panel."""
        all_t    = self._trades
        open_t   = [t for t in all_t if t.status == "OPEN"]
        closed_t = [t for t in all_t if t.status == "CLOSED"]

        wins  = [t for t in closed_t if (t.realized_pl_dollars or 0) > 0]
        loss  = [t for t in closed_t if (t.realized_pl_dollars or 0) <= 0]
        total_pl = sum((t.realized_pl_dollars or 0) for t in closed_t)
        unrealized = sum(t.unrealized_pl_dollars for t in open_t)

        win_rate = round(len(wins) / max(len(closed_t), 1) * 100, 1)
        avg_pl   = round(total_pl / max(len(closed_t), 1), 4)

        best  = max(closed_t, key=lambda t: t.realized_pl_dollars or -9999, default=None)
        worst = min(closed_t, key=lambda t: t.realized_pl_dollars or 9999,  default=None)

        return {
            "total":       len(all_t),
            "open":        len(open_t),
            "closed":      len(closed_t),
            "wins":        len(wins),
            "losses":      len(loss),
            "win_rate":    f"{win_rate}%",
            "total_pl":    f"${total_pl:+.4f}",
            "unrealized":  f"${unrealized:+.4f}",
            "avg_pl":      f"${avg_pl:+.4f}",
            "best_trade":  best.pl_str  if best  else "—",
            "worst_trade": worst.pl_str if worst else "—",
        }

    # ── Export ──────────────────────────────────────────────────────────────

    def export_csv(self, export_dir: str = "exports") -> str:
        """
        Export all paper trades to CSV in exports/ folder.
        Returns the file path written. Creates folder if missing.
        No API keys or secrets are included.
        """
        import csv
        from pathlib import Path
        out_dir = Path(export_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = out_dir / f"paper_trades_{ts}.csv"
        fieldnames = [
            "trade_id","ticker","title","side",
            "entry_price","exit_price","current_price","contracts",
            "opened_at","closed_at","buy_fee","sell_fee",
            "realized_pnl","unrealized_pnl","status","notes",
        ]
        try:
            with open(out, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for t in self._trades:
                    writer.writerow({
                        "trade_id":      t.trade_id,
                        "ticker":        t.ticker,
                        "title":         t.title,
                        "side":          t.side,
                        "entry_price":   f"{t.entry_price:.1f}c",
                        "exit_price":    f"{t.exit_price:.1f}c"     if t.exit_price  else "N/A",
                        "current_price": f"{t.current_price:.1f}c",
                        "contracts":     t.contracts,
                        "opened_at":     t.time_opened,
                        "closed_at":     t.time_closed or "N/A",
                        "buy_fee":       f"{t.buy_fee:.1f}c",
                        "sell_fee":      f"{t.sell_fee:.1f}c"       if t.sell_fee    else "N/A",
                        "realized_pnl":  t.pl_str                   if t.status == "CLOSED" else "N/A",
                        "unrealized_pnl":f"${t.unrealized_pl_dollars:+.4f}" if t.status == "OPEN" else "N/A",
                        "status":        t.status,
                        "notes":         t.notes,
                    })
            self._log(f"Exported {len(self._trades)} trades → {out}")
            return str(out)
        except Exception as e:
            self._log(f"Export error: {e}")
            return ""

    def export_performance_csv(self, export_dir: str = "exports") -> str:
        """
        Export performance summary to CSV.
        Returns file path. No API keys included.
        """
        import csv
        from pathlib import Path
        out_dir = Path(export_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = out_dir / f"performance_{ts}.csv"
        perf = self.performance_summary()
        try:
            with open(out, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Metric", "Value"])
                for k, v in perf.items():
                    writer.writerow([k, v])
                writer.writerow(["exported_at", datetime.now().isoformat()])
            self._log(f"Performance exported → {out}")
            return str(out)
        except Exception as e:
            self._log(f"Performance export error: {e}")
            return ""

    def save_performance_snapshot(self) -> None:
        """Append a performance snapshot to performance_history.json."""
        import json
        try:
            hist_path = PAPER_DIR / "performance_history.json"
            perf      = self.performance_summary()
            perf["snapshot_at"] = datetime.now().isoformat()
            history = []
            if hist_path.exists():
                try:
                    with open(hist_path, "r", encoding="utf-8") as f:
                        history = json.load(f)
                except Exception:
                    history = []
            history.append(perf)
            # Keep last 200 snapshots
            if len(history) > 200:
                history = history[-200:]
            with open(hist_path, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, default=str)
        except Exception as e:
            self._log(f"Performance snapshot error: {e}")

    # ── Persistence ─────────────────────────────────────────────────────────

    def _save_to_disk(self):
        """Save all trades to CSV and JSON."""
        try:
            rows = [asdict(t) for t in self._trades]
            # CSV
            if rows:
                with open(PAPER_CSV, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(rows)
            # JSON (more complete)
            json_path = PAPER_DIR / "paper_trades.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(rows, f, indent=2, default=str)
        except Exception as e:
            self._log(f"Paper trades save error: {e}")

    def _load_from_disk(self):
        """Load existing trades from JSON on startup."""
        try:
            json_path = PAPER_DIR / "paper_trades.json"
            if not json_path.exists():
                return
            with open(json_path, "r", encoding="utf-8") as f:
                rows = json.load(f)
            self._trades = []
            for row in rows:
                try:
                    self._trades.append(PaperTradeRecord(**row))
                except Exception:
                    pass
            if self._trades:
                max_id = max(
                    (int(t.trade_id.split("-")[-1]) for t in self._trades
                     if "-" in t.trade_id), default=0)
                self._id_counter = max_id
        except Exception as e:
            self._log(f"Paper trades load error: {e}")

    def export_csv_path(self) -> str:
        return str(PAPER_CSV)
