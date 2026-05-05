"""
market_scanner_engine.py
Core calculation logic for the AI Market Scanner.

All calculations are for analysis and paper trading only.
No real orders. Auto trading is OFF.

Price convention throughout: ALL prices are in CENTS (0-100).
  e.g. 44c means 44 cents = $0.44 per contract
  A $1 contract settles at either 100c (win) or 0c (loss).
"""

import math
from dataclasses import dataclass, field
from typing import Optional, Tuple
from datetime import datetime


# ── Data structures ────────────────────────────────────────────────────────

@dataclass
class TradePlan:
    """
    Human-readable trade plan for a single signal.
    All prices in cents. Size in dollars.
    """
    signal:          str           # ENTRY | STRONG ENTRY | WATCH | AVOID | NO TRADE
    side:            str           # YES | NO
    entry:           float         # suggested entry price (cents)
    breakeven:       float         # minimum exit price to not lose money (cents)
    first_target:    float         # conservative exit target (cents)
    strong_target:   float         # ideal exit target near fair value (cents)
    avoid_above:     float         # do not chase above this price (cents)
    max_risk_dollars:float         # maximum dollar risk for this trade
    contracts:       int           # suggested contract count
    buy_fee_est:     float         # estimated Kalshi fee to enter (cents total)
    sell_fee_est:    float         # estimated Kalshi fee to exit (cents total)
    total_fee_est:   float         # buy + sell fee total (cents)
    raw_edge:        float         # fair - ask (cents)
    fee_adj_edge:    float         # raw_edge minus fee per contract (cents)
    fair_price:      float         # model fair value (cents)
    ask_price:       float         # current ask price (cents)
    reason:          str           # 1-sentence plain-English explanation
    detail:          str           # multi-line detail for the UI
    data_quality:    str           # FULL | PARTIAL | MISSING


@dataclass
class MarketSignal:
    """One scanned market with all computed signal fields.
    ALL prices stored as CENTS (0–100) for display convenience.
    Input dollar prices are converted to cents via _to_cents() in analyse_market().
    format_price() must NOT be called on these — they are already cents.
    Use format_cents(value) to display them as "50c".
    """
    market_id:      str
    market_name:    str
    category:       str
    side:           str            # YES | NO
    bid_price:      float          # cents (0–100)
    ask_price:      float          # cents
    last_price:     float          # cents
    fair_price:     float          # cents, 0.0 = missing
    volume:         int
    liquidity:      str

    # Computed fields (filled by analyse_market)
    raw_edge:       float = 0.0    # cents: fair - ask
    fee_est:        float = 0.0    # cents total
    fee_adj_edge:   float = 0.0    # cents
    breakeven:      float = 0.0    # cents
    spread:         float = 0.0    # cents: ask - bid
    signal:         str   = "NO TRADE"
    suggested_size: float = 0.0    # dollars
    exit_target:    float = 0.0    # cents
    reason:         str   = ""
    status:         str   = "PAPER"
    data_quality:   str   = "FULL"
    trade_plan:     Optional[TradePlan] = field(default=None)


@dataclass
class PaperTrade:
    """One paper trade record."""
    time:          str
    market:        str
    side:          str
    entry_price:   float           # cents
    contracts:     int
    fee_paid:      float           # cents (total buy fee)
    target_exit:   float           # cents
    current_price: float           # cents
    status:        str  = "OPEN"

    @property
    def unrealized_pl(self) -> float:
        """Estimated P&L in dollars. Negative = loss."""
        if self.status != "OPEN":
            return 0.0
        gain_cents    = (self.current_price - self.entry_price) * self.contracts
        gain_dollars  = gain_cents / 100.0
        fee_dollars   = self.fee_paid / 100.0
        return round(gain_dollars - fee_dollars, 2)


