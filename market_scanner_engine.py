"""
market_scanner_engine.py
Core calculation logic for the AI Market Scanner.
No API keys required — works with mock or live data connectors.
"""

import math
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


# ──────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────

@dataclass
class MarketSignal:
    market_id:      str
    market_name:    str
    category:       str
    side:           str           # YES / NO
    bid_price:      float         # cents 0-100
    ask_price:      float
    last_price:     float
    fair_price:     float         # model estimate
    volume:         int
    liquidity:      str           # High / Medium / Low
    # computed
    raw_edge:       float  = 0.0
    fee_est:        float  = 0.0
    fee_adj_edge:   float  = 0.0
    breakeven:      float  = 0.0
    spread:         float  = 0.0
    signal:         str    = "NO TRADE"
    suggested_size: float  = 0.0
    exit_target:    float  = 0.0
    reason:         str    = ""
    status:         str    = "WATCH"


@dataclass
class PaperTrade:
    time:          str
    market:        str
    side:          str
    entry_price:   float
    contracts:     int
    fee_paid:      float
    target_exit:   float
    current_price: float
    status:        str    = "OPEN"

    @property
    def unrealized_pl(self) -> float:
        if self.status != "OPEN":
            return 0.0
        gain = (self.current_price - self.entry_price) / 100.0 * self.contracts
        return round(gain - self.fee_paid / 100.0, 2)


@dataclass
class RiskGuard:
    max_trade_size:      float = 10.0
    max_daily_loss:      float = 30.0
    max_trades_per_day:  int   = 10
    stop_after_losses:   int   = 3
    auto_trading:        bool  = False
    trades_today:        int   = 0
    losses_today:        int   = 0
    daily_pnl:           float = 0.0

    def can_trade(self) -> tuple[bool, str]:
        if self.auto_trading:
            return False, "Auto trading is OFF"
        if self.daily_pnl <= -self.max_daily_loss:
            return False, f"Daily loss limit ${self.max_daily_loss} reached"
        if self.trades_today >= self.max_trades_per_day:
            return False, f"Max trades/day ({self.max_trades_per_day}) reached"
        if self.losses_today >= self.stop_after_losses:
            return False, f"Stop after {self.stop_after_losses} losses triggered"
        return True, "OK"


# ──────────────────────────────────────────────
# Core calculations
# ──────────────────────────────────────────────

def calculate_kalshi_fee(contracts: int, price_cents: float) -> float:
    """
    Kalshi fee formula:
    fee = ceil_to_cent(0.07 * contracts * price * (1 - price))
    price is in dollars (e.g. 44c = 0.44)
    Returns fee in cents.
    """
    price_dollars = price_cents / 100.0
    raw_fee_dollars = 0.07 * contracts * price_dollars * (1.0 - price_dollars)
    # Ceil to nearest cent
    fee_cents = math.ceil(raw_fee_dollars * 100.0)
    return float(fee_cents)


def calculate_contracts(budget_dollars: float, price_cents: float) -> int:
    """
    How many contracts can we buy for this budget at this price?
    Accounts for fee reducing effective capital.
    """
    if price_cents <= 0:
        return 0
    price_dollars = price_cents / 100.0
    # Rough: contracts = budget / (price + fee_per_contract)
    # fee_per_contract ≈ 0.07 * price * (1 - price)
    fee_per = 0.07 * price_dollars * (1.0 - price_dollars)
    total_per = price_dollars + fee_per
    if total_per <= 0:
        return 0
    return max(0, int(budget_dollars / total_per))


def calculate_breakeven(entry_cents: float, contracts: int) -> float:
    """
    Estimate the sell price needed to break even.
    Must cover: entry cost + buy fee + estimated sell fee.
    Returns breakeven in cents.
    """
    if contracts <= 0:
        return 0.0
    buy_fee   = calculate_kalshi_fee(contracts, entry_cents)
    # Estimate sell fee at breakeven (iterate once)
    est_sell  = entry_cents + (buy_fee / contracts)
    sell_fee  = calculate_kalshi_fee(contracts, est_sell)
    total_cost = entry_cents * contracts + buy_fee + sell_fee
    breakeven  = total_cost / contracts
    return round(breakeven, 1)


def calculate_raw_edge(fair_cents: float, ask_cents: float) -> float:
    """
    Raw edge for a BUY order:
    edge = fair_price - ask_price
    Positive = value, negative = overpriced.
    """
    return round(fair_cents - ask_cents, 1)


