# IMPLEMENTATION ROADMAP - PHASE 2+ ENHANCEMENTS

## 🚀 Quick Implementation Plan

This document outlines the exact steps to transform Soccer Edge Engine from a manual tool into a powerful automated edge finder.

---

## 📋 PHASE 2A: Database Layer (Week 1)

### Task: Replace CSV with SQLite

**Reason:** CSV is slow for large datasets, SQLite enables complex queries

**Files to create:**
1. `database.py` - SQLite schema and connection management
2. `models.py` - Python dataclasses for DB objects

**Quick Example:**

```python
# database.py
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).with_name("soccer_edge.db")

def init_database():
    """Create all tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Analyses table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        home_team TEXT NOT NULL,
        away_team TEXT NOT NULL,
        minute INTEGER,
        home_goals INTEGER,
        away_goals INTEGER,
        draw_price REAL,
        under_price REAL,
        over_price REAL,
        recommended TEXT,
        best_edge REAL,
        confidence TEXT,
        settled BOOLEAN DEFAULT 0,
        final_home_goals INTEGER,
        final_away_goals INTEGER,
        result TEXT
    )
    ''')
    
    # Watchlist table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS watchlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        home_team TEXT,
        away_team TEXT,
        added_at TEXT,
        status TEXT DEFAULT 'ACTIVE'
    )
    ''')
    
    conn.commit()
    conn.close()

def add_analysis(data: dict):
    """Save analysis to database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO analyses 
    (timestamp, home_team, away_team, minute, home_goals, away_goals,
     draw_price, under_price, over_price, recommended, best_edge, confidence)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().isoformat(),
        data['home_team'],
        data['away_team'],
        data['minute'],
        data['home_goals'],
        data['away_goals'],
        data['draw_price'],
        data['under_price'],
        data['over_price'],
        data['recommended'],
        data['best_edge'],
        data['confidence']
    ))
    
    conn.commit()
    conn.close()
```

---

## 📐 PHASE 2B: 3-Column GUI Redesign (Week 2)

### Task: Restructure soccer_gui.py with 3-column layout

**New Structure:**