@dataclass
class RiskGuard:
    """
    Enforces paper-mode limits. Auto trading is always OFF.
    can_trade() returns (False, reason) to block any real action.
    """
    max_trade_size:     float = 10.0
    max_daily_loss:     float = 30.0
    max_trades_per_day: int   = 10
    stop_after_losses:  int   = 3
    auto_trading:       bool  = False   # NEVER set to True
    trades_today:       int   = 0
    losses_today:       int   = 0
    daily_pnl:          float = 0.0

    def can_trade(self) -> Tuple[bool, str]:
        if self.auto_trading:
            return False, "Auto trading is OFF — paper mode only"
        if self.daily_pnl <= -self.max_daily_loss:
            return False, f"Daily loss limit ${self.max_daily_loss:.0f} reached"
        if self.trades_today >= self.max_trades_per_day:
            return False, f"Max {self.max_trades_per_day} trades/day reached"
        if self.losses_today >= self.stop_after_losses:
            return False, f"Stop-loss triggered after {self.stop_after_losses} losses"
        return True, "Paper mode OK"


# ── Fee calculations ───────────────────────────────────────────────────────

def calculate_kalshi_fee(contracts: int, price_cents: float) -> float:
    """
    Official Kalshi fee formula:
      fee = ceil_to_cent(0.07 × contracts × price × (1 − price))

    where price is in DOLLARS (0.0 – 1.0), not cents.

    Example:
      contracts=22, price=44c → price_dollars=0.44
      fee = ceil(0.07 × 22 × 0.44 × 0.56) = ceil(0.3793) = 0.38 → 38 cents

    Returns: fee in CENTS (total, not per contract).
    """
    if contracts <= 0 or price_cents <= 0:
        return 0.0
    price_dollars   = price_cents / 100.0
    raw_fee_dollars = 0.07 * contracts * price_dollars * (1.0 - price_dollars)
    fee_cents       = math.ceil(raw_fee_dollars * 100.0)
    return float(fee_cents)


def calculate_contracts_for_budget(budget_dollars: float,
                                    price_cents: float) -> int:
    """
    Conservative contract count for a given budget.

    Accounts for both the purchase cost and the entry fee so we
    never overspend the budget.

    Formula (per contract):
      cost_per = price_cents/100 + fee_per_contract_dollars
      fee_per  = 0.07 × price_dollars × (1 − price_dollars)
      contracts = floor(budget / cost_per)

    Args:
        budget_dollars: e.g. 10.0 for a $10 max trade
        price_cents:    e.g. 44.0 for a 44-cent market

    Returns: integer number of contracts (minimum 0).
    """
    if price_cents <= 0 or budget_dollars <= 0:
        return 0
    price_dollars = price_cents / 100.0
    fee_per       = 0.07 * price_dollars * (1.0 - price_dollars)
    cost_per      = price_dollars + fee_per
    if cost_per <= 0:
        return 0
    return max(0, int(budget_dollars / cost_per))


def calculate_raw_edge(fair_cents: float, buy_price_cents: float) -> float:
    """
    Raw (pre-fee) edge for a BUY order:
      raw_edge = fair_price − ask_price

    Positive → we're paying less than fair value (value bet).
    Negative → market is asking more than fair value (overpriced).

    Args:
        fair_cents:      model's estimate of true probability × 100
        buy_price_cents: current ask price to enter the trade
    """
    return round(fair_cents - buy_price_cents, 1)


def calculate_fee_adjusted_edge(raw_edge_cents: float,
                                 total_fee_cents: float,
                                 contracts: int) -> float:
    """
    Edge after deducting the per-contract fee burden:
      fee_adj_edge = raw_edge − (total_fee / contracts)

    This is the true edge we keep after paying Kalshi.
    If fee_adj_edge is still positive, the trade has real value.

    Args:
        raw_edge_cents:  output of calculate_raw_edge()
        total_fee_cents: total fee for the position (buy + sell estimate)
        contracts:       number of contracts in the position
    """
    if contracts <= 0:
        return raw_edge_cents
    fee_per_contract = total_fee_cents / contracts
    return round(raw_edge_cents - fee_per_contract, 1)


def calculate_breakeven_exit(entry_cents: float, contracts: int) -> float:
    """
    Minimum sell price needed to not lose money.

    Must cover:
      1. Entry cost   (entry_cents × contracts)
      2. Buy fee      (calculate_kalshi_fee at entry)
      3. Sell fee     (estimated at breakeven — one iteration)

    Derivation:
      total_needed = entry × n + buy_fee
      sell_revenue = sell_price × n − sell_fee(sell_price)
      Set sell_revenue = total_needed, solve for sell_price.
      (One Newton iteration is sufficient for our precision.)

    Returns: breakeven exit price in cents.
    """
    if contracts <= 0 or entry_cents <= 0:
        return 0.0

    buy_fee = calculate_kalshi_fee(contracts, entry_cents)

    # Estimate: first guess = entry + fee burden per contract
    est_sell    = entry_cents + (buy_fee / contracts)
    sell_fee    = calculate_kalshi_fee(contracts, est_sell)

    # One refinement step
    total_out   = entry_cents * contracts + buy_fee + sell_fee
    breakeven   = total_out / contracts
    return round(breakeven, 1)


