# Soccer Edge Engine - Comprehensive Project Analysis

**Current Date:** April 11, 2026  
**Status:** Phase 1 Complete (Manual Analysis) → Phase 2 Ready (Live Integration)

---

## 📊 EXECUTIVE SUMMARY

The **Soccer Edge Engine** is a sophisticated real-time soccer betting analysis and edge-finding platform. It currently has:

✅ **Strong Foundation:** Poisson-based probability model, team profiling system, CSV-based history tracking  
✅ **Working GUI:** Modern Tkinter dashboard with manual input capability  
✅ **Core Engine:** Proven edge detection algorithm comparing model vs market prices  

⚠️ **Needs Completion:** API integration, live data feeds, 3-column UI architecture, color-coded edge signals

---

## 🏗 CURRENT ARCHITECTURE

### **Project Structure**

```
soccer-edge-engine/
├── soccer_phase1_engine.py       # Core probability engine (Poisson-based)
├── soccer_gui.py                 # Current UI (Tkinter) - Manual input only
├── team_profiles.py              # Team strength database
├── team_stats.csv                # Team statistics reference
├── history_logger.py             # CSV-based analysis tracking
├── live_data.py                  # API-football integration (stub)
├── watchlist.py                  # In-memory match watchlist
├── test.py                       # Test utilities
└── PROJECT_ROADMAP.md            # Development guide
```

---

## 🔧 TECHNICAL BREAKDOWN

### **1. Core Engine** (`soccer_phase1_engine.py`)
**Status:** ✅ Fully Functional

**Capabilities:**
- Poisson probability distribution for goal prediction
- Dynamic team strength profiles (attack, defense, draw bias, late-game tendencies)
- Real-time match state modeling (minute, score, red cards, pressure bias)
- Edge calculation: `Edge = Model Fair Value (cents) - Market Price (cents)`

**Key Features:**
- Baseline goal modeling: ~2.5 goals per 90 minutes
- Time decay factor: Goals taper as time decreases
- Red card impact: +10% goal boost per card differential
- Pressure bias modeling: -2 to +2 scale for home/away advantage
- Late-game slowdown: After 75', goal rate reduces by 15%
- Early-game boost: Before 20', goal rate increases by 3%

**Functions:**
```python
- estimate_remaining_goal_rate()  # Calculate expected goals
- draw_probability()              # Draw outcome probability
- under_over_2_5()               # Over/Under 2.5 probability
- full_analysis()                # Complete market comparison
- fair_cents()                   # Convert probability to betting odds
```

**Output Format:** Probability estimates with edge signals (HIGH VALUE, VALUE, SMALL EDGE, AVOID)

---

### **2. Current GUI** (`soccer_gui.py`)
**Status:** ⚠️ Functional but Limited

**Current Layout:**
- **LEFT SIDEBAR:** Match input form + watchlist + history
- **RIGHT PANEL:** Model output + team profiles + accuracy dashboard
- **NO CENTER PANEL:** Missing dedicated scoreboard view

**Current Features:**
- Manual match input (home team, away team, minute, score, etc.)
- Live tracker: Auto-advances minute counter
- Watchlist management: Save interesting matches
- History tracking: Last 10 analyses
- Accuracy dashboard: Win rate statistics

**Color Scheme:**
- Background: `#111827` (dark charcoal)
- Cards: `#1f2937` (slightly lighter)
- Text: `#f9fafb` (nearly white)
- Accents: Cyan, Green, Red, Gold, Purple

**Missing Elements:**
- ❌ Live API data feeds
- ❌ 3-column layout (Left/Center/Right panels explicitly designed)
- ❌ Live scoreboard/match clock
- ❌ Real-time odds integration
- ❌ Edge recommendation highlights
- ❌ League/country stats sidebar
- ❌ Match history database

---

### **3. Team Profiles** (`team_profiles.py`)
**Status:** ✅ Functional (Dynamic)

**Features:**
- Loads from `team_stats.csv`
- Profiles per team:
  - **Attack multiplier:** Offensive strength (typically 0.8-1.2)
  - **Defense multiplier:** Defensive solidity (typically 0.8-1.2)
  - **Draw bias:** Tendency to draw (typically 0.8-1.2)
  - **Late-game bias:** Second-half scoring strength (typically 0.8-1.2)
- Fallback to DEFAULT_PROFILE if team not found

---

### **4. History Logger** (`history_logger.py`)
**Status:** ✅ Fully Functional

**Tracks per Analysis:**
- Match details (teams, minute, score)
- Market inputs (draw, under, over prices)
- Model predictions (draw prob, under prob, over prob)
- Recommended pick + confidence + edge value
- Settlement data (final score, hit/miss tracking)