```python
# soccer_gui_v2.py (Replacing soccer_gui.py)

import tkinter as tk
from tkinter import ttk

class SoccerEdgeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Soccer Edge Engine v2.0")
        self.root.geometry("1920x1080")
        
        # Create main 3-column layout
        self.create_left_panel()      # Statistics & Leagues
        self.create_center_panel()    # Live Scoreboard
        self.create_right_panel()     # Edge Analysis
    
    def create_left_panel(self):
        """LEFT COLUMN - Statistics, leagues, match history."""
        left = tk.Frame(self.root, bg="#1f2937", width=380)
        left.pack(side="left", fill="y", padx=10, pady=10)
        
        # League filter
        tk.Label(left, text="LEAGUES", bg="#1f2937", fg="#22d3ee", 
                 font=("Segoe", 12, "bold")).pack(fill="x", padx=10, pady=5)
        
        self.league_filter = ttk.Combobox(
            left, values=["Premier League", "La Liga", "Serie A", "Bundesliga"],
            state="readonly", width=30
        )
        self.league_filter.pack(fill="x", padx=10, pady=5)
        self.league_filter.bind("<<ComboboxSelected>>", self.on_league_change)
        
        # Match history list
        tk.Label(left, text="MATCH HISTORY", bg="#1f2937", fg="#22d3ee",
                 font=("Segoe", 12, "bold")).pack(fill="x", padx=10, pady=(15, 5))
        
        self.match_listbox = tk.Listbox(
            left, height=25, width=40, bg="#0f172a", fg="#f9fafb",
            font=("Consolas", 9)
        )
        self.match_listbox.pack(fill="both", expand=True, padx=10, pady=5)
        self.match_listbox.bind("<<ListboxSelect>>", self.on_match_select)
        
        # Load matches
        self.refresh_match_list()
    
    def create_center_panel(self):
        """CENTER COLUMN - Live scoreboard & match details."""
        center = tk.Frame(self.root, bg="#111827")
        center.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        # Match header
        tk.Label(center, text="LIVE MATCH", bg="#111827", fg="#22d3ee",
                 font=("Segoe", 14, "bold")).pack(fill="x", pady=5)
        
        # Scoreboard display
        scoreboard_frame = tk.Frame(center, bg="#1f2937", height=150)
        scoreboard_frame.pack(fill="x", padx=5, pady=10)
        
        # Home team
        self.home_team_label = tk.Label(
            scoreboard_frame, text="—", bg="#1f2937", fg="#f9fafb",
            font=("Segoe", 24, "bold")
        )
        self.home_team_label.pack(side="left", padx=20, pady=20)
        
        # Score
        self.score_label = tk.Label(
            scoreboard_frame, text="0 - 0", bg="#1f2937", fg="#22c55e",
            font=("Segoe", 32, "bold")
        )
        self.score_label.pack(side="left", padx=20, pady=20, expand=True)
        
        # Away team
        self.away_team_label = tk.Label(
            scoreboard_frame, text="—", bg="#1f2937", fg="#f9fafb",
            font=("Segoe", 24, "bold")
        )
        self.away_team_label.pack(side="left", padx=20, pady=20)
        
        # Match status
        self.minute_label = tk.Label(
            center, text="45' | LIVE", bg="#111827", fg="#fbbf24",
            font=("Segoe", 16, "bold")
        )
        self.minute_label.pack(fill="x", pady=10)
        
        # Live stats
        tk.Label(center, text="LIVE STATISTICS", bg="#111827", fg="#22d3ee",
                 font=("Segoe", 12, "bold")).pack(fill="x", pady=(15, 5))
        
        self.stats_text = tk.Text(
            center, height=15, bg="#0f172a", fg="#f9fafb",
            font=("Consolas", 10), relief="flat"
        )
        self.stats_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.stats_text.config(state="disabled")
    
    def create_right_panel(self):
        """RIGHT COLUMN - Edge recommendations & analysis."""
        right = tk.Frame(self.root, bg="#0f172a", width=380)
        right.pack(side="right", fill="y", padx=10, pady=10)
        
        tk.Label(right, text="EDGE RECOMMENDATIONS", bg="#0f172a", fg="#fbbf24",
                 font=("Segoe", 12, "bold")).pack(fill="x", padx=10, pady=5)
        
        # High value edges
        self.edge_display = tk.Text(
            right, height=30, width=40, bg="#111827", fg="#f9fafb",
            font=("Consolas", 9), relief="flat"
        )
        self.edge_display.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Color tags for edges
        self.edge_display.tag_configure("high_value", foreground="#22c55e", 
                                        font=("Consolas", 10, "bold"))
        self.edge_display.tag_configure("value", foreground="#fbbf24")
        self.edge_display.tag_configure("small", foreground="#22d3ee")
        self.edge_display.tag_configure("avoid", foreground="#ef4444")
        
        self.edge_display.config(state="disabled")
        
        # Action buttons
        button_frame = tk.Frame(right, bg="#0f172a")
        button_frame.pack(fill="x", padx=5, pady=5)
        
        tk.Button(button_frame, text="Refresh", bg="#22d3ee", fg="#001818",
                  command=self.refresh_edges).pack(fill="x", pady=2)
        
        tk.Button(button_frame, text="Add Watchlist", bg="#6366f1", fg="white",
                  command=self.add_to_watchlist).pack(fill="x", pady=2)
    
    def on_match_select(self, event):
        """Handle match selection from left panel."""
        selection = self.match_listbox.curselection()
        if selection:
            # Load match data and auto-populate center/right panels
            print(f"Selected match: {selection[0]}")
            self.refresh_scoreboard()
            self.refresh_edges()
    
    def on_league_change(self, event):
        """Handle league filter change."""
        league = self.league_filter.get()
        print(f"Filtering by: {league}")
        self.refresh_match_list()
    
    def refresh_match_list(self):
        """Populate left panel with matches from selected league."""
        # TODO: Fetch from database/API
        pass
    
    def refresh_scoreboard(self):
        """Update center panel with live match data."""
        # TODO: Fetch live match data
        pass
    
    def refresh_edges(self):
        """Calculate and display edge recommendations."""
        # TODO: Call SoccerEdgeEngine.full_analysis()
        pass
    
    def add_to_watchlist(self):
        """Add selected match to watchlist."""
        # TODO: Call watchlist database function
        pass


if __name__ == "__main__":
    root = tk.Tk()
    gui = SoccerEdgeGUI(root)
    root.mainloop()
```

---

## 🔄 PHASE 2C: Live Data Integration (Week 3)

### Task: Enhance live_data.py to fetch real data

**Current Status:** Stub. Next: Add league & live odds fetching

