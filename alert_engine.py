"""
alert_engine.py — Local-only Alert Center for Soccer Edge Engine AI Scanner.

All alerts are informational and paper-mode only.
No real trading. No external notifications. No API keys stored.
"""
from __future__ import annotations
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List

ALERTS_DIR  = Path("data")
ALERTS_FILE = ALERTS_DIR / "ai_scanner_alerts.json"

COOLDOWN_SECS = 300   # 5 minutes between identical alerts per ticker+type

SEVERITY_ORDER = {"ERROR": 0, "WARNING": 1, "WATCH": 2, "INFO": 3}


@dataclass
class ScannerAlert:
    """One alert record. Never contains API keys or secrets."""
    alert_id:    str
    ticker:      str
    market_title:str
    alert_type:  str        # SIGNAL_UPGRADE | EDGE_ABOVE | SPREAD_BELOW |
                            # PRICE_TARGET | CLOSING_SOON | STALE | PL_WARNING |
                            # DATA_QUALITY | SYSTEM
    message:     str
    severity:    str        # INFO | WATCH | WARNING | ERROR
    created_at:  str
    last_seen_at:str
    acknowledged:bool       = False
    source:      str        = "scanner"  # scanner|watchlist|paper_trade|system


class AlertCenter:
    """
    Persistent local alert store with cooldown deduplication.
    Thread-safe writes (called from Tkinter main thread only).
    """

    def __init__(self, log_fn=None):
        self._alerts: List[ScannerAlert] = []
        self._log    = log_fn or print
        ALERTS_DIR.mkdir(parents=True, exist_ok=True)
        self._load()

    # ── Public API ───────────────────────────────────────────────────────

    def add(self, ticker: str, market_title: str, alert_type: str,
            message: str, severity: str = "INFO",
            source: str = "scanner") -> Optional[ScannerAlert]:
        """
        Add an alert if not suppressed by cooldown.
        Returns the alert if created, None if suppressed.
        Never stores API keys.
        """
        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")

        # Check cooldown — same ticker + alert_type within COOLDOWN_SECS
        for a in self._alerts:
            if a.ticker == ticker and a.alert_type == alert_type:
                try:
                    last = datetime.strptime(a.last_seen_at, "%Y-%m-%d %H:%M:%S")
                    if (now - last).total_seconds() < COOLDOWN_SECS:
                        # Update last_seen but don't create duplicate
                        a.last_seen_at = now_str
                        return None
                except Exception:
                    pass

        alert = ScannerAlert(
            alert_id     = str(uuid.uuid4())[:8],
            ticker       = ticker,
            market_title = market_title[:60],
            alert_type   = alert_type,
            message      = message[:200],
            severity     = severity,
            created_at   = now_str,
            last_seen_at = now_str,
            acknowledged = False,
            source       = source,
        )
        self._alerts.append(alert)
        # Cap at 500 alerts — drop oldest acknowledged first
        if len(self._alerts) > 500:
            acked = [a for a in self._alerts if a.acknowledged]
            if acked:
                self._alerts.remove(acked[0])
            else:
                self._alerts.pop(0)
        self._save()
        self._log(f"[{severity}] {ticker}: {message}")
        return alert

    def acknowledge(self, alert_id: str) -> bool:
        for a in self._alerts:
            if a.alert_id == alert_id:
                a.acknowledged = True
                self._save()
                return True
        return False

    def acknowledge_all(self) -> int:
        count = 0
        for a in self._alerts:
            if not a.acknowledged:
                a.acknowledged = True
                count += 1
        if count:
            self._save()
        return count

    def clear_acknowledged(self) -> int:
        before = len(self._alerts)
        self._alerts = [a for a in self._alerts if not a.acknowledged]
        cleared = before - len(self._alerts)
        if cleared:
            self._save()
        return cleared

    def all_alerts(self, include_acked: bool = True) -> List[ScannerAlert]:
        alerts = self._alerts if include_acked else [
            a for a in self._alerts if not a.acknowledged]
        return sorted(alerts, key=lambda a: a.created_at, reverse=True)

    def recent_for_ticker(self, ticker: str, limit: int = 5) -> List[ScannerAlert]:
        return [a for a in self.all_alerts() if a.ticker == ticker][:limit]

    def unacked_count(self) -> int:
        return sum(1 for a in self._alerts if not a.acknowledged)

    def export_csv(self, export_dir: str = "exports") -> str:
        """Export alerts to CSV. No API keys included."""
        import csv
        out_dir = Path(export_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = out_dir / f"alerts_{ts}.csv"
        fields = ["alert_id","ticker","market_title","alert_type","message",
                  "severity","created_at","last_seen_at","acknowledged","source"]
        try:
            with open(out, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=fields)
                w.writeheader()
                for a in self.all_alerts():
                    w.writerow(asdict(a))
            return str(out)
        except Exception as e:
            self._log(f"Alert export error: {e}")
            return ""

    # ── Alert evaluation ─────────────────────────────────────────────────

    def evaluate_signals(self, signals: list, watchlist) -> int:
        """
        Check all watched markets against current signals.
        Returns count of new alerts created.
        """
        signal_map = {s.market_id: s for s in signals}
        count = 0

        for entry in watchlist.all_entries():
            ticker = entry.ticker
            sig    = signal_map.get(ticker)
            if sig is None:
                continue

            title  = entry.title or ticker
            prev   = entry.signal or "DATA NEEDED"
            curr   = sig.signal

            # Alert: signal upgrade to POSSIBLE EDGE
            if curr == "POSSIBLE EDGE" and prev not in ("POSSIBLE EDGE",):
                a = self.add(ticker, title, "SIGNAL_UPGRADE",
                    f"Signal upgraded: {prev} → POSSIBLE EDGE",
                    severity="WATCH", source="scanner")
                if a: count += 1

            # Alert: signal upgrade to WATCH from DATA NEEDED
            if (curr in ("WATCH", "PAPER ONLY") and
                    prev in ("DATA NEEDED", "NO TRADE")):
                a = self.add(ticker, title, "SIGNAL_UPGRADE",
                    f"Signal improved: {prev} → {curr}",
                    severity="INFO", source="scanner")
                if a: count += 1

            # Alert: edge above min_edge_cents target
            min_e = entry.min_edge_cents
            if min_e and sig.raw_edge and sig.raw_edge >= min_e:
                a = self.add(ticker, title, "EDGE_ABOVE",
                    f"Edge {sig.raw_edge:+.1f}c ≥ target {min_e:.0f}c",
                    severity="WATCH", source="scanner")
                if a: count += 1

            # Alert: spread below max_spread target
            max_s = entry.max_spread_cents
            if max_s and sig.spread and sig.spread <= max_s:
                a = self.add(ticker, title, "SPREAD_BELOW",
                    f"Spread {sig.spread:.1f}c ≤ target {max_s:.0f}c",
                    severity="INFO", source="scanner")
                if a: count += 1

            # Alert: yes_ask at or below target_yes_price
            if entry.target_yes_price and sig.ask_price:
                if sig.side == "YES" and sig.ask_price <= entry.target_yes_price:
                    a = self.add(ticker, title, "PRICE_TARGET",
                        f"YES ask {sig.ask_price:.0f}c ≤ target {entry.target_yes_price:.0f}c",
                        severity="WATCH", source="watchlist")
                    if a: count += 1

            # Alert: no_ask at or below target_no_price
            if entry.target_no_price and sig.ask_price:
                if sig.side == "NO" and sig.ask_price <= entry.target_no_price:
                    a = self.add(ticker, title, "PRICE_TARGET",
                        f"NO ask {sig.ask_price:.0f}c ≤ target {entry.target_no_price:.0f}c",
                        severity="WATCH", source="watchlist")
                    if a: count += 1

        return count

    # ── Persistence ──────────────────────────────────────────────────────

    def _save(self) -> None:
        try:
            with open(ALERTS_FILE, "w", encoding="utf-8") as f:
                json.dump([asdict(a) for a in self._alerts], f,
                          indent=2, default=str)
        except Exception as e:
            self._log(f"[alerts] save error: {e}")

    def _load(self) -> None:
        if not ALERTS_FILE.exists():
            return
        try:
            with open(ALERTS_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self._alerts = [ScannerAlert(**d) for d in raw]
        except Exception:
            bak = ALERTS_FILE.with_suffix(".json.bak")
            try:
                ALERTS_FILE.rename(bak)
                self._log(f"[alerts] corrupt file backed up to {bak.name}, starting empty")
            except Exception:
                pass
            self._alerts = []