**Functions:**
```python
- log_analysis()           # Save new analysis
- settle_match_by_index()  # Mark match as completed
- summarize_accuracy()     # Calculate win rates
```

**Output:** `analysis_history.csv` with 25 fields

---

### **5. Live Data Module** (`live_data.py`)
**Status:** 🚧 Incomplete (Stub Only)

**Current State:**
```python
- Loads API_FOOTBALL_KEY from .env file
- fetch_live_matches() function exists but NOT INTEGRATED
- Returns: home, away, minute, home_goals, away_goals for live matches
```

**Missing:**
- ❌ Actual API calls to fetch leagues/countries
- ❌ Real-time odds data integration
- ❌ Scheduled refresh mechanism
- ❌ Error handling and retry logic
- ❌ Rate limiting for API calls

---

### **6. Watchlist** (`watchlist.py`)
**Status:** ✅ Functional (In-Memory)

**Features:**
- Add matches for tracking
- Retrieve by index
- In-memory storage only (NOT persistent)

**Missing:**
- ❌ Database persistence (SQLite or CSV)
- ❌ Match status tracking
- ❌ Notification system

---

## 🎯 YOUR VISION: 3-COLUMN LAYOUT

### **LEFT COLUMN - STATISTICS & MATCH LIBRARY**
**What it should show:**
- 🌍 Countries/Leagues filter
- 📊 League statistics (teams, matches, trends)
- 📅 Match history database (filterable by date, league, team)
- 🏆 Top performers/worst performers
- 📈 Historical win rates by league/team

**Data Needed:**
- Live leagues API call
- Historical match database
- League stats aggregation

---

### **CENTER COLUMN - LIVE SCOREBOARD & MATCH DETAIL**
**What it should show:**
- ⚽ Selected match scoreboard (large, easy to read)
- 🕐 Live match timer/minute counter
- 📊 Real-time stats:
  - Possession %
  - Shots on target
  - Cards (yellow/red)
  - Fouls
  - Offsides
- 📈 Live probability updates
- 💰 Current odds (multiple books)

**Design Elements:**
- Large digital clock showing match status
- Color-coded team sections (home/away)
- Live stat updates every 5-10 seconds
- "FINISHED" | "LIVE" | "NOT STARTED" badges

---

### **RIGHT COLUMN - EDGE ANALYSIS & RECOMMENDATIONS**
**What it should show:**
- 🎯 Top recommended edges (color-coded by confidence)
  - HIGH VALUE (edge ≥ +25c) - 🟢 Green
  - VALUE (edge 8-25c) - 🟡 Yellow
  - SMALL EDGE (edge 0-8c) - 🔵 Blue
  - AVOID (edge ≤ 0c) - 🔴 Red
- 📊 Market comparison table (Model vs Market vs Edge)
- ⭐ Confidence indicator
- 💡 Quick insight trends
- 📋 Recommended action
- 🔔 Odds movement alerts

**Real-Time Updates:**
- Auto-refresh odds every 10-30 seconds
- Highlight changed edges
- Track edge movement

---

## 🔑 CRITICAL API INTEGRATIONS NEEDED

### **1. Football Data API** (Choose ONE)

**Option A: API-Football (api-sports.io)** - Currently set up
- ✅ Already configured in `live_data.py`
- ✅ Requires: `API_FOOTBALL_KEY` in `.env`
- Features: Live fixtures, statistics, odds, schedules
- Endpoints needed:
  ```
  GET /fixtures           # Live/upcoming matches
  GET /fixtures?live=all  # All live matches
  GET /leagues           # League list with statistics
  GET /standings         # League standings
  GET /statistics        # Team/League statistics
  ```

**Option B: Odds API (oddsapi.com)**
- Better for odds comparison
- Multi-book odds data
- Requires separate key

### **2. Odds Integration** (Multi-Book)

Need to track odds from:
- Kalshi (binary options)
- Betfair
- DraftKings
- FanDuel
- Multiple Sportsbooks

### **3. Data Flow Architecture**

```
[API-Football] → Fetch live matches/stats → [Soccer Edge Engine]
                                           ↓
                                    Probability calc
                                           ↓
[Odds Feeds] ← Pull current odds ← [Edge Detection]
                                           ↓
                                    [GUI Update]
```

---

## 💾 DATABASE NEEDS

Current system uses CSV only. For production, needs:

```sql
-- Teams
CREATE TABLE teams (
  id PRIMARY KEY,
  name,
  attack_multiplier,
  defense_multiplier,
  draw_bias,
  late_bias
);

-- Leagues
CREATE TABLE leagues (
  id PRIMARY KEY,
  name,
  country,
  season,
  matches_count
);

-- Matches (History)
CREATE TABLE matches (
  id PRIMARY KEY,
  league_id,
  home_team,
  away_team,
  date,
  final_score_home,
  final_score_away,
  status (LIVE, FINISHED, NOT_STARTED)
);

-- Analyses (Replace analysis_history.csv)
CREATE TABLE analyses (
  id PRIMARY KEY,
  match_id,
  timestamp,
  model_draw_prob,
  model_under_prob,
  model_over_prob,
  market_draw,
  market_under,
  market_over,
  recommended_play,
  edge_value,
  confidence,
  result (HIT, MISS, NULL)
);

-- Watchlist
CREATE TABLE watchlist (
  id PRIMARY KEY,
  user_id,
  match_id,
  added_timestamp,
  status (ACTIVE, COMPLETED)
);
```

---

## 🎨 UI/UX ENHANCEMENT ROADMAP

### **Phase 2: Modern 3-Column Layout**
- [ ] Redesign GUI with 3 distinct panels
- [ ] Add live match data display
- [ ] Implement real-time scoreboard

### **Phase 2A: Color Coding & Visual Signals**
- [ ] High-value edges: Bright green + highlight
- [ ] Medium edges: Yellow/amber
- [ ] Avoid zones: Red with warning
- [ ] Confidence levels: Star ratings or progress bars

### **Phase 2B: Real-Time Data Integration**
- [ ] Live match APIs
- [ ] Automated odds polling
- [ ] Push notifications for high-edge opportunities

### **Phase 2C: Advanced Features**
- [ ] Multi-league statistics sidebar
- [ ] Historical trend analysis
- [ ] Bankroll management calculator
- [ ] ROI tracking per league/team
- [ ] Export reports (PDF/CSV)

---

## 📋 QUICK WINS (Short-Term Improvements)

1. **Create `.env` template**
   ```
   API_FOOTBALL_KEY=your_key_here
   API_ODDS_KEY=optional
   ```

2. **Add DB initialization script** (SQLite)
   ```python
   # Initialize database.py
   import sqlite3
   # Create schema above
   ```

3. **Enhance live_data.py** with league fetching
   ```python
   def fetch_leagues()
   def fetch_team_stats()
   def fetch_live_odds()
   ```

4. **Redesign soccer_gui.py** into 3-column layout
   - Use grid layout instead of pack
   - Left: Statistics panel
   - Center: Scoreboard panel  
   - Right: Edge analysis panel

5. **Add edge notification system**
   - Highlight HIGH VALUE edges
   - Color code by confidence
   - Add audio/visual alerts

---

## ⚡ PERFORMANCE & SCALING

**Current Bottlenecks:**
- Manual data entry required
- No persistent watchlist storage
- CSV-based history (slow for large datasets)
- No API caching

**Optimization Opportunities:**
1. Implement Redis caching for API responses
2. Switch to SQLite for history (100x faster than CSV)
3. Background worker thread for odds updates
4. Database indexing on frequently queried fields

---

## 📈 SUCCESS METRICS

When fully implemented, you'll have:

✅ **Live multi-league scoreboard** with real-time updates  
✅ **Automatic edge detection** across 100+ matches  
✅ **Color-coded signals** (green/yellow/red confidence)  
✅ **Historical performance tracking** (win rate by league/odds)  
✅ **Mobile-ready responsive design**  
✅ **1-click bet recommendations** with alt odds options  

---

## 🚀 NEXT STEPS RECOMMENDATION

1. **First:** Set up `.env` with API keys → Test live_data functions
2. **Second:** Implement 3-column GUI layout
3. **Third:** Integrate live match data into center panel
4. **Fourth:** Build odds polling system
5. **Fifth:** Create database layer (replace CSV)
6. **Sixth:** Add edge notifications & color coding
7. **Seventh:** Performance optimization & scaling

---

## 📞 CURRENT LIMITATIONS

| Feature | Status | Priority |
|---------|--------|----------|
| Manual match input | ✅ Working | - |
| Probability modeling | ✅ Working | - |
| History CSV tracking | ✅ Working | Medium |
| Live API integration | 🚧 50% | HIGH |
| 3-column UI layout | ❌ Missing | HIGH |
| Real-time scoreboard | ❌ Missing | HIGH |
| Odds integration | ❌ Missing | HIGH |
| Color-coded edges | ⚠️ Partial | MEDIUM |
| Database persistence | ❌ Missing | MEDIUM |
| League statistics | ❌ Missing | MEDIUM |

---

**Ready to build? Let's start with Phase 2 implementation!** 🎯