```python
# live_data.py (Enhanced version)

import os
import requests
from dotenv import load_dotenv
from functools import lru_cache
import time

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"

# Rate limiting
LAST_REQUEST_TIME = 0
MIN_INTERVAL = 0.5  # seconds between requests


def rate_limit():
    """Respect API rate limits."""
    global LAST_REQUEST_TIME
    elapsed = time.time() - LAST_REQUEST_TIME
    if elapsed < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - elapsed)
    LAST_REQUEST_TIME = time.time()


def fetch_leagues():
    """Get all available leagues."""
    rate_limit()
    
    url = f"{BASE_URL}/leagues"
    headers = {"x-apisports-key": API_KEY}
    params = {"season": 2023}
    
    response = requests.get(url, headers=headers, params=params, timeout=10)
    
    if response.status_code != 200:
        print(f"Error fetching leagues: {response.text}")
        return []
    
    data = response.json()
    leagues = []
    
    for league in data.get("response", [])[:10]:  # Top 10 leagues
        leagues.append({
            "id": league["league"]["id"],
            "name": league["league"]["name"],
            "country": league["league"]["country"],
            "type": league["league"]["type"],
            "season": league["seasons"][0]["year"] if league.get("seasons") else 2023
        })
    
    return leagues


def fetch_live_matches():
    """Get all currently live matches."""
    rate_limit()
    
    url = f"{BASE_URL}/fixtures"
    headers = {"x-apisports-key": API_KEY}
    params = {"live": "all"}
    
    response = requests.get(url, headers=headers, params=params, timeout=10)
    
    if response.status_code != 200:
        print(f"Error fetching live matches: {response.text}")
        return []
    
    data = response.json()
    matches = []
    
    for item in data.get("response", []):
        fixture = item["fixture"]
        teams = item["teams"]
        goals = item["goals"]
        statistics = item.get("statistics", [])
        
        # Extract possession data if available
        home_possession = 50
        for stat_group in statistics:
            if stat_group.get("team", {}).get("id") == teams["home"]["id"]:
                for stat in stat_group.get("statistics", []):
                    if stat["type"] == "Ball Possession":
                        home_possession = int(stat["value"].rstrip("%"))
        
        matches.append({
            "fixture_id": fixture["id"],
            "home": teams["home"]["name"],
            "away": teams["away"]["name"],
            "minute": fixture["status"]["elapsed"],
            "home_goals": goals["home"] or 0,
            "away_goals": goals["away"] or 0,
            "status": fixture["status"]["short"],
            "league": fixture.get("league", {}).get("name", "Unknown"),
            "home_possession": home_possession,
            "home_shots": 0,  # Would need another API call
            "away_shots": 0,
        })
    
    return matches


def fetch_team_stats(league_id: int, season: int = 2023):
    """Get team statistics for a league."""
    rate_limit()
    
    url = f"{BASE_URL}/statistics"
    headers = {"x-apisports-key": API_KEY}
    params = {"league": league_id, "season": season}
    
    response = requests.get(url, headers=headers, params=params, timeout=10)
    
    if response.status_code != 200:
        return {}
    
    data = response.json()
    stats = {}
    
    for team_stats in data.get("response", []):
        team_name = team_stats["team"]["name"]
        team_stats_data = team_stats.get("statistics", [])
        
        stats[team_name] = {
            "goals_for": next((s["value"] for s in team_stats_data 
                             if s["type"] == "Goals For"), 0),
            "goals_against": next((s["value"] for s in team_stats_data 
                                 if s["type"] == "Goals Against"), 0),
            "matches": next((s["value"] for s in team_stats_data 
                           if s["type"] == "Matches Played"), 0),
        }
    
    return stats


def fetch_live_odds():
    """
    Placeholder for odds integration.
    Would connect to Betfair, DraftKings, or odds aggregator API.
    """
    # TODO: Integrate with odds provider
    return {
        "draw": 40,
        "under": 45,
        "over": 60
    }


# Background refresh scheduler
class LiveDataManager:
    """Manage background updating of live data."""
    
    def __init__(self, refresh_interval=10):
        self.refresh_interval = refresh_interval
        self.live_matches = []
        self.leagues = []
        self.last_update = 0
    
    def update(self):
        """Fetch fresh data if interval has passed."""
        current_time = time.time()
        if current_time - self.last_update >= self.refresh_interval:
            self.live_matches = fetch_live_matches()
            self.last_update = current_time


if __name__ == "__main__":
    print("Testing API connections...\n")
    
    print("1. Fetching leagues...")
    leagues = fetch_leagues()
    print(f"   Found {len(leagues)} leagues:")
    for league in leagues[:3]:
        print(f"   - {league['name']} ({league['country']})")
    
    print("\n2. Fetching live matches...")
    matches = fetch_live_matches()
    print(f"   Found {len(matches)} live matches:")
    for match in matches[:5]:
        print(f"   - {match['home']} vs {match['away']} | {match['minute']}' | {match['home_goals']}-{match['away_goals']}")
```

---