# ── Signal classification ──────────────────────────────────────────────────

def classify_signal(
    edge_cents:     float,
    spread_cents:   float,
    fair_price:     float,
    max_spread:     float = 5.0,
    min_edge:       float = 8.0,
    liquidity:      str   = "Medium",
    fee_adj_edge:   float = 0.0,
) -> str:
    """
    Classify a market into one of five signal tiers.

    Decision tree (evaluated top to bottom — first match wins):

    1. DATA NEEDED  — fair price is 0 or missing: cannot calculate edge
    2. NO TRADE     — spread too wide or liquidity too low for the spread
    3. AVOID        — raw edge is negative (market is overpriced)
    4. WATCH        — edge positive but below minimum threshold
    5. ENTRY        — edge above minimum threshold
    6. STRONG ENTRY — edge well above threshold AND tight spread AND good liquidity

    Args:
        edge_cents:   raw edge (fair - ask) in cents
        spread_cents: bid-ask spread in cents
        fair_price:   model fair price in cents (0 = unknown)
        max_spread:   maximum acceptable spread (cents)
        min_edge:     minimum edge to trigger ENTRY (cents)
        liquidity:    "High" | "Medium" | "Low"
        fee_adj_edge: fee-adjusted edge (used for STRONG ENTRY gate)
    """
    # Gate 1 — missing fair price
    if fair_price <= 0:
        return "DATA NEEDED"

    # Gate 2 — spread / liquidity
    if liquidity == "Low" and spread_cents > max_spread * 0.6:
        return "NO TRADE"
    if spread_cents > max_spread:
        return "NO TRADE"

    # Gate 3 — negative edge
    if edge_cents <= 0:
        return "AVOID"

    # Gate 4 — below threshold
    if edge_cents < min_edge:
        return "WATCH"

    # Gate 5/6 — ENTRY vs STRONG ENTRY
    # STRONG ENTRY: edge is meaningfully above minimum, spread tight,
    # liquidity good, and fee-adjusted edge is still positive.
    strong_edge_threshold = min_edge + 3.0
    if (edge_cents >= strong_edge_threshold
            and spread_cents <= 3.0
            and liquidity in ("High", "Medium")
            and fee_adj_edge > 0):
        return "STRONG ENTRY"

    return "ENTRY"


def _suggest_size(signal: str, max_size: float, edge_cents: float) -> float:
    """
    Conservative position sizing by signal tier.

    STRONG ENTRY → full max_size
    ENTRY        → 60% of max_size (min $5)
    others       → $0 (no trade recommended)
    """
    if signal == "STRONG ENTRY":
        return max_size
    if signal == "ENTRY":
        return min(max_size, max(5.0, max_size * 0.6))
    return 0.0


def _suggest_exit(fair_cents: float, ask_cents: float, signal: str) -> float:
    """
    Conservative first exit target.

    For actionable signals:
      first_target = ask + 60% of the raw edge
    This locks in most of the edge before the market fully reprices.
    """
    if signal in ("ENTRY", "STRONG ENTRY"):
        raw = fair_cents - ask_cents
        return round(ask_cents + raw * 0.6, 1)
    return 0.0


# ── Human-readable explanation builder ────────────────────────────────────

# ── Signal scoring ───────────────────────────────────────────────────────────

SIGNAL_PRIORITY = {
    "POSSIBLE EDGE": 0,
    "STRONG ENTRY":  1,
    "ENTRY":         2,
    "WATCH":         3,
    "PAPER ONLY":    4,
    "CAUTION":       5,
    "DATA NEEDED":   6,
    "AVOID":         7,
    "NO TRADE":      8,
}


