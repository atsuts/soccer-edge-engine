"""
match_bridge.py
Bridges live_data.py -> soccer_phase1_engine.py
Converts a live API match into MatchState + MarketInput
and runs full analysis automatically. No manual input needed.
"""

from __future__ import annotations
from typing import Dict, Any, Optional
from dataclasses import dataclass

from soccer_phase1_engine import (
    SoccerEdgeEngine,
    MatchState,
    MarketInput,
    ModelConfig,
)
from live_data import fetch_full_match_data


@dataclass
class AnalysisResult:
    state:         MatchState
    market:        MarketInput
    probabilities: Dict[str, float]
    confidence:    float
    data_quality:  Dict[str, str]
    best_pick:     str
    best_edge:     float
    reasoning:     list
    warnings:      list


def score_confidence(bundle: Dict[str, Any], minute: int):
    score = 0.5
    quality = {}

    if bundle["lineups"].get("confirmed"):
        score += 0.15
        quality["lineups"] = "Confirmed"
    else:
        score -= 0.10
        quality["lineups"] = "Unconfirmed"

    if bundle["odds"].get("1x2", {}).get("draw") is not None:
        score += 0.10
        quality["odds"] = "Live"
    else:
        quality["odds"] = "Missing"

    if bundle["stats"].get("home"):
        score += 0.10
        quality["stats"] = "Live"
    else:
        quality["stats"] = "Missing"

    if minute >= 75:
        score += 0.10
        quality["time"] = "Late game"
    elif minute >= 45:
        score += 0.05
        quality["time"] = "Second half"
    else:
        quality["time"] = "Early"

    if bundle["h2h"]:
        score += 0.05
        quality["h2h"] = "Available"
    else:
        quality["h2h"] = "Missing"

    if bundle["errors"]:
        score -= 0.05 * len(bundle["errors"])
        quality["errors"] = f"{len(bundle['errors'])} source(s) failed"

    score = max(0.10, min(0.95, score))
    return round(score, 2), quality


def pressure_from_possession(home_poss: float) -> int:
    if home_poss >= 65:
        return 2
    elif home_poss >= 57:
        return 1
    elif home_poss <= 35:
        return -2
    elif home_poss <= 43:
        return -1
    return 0


def build_reasoning(state, probs, market, engine, bundle):
    reasons = []
    warnings = []

    draw_edge = engine.fair_cents(probs["draw_prob"]) - (market.draw_cents or 0)
    over_edge = engine.fair_cents(probs["over_prob"]) - (market.over_cents or 0)
    under_edge = engine.fair_cents(probs["under_prob"]) - (market.under_cents or 0)

    if probs["draw_prob"] > 0.35:
        reasons.append(f"Draw probability {probs['draw_prob']*100:.0f}% above baseline.")
    if state.minute >= 70 and state.home_goals == state.away_goals:
        reasons.append("Late game draw state — time pressure reduces goal rate.")
    if abs(draw_edge) >= 8 or abs(over_edge) >= 8 or abs(under_edge) >= 8:
        reasons.append("Model finds significant discrepancy vs market price.")

    home_xg, away_xg = bundle.get("xg", (0, 0))
    if abs(home_xg - away_xg) > 0.4:
        dominant = state.home_team if home_xg > away_xg else state.away_team
        reasons.append(f"xG favors {dominant} ({home_xg:.2f} vs {away_xg:.2f}).")

    if not bundle["lineups"].get("confirmed"):
        warnings.append("Lineups not confirmed — team strength uncertain.")
    if state.minute < 20:
        warnings.append("Early game — high variance, model less reliable.")
    if bundle["errors"]:
        warnings.append(f"Data gaps: {', '.join(bundle['errors'][:2])}")

    return reasons, warnings


def analyze_live_match(
    fixture_id: int,
    home_team: str,
    away_team: str,
    home_id: int,
    away_id: int,
    home_goals: int,
    away_goals: int,
    minute: int,
    config: Optional[ModelConfig] = None,
) -> AnalysisResult:
    engine = SoccerEdgeEngine(config)

    bundle = fetch_full_match_data(fixture_id, home_id, away_id)

    home_poss, away_poss = bundle.get("possession", (50.0, 50.0))
    pressure = pressure_from_possession(home_poss)
    home_reds, away_reds = bundle.get("red_cards", (0, 0))

    state = MatchState(
        home_team=home_team,
        away_team=away_team,
        minute=minute,
        home_goals=home_goals,
        away_goals=away_goals,
        home_red_cards=home_reds,
        away_red_cards=away_reds,
        pressure_bias=pressure,
        stoppage_minutes_remaining=0,
    )

    odds = bundle.get("odds", {})

    def prob_to_cents(p):
        return round(p * 100, 1) if p else None

    market = MarketInput(
        total_line=2.5,
        draw_cents=prob_to_cents(odds.get("1x2", {}).get("draw")),
        over_cents=prob_to_cents(odds.get("over_2_5")),
        under_cents=prob_to_cents(odds.get("under_2_5")),
    )

    probs = engine.full_analysis(state, market)

    confidence, data_quality = score_confidence(bundle, minute)

    picks = []
    if market.draw_cents:
        picks.append(("DRAW", engine.fair_cents(probs["draw_prob"]) - market.draw_cents))
    if market.over_cents:
        picks.append(("OVER 2.5", engine.fair_cents(probs["over_prob"]) - market.over_cents))
    if market.under_cents:
        picks.append(("UNDER 2.5", engine.fair_cents(probs["under_prob"]) - market.under_cents))

    picks.sort(key=lambda x: x[1], reverse=True)
    best_pick = picks[0][0] if picks else "NO DATA"
    best_edge = picks[0][1] if picks else 0.0

    reasoning, warnings = build_reasoning(state, probs, market, engine, bundle)

    return AnalysisResult(
        state=state,
        market=market,
        probabilities=probs,
        confidence=confidence,
        data_quality=data_quality,
        best_pick=best_pick,
        best_edge=best_edge,
        reasoning=reasoning,
        warnings=warnings,
    )


def analyze_from_gui_match(match: Dict[str, Any]) -> Optional[AnalysisResult]:
    """
    Pass in a match dict from the GUI match list.
    Returns a full AnalysisResult or None if it fails.
    """
    try:
        return analyze_live_match(
            fixture_id=match["fixture_id"],
            home_team=match["home"],
            away_team=match["away"],
            home_id=match["home_id"],
            away_id=match["away_id"],
            home_goals=match["home_goals"],
            away_goals=match["away_goals"],
            minute=match["minute"],
        )
    except Exception as e:
        print(f"[bridge] Failed: {match.get('home')} vs {match.get('away')}: {e}")
        return None