## 🎨 PHASE 2D: Color-Coded Edges (Week 4)

### Task: Add color-coding for edge recommendations

**Add to soccer_gui.py:**

```python
def classify_edge_with_color(edge: float) -> tuple:
    """Return (classification, color_tag)."""
    if edge >= 25:
        return ("HIGH VALUE", "high_value", "🟢")
    elif edge >= 8:
        return ("VALUE", "value", "🟡")
    elif edge > 0:
        return ("SMALL EDGE", "small", "🔵")
    else:
        return ("AVOID", "avoid", "🔴")


def display_edge_recommendations(scored_rows, best_label, best_edge):
    """Enhanced edge display with color coding."""
    edge_display.config(state="normal")
    edge_display.delete("1.0", tk.END)
    
    edge_display.insert(tk.END, "🎯 EDGE RECOMMENDATIONS\n", "header")
    edge_display.insert(tk.END, "=" * 40 + "\n\n", "header")
    
    for row in scored_rows:
        classification, tag, icon = classify_edge_with_color(row["edge"])
        
        edge_display.insert(tk.END, f"{icon} {classification}\n", tag)
        edge_display.insert(tk.END, f"   {row['label']}\n", "white")
        edge_display.insert(tk.END, f"   Model: {row['model']:.1f}c | Market: {row['market']:.1f}c\n", "white")
        edge_display.insert(tk.END, f"   Edge: {row['edge']:+.1f}c\n", tag)
        edge_display.insert(tk.END, f"   {row['signal']}\n\n", tag)
    
    # Best recommendation
    if best_label:
        edge_display.insert(tk.END, "🎬 BEST PICK\n", "header")
        edge_display.insert(tk.END, f"{best_label}\n", "best")
        edge_display.insert(tk.END, f"Edge: {best_edge:+.1f}c\n\n", "best")
    
    edge_display.config(state="disabled")
```

---

## 📦 PHASE 3: Production Optimization (Week 5+)

### Critical tasks:

1. **API Rate Limiting Improvement**
   ```python
   # Add caching with TTL
   from functools import wraps
   import time
   
   def cache_with_ttl(ttl_seconds=60):
       def decorator(func):
           cache = {}
           cache_time = {}
           
           @wraps(func)
           def wrapper(*args, **kwargs):
               key = (args, tuple(kwargs.items()))
               current_time = time.time()
               
               if key in cache and current_time - cache_time[key] < ttl_seconds:
                   return cache[key]
               
               result = func(*args, **kwargs)
               cache[key] = result
               cache_time[key] = current_time
               return result
           
           return wrapper
       return decorator
   ```

2. **Database Indexing**
   ```python
   # Performance optimization
   cursor.execute('CREATE INDEX idx_timestamp ON analyses(timestamp)')
   cursor.execute('CREATE INDEX idx_recommendation ON analyses(recommended)')
   cursor.execute('CREATE INDEX idx_teams ON analyses(home_team, away_team)')
   ```

3. **Background Worker Thread**
   ```python
   import threading
   from queue import Queue
   
   class DataUpdateWorker(threading.Thread):
       def __init__(self, update_queue):
           super().__init__(daemon=True)
           self.queue = update_queue
       
       def run(self):
           """Continuously fetch live data."""
           while True:
               try:
                   live_matches = fetch_live_matches()
                   self.queue.put(("matches", live_matches))
                   time.sleep(10)
               except Exception as e:
                   print(f"Worker error: {e}")
   ```

---

## ✅ IMPLEMENTATION CHECKLIST

### Phase 2A: Database
- [ ] Create `database.py` with SQLite schema
- [ ] Migrate history_logger.py to use database
- [ ] Test data persistence
- [ ] Verify performance improvement

### Phase 2B: 3-Column GUI  
- [ ] Redesign main layout (left/center/right)
- [ ] Implement left panel (leagues, match list)
- [ ] Implement center panel (scoreboard)
- [ ] Implement right panel (edges)
- [ ] Wire up selection handlers
- [ ] Test responsiveness

### Phase 2C: Live Data
- [ ] Complete live_data.py functions
- [ ] Test API connections
- [ ] Add error handling
- [ ] Implement rate limiting
- [ ] Add data caching

### Phase 2D: Color Coding
- [ ] Add edge color mapping
- [ ] Update display functions
- [ ] Add text tags for colors
- [ ] Test color visibility

### Phase 3: Production
- [ ] Add API caching
- [ ] Database indexing
- [ ] Background worker thread
- [ ] Error logging
- [ ] Performance testing
- [ ] Documentation

---

**Ready to execute Phase 2?** Let's build it! 🚀