def score_market(
    signal:       str,
    spread_cents: float,
    liquidity:    str,
    bid:          float,
    ask:          float,
    fair:         float,
    volume:       int,
    extra:        dict = None,   # optional: {"distance_pct": float, "time_left_mins": int}
) -> dict:
    """
    Compute a 0-100 signal score and augmented signal tier.

    Returns:
        {
            "score":       int,       # 0 (worst) to 100 (best)
            "tier":        str,       # upgraded signal label
            "reasons":     list[str], # human-readable positive reasons
            "risks":       list[str], # human-readable risk factors
            "suggested":   str,       # one-line recommended action
            "data_issues": list[str], # missing data problems
        }

    Does NOT fabricate edge. Missing fair price → conservative result.
    """
    extra       = extra or {}
    score       = 0
    reasons     = []
    risks       = []
    data_issues = []
    tier        = signal

    # ── Data availability ──────────────────────────────────────────────
    if ask <= 0:
        data_issues.append("Missing ask price — load orderbook first")
        tier = "DATA NEEDED"
    if bid <= 0:
        data_issues.append("Missing bid price")
    if fair <= 0:
        data_issues.append("No fair price model — cannot calculate true edge")
        risks.append("Fair value unavailable — paper/watch only")

    if not data_issues:
        score += 20
        reasons.append("Quote available (bid/ask loaded)")

    # ── Spread ─────────────────────────────────────────────────────────
    if ask > 0 and bid > 0:
        if spread_cents <= 2:
            score += 20
            reasons.append(f"Tight spread ({spread_cents:.1f}c)")
        elif spread_cents <= 5:
            score += 10
            reasons.append(f"Acceptable spread ({spread_cents:.1f}c)")
        elif spread_cents <= 10:
            score += 0
            risks.append(f"Wide spread ({spread_cents:.1f}c)")
        else:
            score -= 10
            risks.append(f"Very wide spread ({spread_cents:.1f}c) — CAUTION")
            if tier not in ("DATA NEEDED", "AVOID"):
                tier = "CAUTION"

    # ── Liquidity ──────────────────────────────────────────────────────
    liq_scores = {"High": 20, "Medium": 10, "Low": 0}
    liq_score  = liq_scores.get(liquidity, 5)
    score += liq_score
    if liquidity == "High":
        reasons.append("High liquidity")
    elif liquidity == "Low":
        risks.append("Low liquidity — fill uncertainty")
        if tier not in ("DATA NEEDED", "AVOID"):
            tier = "CAUTION"

    # ── Volume ─────────────────────────────────────────────────────────
    if volume > 10000:
        score += 10
        reasons.append(f"High volume ({volume:,})")
    elif volume > 1000:
        score += 5
    elif volume == 0:
        data_issues.append("No volume data")

    # ── Crypto reference distance ───────────────────────────────────────
    dist_pct = extra.get("distance_pct")
    if dist_pct is not None:
        abs_dist = abs(dist_pct)
        if abs_dist <= 1.0:
            score += 15
            reasons.append(f"Price very close to target ({dist_pct:+.2f}%)")
            if tier in ("WATCH",):
                tier = "PAPER ONLY"
        elif abs_dist <= 3.0:
            score += 8
            reasons.append(f"Price near target ({dist_pct:+.2f}%)")
        else:
            risks.append(f"Price far from target ({dist_pct:+.2f}%)")

    # ── Time to expiration ─────────────────────────────────────────────
    time_left = extra.get("time_left_mins")
    if time_left is not None:
        if time_left < 15:
            score -= 15
            risks.append(f"Expiring very soon ({time_left}m) — CAUTION")
            if tier not in ("DATA NEEDED", "AVOID"):
                tier = "CAUTION"
        elif time_left < 60:
            score -= 5
            risks.append(f"Less than 1 hour to expiration ({time_left}m)")
        elif time_left > 1440:
            score += 5
            reasons.append(f"Plenty of time remaining ({time_left//60}h)")

    # ── Fair price edge ────────────────────────────────────────────────
    if fair > 0 and ask > 0:
        edge = fair - ask
        if edge >= 12:
            score += 20
            tier = "POSSIBLE EDGE"
            reasons.append(f"Strong edge: {edge:+.1f}c above fair value")
        elif edge >= 8:
            score += 15
            reasons.append(f"Edge: {edge:+.1f}c above fair value")
        elif edge >= 3:
            score += 8
            reasons.append(f"Positive edge: {edge:+.1f}c")
        elif edge < 0:
            score -= 10
            risks.append(f"Negative edge ({edge:+.1f}c) — market overpriced")

    score = max(0, min(100, score))

    # ── Suggested action ───────────────────────────────────────────────
    if tier == "POSSIBLE EDGE":
        suggested = "Consider paper trade — edge present if fair model is correct"
    elif tier in ("WATCH", "PAPER ONLY"):
        suggested = "Add to watchlist — monitor for better entry or confirmation"
    elif tier == "CAUTION":
        suggested = "Wait — spread/liquidity/timing unfavorable"
    elif tier == "DATA NEEDED":
        suggested = "Load orderbook and enable fair price model first"
    elif tier == "AVOID":
        suggested = "Market appears overpriced — skip"
    else:
        suggested = "Monitor only"

    return {
        "score":       score,
        "tier":        tier,
        "reasons":     reasons,
        "risks":       risks,
        "suggested":   suggested,
        "data_issues": data_issues,
    }