def calculate_fee_adjusted_edge(raw_edge: float, fee_cents: float,
                                 contracts: int) -> float:
    """Edge after fee cost is subtracted."""
    if contracts <= 0:
        return raw_edge
    fee_per_contract = fee_cents / contracts
    return round(raw_edge - fee_per_contract, 1)


def classify_signal(
    edge:             float,
    spread:           float,
    max_spread:       float = 5.0,
    min_edge:         float = 8.0,
    liquidity:        str   = "Medium",
) -> str:
    if liquidity == "Low" and spread > max_spread * 0.6:
        return "NO TRADE"
    if spread > max_spread:
        return "NO TRADE"
    if edge <= 0:
        return "AVOID"
    if edge < min_edge:
        return "WATCH"
    if edge >= min_edge + 5 and spread <= 2:
        return "STRONG ENTRY"
    if edge >= min_edge:
        return "ENTRY"
    return "WATCH"


def suggest_size(signal: str, max_size: float, edge: float) -> float:
    if signal == "STRONG ENTRY":
        return max_size
    if signal == "ENTRY":
        return min(max_size, max(5.0, max_size * 0.6))
    return 0.0


def suggest_exit(fair_cents: float, signal: str) -> Optional[float]:
    if signal in ("ENTRY", "STRONG ENTRY"):
        return round(fair_cents * 0.97, 1)  # slight discount to fair
    return None


# ──────────────────────────────────────────────
# Full market analysis
# ──────────────────────────────────────────────

def analyse_market(
    raw:          dict,
    min_edge:     float = 8.0,
    max_spread:   float = 5.0,
    max_size:     float = 10.0,
) -> MarketSignal:
    """
    Takes a raw market dict and returns a fully computed MarketSignal.
    """
    bid   = raw.get("bid_price", 0.0)
    ask   = raw.get("ask_price", 0.0)
    fair  = raw.get("model_fair_price", 0.0)
    contracts = calculate_contracts(max_size, ask)
    fee   = calculate_kalshi_fee(max(contracts, 1), ask)
    spread= round(ask - bid, 1)
    edge  = calculate_raw_edge(fair, ask)
    fadj  = calculate_fee_adjusted_edge(edge, fee, max(contracts, 1))
    beven = calculate_breakeven(ask, max(contracts, 1))
    sig   = classify_signal(edge, spread, max_spread, min_edge,
                             raw.get("liquidity", "Medium"))
    size  = suggest_size(sig, max_size, edge)
    exit_ = suggest_exit(fair, sig)

    reasons = {
        "STRONG ENTRY": f"Model fair {fair:.0f}c vs ask {ask:.0f}c — {edge:+.0f}c edge, tight spread, strong value.",
        "ENTRY":        f"Model fair {fair:.0f}c vs ask {ask:.0f}c — {edge:+.0f}c edge above minimum.",
        "WATCH":        f"Edge {edge:+.0f}c is positive but below {min_edge:.0f}c threshold. Monitor.",
        "AVOID":        f"Model fair {fair:.0f}c below ask {ask:.0f}c — market is overpriced.",
        "NO TRADE":     f"Spread {spread:.0f}c exceeds limit or liquidity too low.",
    }

    return MarketSignal(
        market_id      = raw.get("market_id", ""),
        market_name    = raw.get("market_name", ""),
        category       = raw.get("category", ""),
        side           = raw.get("side", "YES"),
        bid_price      = bid,
        ask_price      = ask,
        last_price     = raw.get("last_price", ask),
        fair_price     = fair,
        volume         = raw.get("volume", 0),
        liquidity      = raw.get("liquidity", "Medium"),
        raw_edge       = edge,
        fee_est        = fee,
        fee_adj_edge   = fadj,
        breakeven      = beven,
        spread         = spread,
        signal         = sig,
        suggested_size = size,
        exit_target    = exit_ or 0.0,
        reason         = reasons.get(sig, ""),
        status         = "PAPER",
    )


def run_scanner(
    markets:    list,
    min_edge:   float = 8.0,
    max_spread: float = 5.0,
    max_size:   float = 10.0,
) -> list:
    """Analyse a list of raw market dicts and return sorted MarketSignal list."""
    signals = [analyse_market(m, min_edge, max_spread, max_size) for m in markets]
    # Sort: STRONG ENTRY first, then ENTRY, WATCH, AVOID, NO TRADE
    order = {"STRONG ENTRY": 0, "ENTRY": 1, "WATCH": 2, "AVOID": 3, "NO TRADE": 4}
    signals.sort(key=lambda s: (order.get(s.signal, 5), -abs(s.raw_edge)))
    return signals
