#!/usr/bin/env python3
"""
Web-based Soccer Edge Engine GUI
Works in VS Studio/Codespaces without display issues
"""

import json
import csv
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from soccer_phase1_engine import SoccerEdgeEngine, MatchState, MarketInput
from history_logger import log_analysis, settle_match_by_index, summarize_accuracy
from watchlist import add_match, get_watchlist, get_match_by_index

app = Flask(__name__)

# Load data
HISTORY_FILE = Path(__file__).with_name('analysis_history.csv')

# Mock data for filters
MOCK_DATA = {
    'countries': ['ALL', 'England', 'Spain', 'Italy', 'Germany', 'France'],
    'leagues': {
        'ALL': ['ALL', 'Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1'],
        'England': ['ALL', 'Premier League', 'Championship', 'League One', 'League Two'],
        'Spain': ['ALL', 'La Liga', 'Segunda Division', 'Copa del Rey'],
        'Italy': ['ALL', 'Serie A', 'Serie B', 'Coppa Italia'],
        'Germany': ['ALL', 'Bundesliga', '2. Bundesliga', 'DFB Pokal'],
        'France': ['ALL', 'Ligue 1', 'Ligue 2', 'Coupe de France']
    }
}

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html', data=MOCK_DATA)

@app.route('/api/watchlist')
def api_watchlist():
    """Get watchlist data"""
    try:
        watchlist = get_watchlist()
        return jsonify(watchlist)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/history')
def api_history():
    """Get analysis history"""
    try:
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                history = list(reader)
            return jsonify(history)
        return jsonify([])
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """Run analysis on match"""
    try:
        data = request.json
        home_team = data.get('home_team')
        away_team = data.get('away_team')
        
        if not home_team or not away_team:
            return jsonify({'error': 'Home and away teams required'})
        
        # Create engine instance
        engine = SoccerEdgeEngine()
        
        # Create match state
        match_state = MatchState(
            home_team=home_team,
            away_team=away_team,
            home_score=data.get('home_score', 0),
            away_score=data.get('away_score', 0),
            minute=data.get('minute', 0),
            is_live=data.get('is_live', False)
        )
        
        # Run analysis
        result = engine.analyze_match(match_state)
        
        # Log to history
        log_analysis(match_state, result)
        
        return jsonify({
            'success': True,
            'result': result.__dict__ if hasattr(result, '__dict__') else str(result)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/add_to_watchlist', methods=['POST'])
def api_add_to_watchlist():
    """Add match to watchlist"""
    try:
        data = request.json
        match_id = add_match(
            data.get('home_team'),
            data.get('away_team'),
            data.get('league', 'Unknown'),
            data.get('kickoff_time', 'Unknown')
        )
        return jsonify({'success': True, 'match_id': match_id})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    print("Starting Soccer Edge Engine Web GUI...")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)