def build_trade_plan(
    raw:          dict,
    signal:       str,
    edge:         float,
    fee_adj_edge: float,
    breakeven:    float,
    contracts:    int,
    buy_fee:      float,
    fair:         float,
    ask:          float,
    bid:          float,
    spread:       float,
    max_size:     float,
    min_edge:     float,
) -> TradePlan:
    """
    Build a complete TradePlan with human-readable explanation.

    All prices in cents. Returns a TradePlan dataclass.
    """
    side      = raw.get("side", "YES")
    market    = raw.get("market_name", "")
    liquidity = raw.get("liquidity", "Medium")

    # Sell fee estimate at the first target
    exit_target    = _suggest_exit(fair, ask, signal)
    sell_fee       = calculate_kalshi_fee(contracts, exit_target) if exit_target > 0 else 0.0
    total_fee      = buy_fee + sell_fee
    avoid_above    = round(ask + 3, 1)
    strong_target  = round(fair * 0.97, 1)
    max_risk       = _suggest_size(signal, max_size, edge)
    data_quality   = _data_quality(raw)

    # ── Plain-English reason (one sentence) ───────────────────────────────
    # Build context-aware reason
    # ask_missing: no ask price means bid/ask not yet loaded from orderbook
    _ask_missing_in_plan = (ask == 0)
    if _ask_missing_in_plan:
        data_needed_reason = (
            "Kalshi market data loaded, but model fair price is not available yet. "
            "Click 'Load Orderbook' to fetch bid/ask prices for this market, "
            "then connect a pricing model to generate ENTRY signals."
        )
    elif fair == 0:
        data_needed_reason = (
            "Kalshi market loaded with live bid/ask. "
            "Model fair price is not available yet — cannot calculate edge. "
            "Signal will upgrade once a fair price estimate is added."
        )
    else:
        data_needed_reason = (
            "No model fair price available — cannot calculate edge. "
            "Add a fair price estimate before trading."
        )

    reasons = {
        "STRONG ENTRY": (
            f"Model fair value is {fair:.0f}c but market asks only {ask:.0f}c "
            f"— {edge:+.0f}c raw edge, {fee_adj_edge:+.0f}c after fees, "
            f"tight {spread:.0f}c spread, {liquidity.lower()} liquidity."
        ),
        "ENTRY": (
            f"Model fair value {fair:.0f}c vs ask {ask:.0f}c "
            f"gives {edge:+.0f}c edge ({fee_adj_edge:+.0f}c after fees). "
            f"Spread {spread:.0f}c is acceptable."
        ),
        "WATCH": (
            f"Edge is {edge:+.0f}c — positive but below the {min_edge:.0f}c "
            f"minimum threshold. Monitor for improvement."
        ),
        "AVOID": (
            f"Market ask {ask:.0f}c exceeds model fair {fair:.0f}c "
            f"by {-edge:.0f}c — do not buy at this price."
        ),
        "NO TRADE": (
            f"Spread {spread:.0f}c exceeds limit or {liquidity.lower()} "
            f"liquidity makes fill uncertain."
        ),
        "DATA NEEDED": data_needed_reason,
    }
    reason = reasons.get(signal, "Unknown signal.")

    # ── Multi-line detail for the UI ──────────────────────────────────────
    if signal in ("ENTRY", "STRONG ENTRY"):
        detail = (
            f"Buy {side} at {ask:.0f}c or better.\n"
            f"Contracts at ${max_risk:.0f}: ~{contracts}\n"
            f"Entry fee (est): {buy_fee:.0f}c\n"
            f"Breakeven exit:  {breakeven:.0f}c\n"
            f"First target:    {exit_target:.0f}c\n"
            f"Strong target:   {strong_target:.0f}c\n"
            f"Do not chase above {avoid_above:.0f}c.\n"
            f"Total fees (est): {total_fee:.0f}c\n"
            f"Mode: Paper only — no real orders sent."
        )
    elif signal == "WATCH":
        detail = (
            f"Edge {edge:+.0f}c is below {min_edge:.0f}c minimum.\n"
            f"Watch for ask to drop below {fair - min_edge:.0f}c.\n"
            f"No position recommended yet."
        )
    elif signal == "DATA NEEDED":
        detail = (
            "Fair price is missing or zero.\n"
            "Cannot compute edge without a model estimate.\n"
            "Signal will update when fair price is available."
        )
    else:
        detail = reason

    return TradePlan(
        signal           = signal,
        side             = side,
        entry            = ask,
        breakeven        = breakeven,
        first_target     = exit_target if exit_target > 0 else 0.0,
        strong_target    = strong_target if fair > 0 else 0.0,
        avoid_above      = avoid_above,
        max_risk_dollars = max_risk,
        contracts        = contracts,
        buy_fee_est      = buy_fee,
        sell_fee_est     = sell_fee,
        total_fee_est    = total_fee,
        raw_edge         = edge,
        fee_adj_edge     = fee_adj_edge,
        fair_price       = fair,
        ask_price        = ask,
        reason           = reason,
        detail           = detail,
        data_quality     = data_quality,
    )


