"""
match_bridge.py — Bridge between live API data and soccer analysis engine.

Provides analyze_from_gui_match() which soccer_gui.py calls when a match
is selected, to enrich it with Poisson probability estimates.

If the soccer_phase1_engine module is unavailable, returns a safe placeholder
so the GUI never crashes on import.
"""

from typing import Optional


def analyze_from_gui_match(match: dict) -> Optional[dict]:
    """
    Run soccer analysis on a GUI match dict.
    Returns enriched result dict, or None if analysis unavailable.

    match dict keys used:
      home, away, home_score, away_score, minute, status,
      home_avg, away_avg, home_form, away_form

    Returns dict with keys:
      home_win_pct, draw_pct, away_win_pct,
      over25_pct, btts_pct,
      recommended_bet, edge, confidence,
      model_used
    """
    try:
        from soccer_phase1_engine import analyze_match
        return analyze_match(match)
    except ImportError:
        pass
    except Exception:
        pass

    # Safe placeholder when engine unavailable
    return {
        "home_win_pct":   33.0,
        "draw_pct":       33.0,
        "away_win_pct":   34.0,
        "over25_pct":     50.0,
        "btts_pct":       45.0,
        "recommended_bet": "—",
        "edge":            0.0,
        "confidence":      "LOW",
        "model_used":      "placeholder",
    }


# ── Compatibility shim ─────────────────────────────────────────────────────
# Some older imports may reference fetch_full_match_data by name.
# This shim prevents ImportError crashes.

def fetch_full_match_data(fixture_id=None, *args, **kwargs) -> dict:
    """
    Compatibility shim — fetch_full_match_data was removed from live_data.py.
    Returns an empty safe structure. Use live_data.fetch_live_matches() instead.
    """
    return {}