def _data_quality(raw: dict) -> str:
    """
    Assess how complete the market data is.

    FULL    — fair price + bid + ask all present
    PARTIAL — some prices missing or zero
    MISSING — fair price not available
    """
    fair = raw.get("model_fair_price", 0.0) or 0.0
    bid  = raw.get("bid_price", 0.0) or 0.0
    ask  = raw.get("ask_price", 0.0) or 0.0

    if fair <= 0:
        return "MISSING"
    if bid <= 0 or ask <= 0:
        return "PARTIAL"
    return "FULL"


# ── Full market analysis ───────────────────────────────────────────────────

def analyse_market(
    raw:        dict,
    min_edge:   float = 8.0,
    max_spread: float = 5.0,
    max_size:   float = 10.0,
) -> MarketSignal:
    """
    Analyse one market dict and return a fully computed MarketSignal.

    Args:
        raw:        dict with keys: market_id, market_name, category, side,
                    bid_price, ask_price, last_price, model_fair_price,
                    volume, liquidity
        min_edge:   minimum cents of edge to trigger ENTRY signal
        max_spread: maximum cents of spread allowed for any trade
        max_size:   maximum dollar size for position sizing

    Returns:
        MarketSignal with all fields populated, including a TradePlan.
    """
    # ── Extract raw values ─────────────────────────────────────────────
    # Prices from connectors are dollar floats (0.0-1.0).
    # The engine works in CENTS (0-100), so we multiply by 100.
    # None means the price was not available → DATA NEEDED signal.
    _bid_raw  = raw.get("bid_price",        None)
    _ask_raw  = raw.get("ask_price",        None)
    _last_raw = raw.get("last_price",       None)
    _fair_raw = raw.get("model_fair_price", None)

    def _to_cents(v, default=0.0) -> float:
        """Convert dollar float to cents. None → default (not 0)."""
        if v is None:
            return default
        try:
            f = float(v)
            # Dollar format: 0.0-1.0 → multiply by 100 to get cents
            # Cents format: already >1 (legacy) → use as-is
            if 0.0 <= f <= 1.0:
                return round(f * 100.0, 2)
            return f   # already in cents (legacy path)
        except:
            return default

    bid       = _to_cents(_bid_raw,  0.0)
    ask       = _to_cents(_ask_raw,  0.0)
    last      = _to_cents(_last_raw, ask)
    fair      = _to_cents(_fair_raw, 0.0)
    liquidity = raw.get("liquidity", "Medium")
    volume    = int(raw.get("volume", 0) or 0)

    # Track whether prices were actually provided vs missing
    bid_missing  = _bid_raw  is None
    ask_missing  = _ask_raw  is None
    fair_missing = _fair_raw is None

    # ── Derived quantities ─────────────────────────────────────────────
    spread    = round(max(0.0, ask - bid), 1)
    contracts = calculate_contracts_for_budget(max_size, ask) if ask > 0 else 0

    # ── Fees ───────────────────────────────────────────────────────────
    buy_fee   = calculate_kalshi_fee(max(contracts, 1), ask) if ask > 0 else 0.0

    # ── Edge ───────────────────────────────────────────────────────────
    raw_edge  = calculate_raw_edge(fair, ask) if fair > 0 else 0.0
    fee_adj   = calculate_fee_adjusted_edge(raw_edge, buy_fee, max(contracts, 1))

    # ── Breakeven ──────────────────────────────────────────────────────
    breakeven = calculate_breakeven_exit(ask, max(contracts, 1)) if ask > 0 else 0.0

    # ── Signal ─────────────────────────────────────────────────────────
    # If bid/ask not loaded (Kalshi markets before orderbook fetch),
    # force DATA NEEDED — we cannot compute edge without a buy price.
    if ask_missing or ask == 0:
        signal = "DATA NEEDED"
    else:
        signal = classify_signal(
            edge_cents   = raw_edge,
            spread_cents = spread,
            fair_price   = fair,
            max_spread   = max_spread,
            min_edge     = min_edge,
            liquidity    = liquidity,
            fee_adj_edge = fee_adj,
        )

    # ── Sizing and targets ─────────────────────────────────────────────
    size      = _suggest_size(signal, max_size, raw_edge)
    exit_tgt  = _suggest_exit(fair, ask, signal)

    # ── Trade plan ─────────────────────────────────────────────────────
    plan = build_trade_plan(
        raw          = raw,
        signal       = signal,
        edge         = raw_edge,
        fee_adj_edge = fee_adj,
        breakeven    = breakeven,
        contracts    = max(contracts, 0),
        buy_fee      = buy_fee,
        fair         = fair,
        ask          = ask,
        bid          = bid,
        spread       = spread,
        max_size     = max_size,
        min_edge     = min_edge,
    )

    return MarketSignal(
        market_id      = str(raw.get("market_id",    "")),
        market_name    = str(raw.get("market_name",  "")),
        category       = str(raw.get("category",     "")),
        side           = str(raw.get("side",         "YES")),
        bid_price      = bid,
        ask_price      = ask,
        last_price     = last,
        fair_price     = fair,
        volume         = volume,
        liquidity      = liquidity,
        raw_edge       = raw_edge,
        fee_est        = buy_fee,
        fee_adj_edge   = fee_adj,
        breakeven      = breakeven,
        spread         = spread,
        signal         = signal,
        suggested_size = size,
        exit_target    = exit_tgt,
        reason         = plan.reason,
        status         = "PAPER",
        data_quality   = plan.data_quality,
        trade_plan     = plan,
    )


def run_scanner(
    markets:    list,
    min_edge:   float = 8.0,
    max_spread: float = 5.0,
    max_size:   float = 10.0,
) -> list:
    """
    Analyse a list of raw market dicts and return sorted MarketSignal list.

    Sort order: STRONG ENTRY → ENTRY → WATCH → AVOID → NO TRADE → DATA NEEDED
    Within each tier: sorted by absolute edge descending.

    Args:
        markets:    list of dicts (from DataLayer.fetch or any connector)
        min_edge:   cents of edge required for ENTRY signal
        max_spread: maximum cents of spread for tradeable markets
        max_size:   maximum dollar size for position sizing

    Returns:
        list of MarketSignal, sorted best to worst.
    """
    order = {
        "STRONG ENTRY": 0,
        "ENTRY":        1,
        "WATCH":        2,
        "AVOID":        3,
        "NO TRADE":     4,
        "DATA NEEDED":  5,
    }

    signals = []
    for m in markets:
        try:
            sig = analyse_market(m, min_edge, max_spread, max_size)
            signals.append(sig)
        except Exception as e:
            # One bad market never crashes the whole scan
            print(f"[scanner] skipped {m.get('market_id','?')}: {e}")

    signals.sort(key=lambda s: (order.get(s.signal, 9), -abs(s.raw_edge)))
    return signals
