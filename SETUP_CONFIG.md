# SOCCER EDGE ENGINE - SETUP & CONFIGURATION GUIDE

## 🔑 API KEYS & CREDENTIALS

### **Step 1: Get API Football Key**

The project is configured to use **API-Football** (api-sports.io).

1. Visit: https://rapidapi.com/api-sports/api/api-football
2. Sign up for FREE (limited to 30 requests/day)  
   OR Subscribe ($10-50/month for production use)
3. Copy your API key
4. Create a `.env` file in the project root:

```bash
# .env (Create this file in /workspaces/soccer-edge-engine/)
API_FOOTBALL_KEY=your_actual_key_here_from_rapidapi
```

### **Step 2: Test the API Connection**

```bash
cd /workspaces/soccer-edge-engine/
python live_data.py
```

Expected output (if key is valid):
```
Loaded key: True Length: 32
Found 5 live matches:
Arsenal vs Manchester City | 45' | 1-2
... (more matches)
```

---

## 📦 PYTHON DEPENDENCIES

The project uses these external packages:

### **Already Installed (Standard Library):**
- `tkinter` - GUI framework (built-in Python)
- `csv` - CSV handling (built-in)
- `dataclasses` - Data structures (built-in Python 3.7+)
- `math` - Mathematics (built-in)
- `pathlib` - File paths (built-in)

### **Needs Installation:**
- `requests` - HTTP requests for APIs
- `python-dotenv` - Environment variable management

**Install required packages:**

```bash
pip install requests python-dotenv
```

---

## 🗂️ PROJECT FILE STRUCTURE

```
soccer-edge-engine/
├── .env                          # ⭐ CREATE THIS - API keys
├── .gitignore                    # Already present
├── 
├── CORE ENGINE
├── soccer_phase1_engine.py       # Probability modeling
├── team_profiles.py              # Team strength database
├── team_stats.csv                # Team stats reference
├──
├── GUI & INTERFACE
├── soccer_gui.py                 # Main GUI (Tkinter)
├── 
├── DATA & HISTORY
├── history_logger.py             # Analysis logging
├── analysis_history.csv          # Auto-generated after first analysis
├── watchlist.py                  # In-memory match watchlist
├──
├── LIVE DATA
├── live_data.py                  # API integration (needs completion)
├──
├── DOCUMENTATION
├── PROJECT_ROADMAP.md            # Original roadmap
├── PROJECT_ANALYSIS.md           # ⭐ New comprehensive analysis
├── SETUP_CONFIG.md               # This file
├──
└── TESTING
   └── test.py                     # Test utilities
```

---

## 🚀 QUICK START GUIDE

### **1. Install Dependencies**
```bash
cd /workspaces/soccer-edge-engine/
pip install requests python-dotenv
```

### **2. Create `.env` File**
```bash
cat > .env << 'EOF'
API_FOOTBALL_KEY=your_key_from_rapidapi
EOF
```

### **3. Run the GUI**
```bash
python soccer_gui.py
```

### **4. Test Manual Analysis**
- Enter teams: Home Team = "Arsenal", Away Team = "Manchester City"
- Set minute = 45
- Set scores: Home Goals = 1, Away Goals = 0
- Set market prices (e.g., Draw = 40, Under = 45, Over = 60)
- Click **"Analyze"**
- See edge calculations in the output panel

### **5. Test Live Data Fetch**
```bash
python live_data.py
```
- Should display currently live matches
- If key works: shows match list
- If key doesn't work: shows error message

---

## ⚙️ CONFIGURATION OPTIONS

### **Soccer Edge Engine Settings**

In `soccer_phase1_engine.py`, the `ModelConfig` class controls:

```python
class ModelConfig:
    baseline_total_goals = 2.5        # Expected goals per 90 min
    draw_bias_base = 0.25             # Base draw probability
    red_card_total_goal_boost = 0.10  # +10% per red card difference
    late_game_slowdown = 0.85         # 85% goal rate after 75'
    early_game_boost = 1.03           # 103% goal rate before 20'
    pressure_total_boost_per_step = 0.03  # Pressure effect per level
```

**To adjust model sensitivity:**

Edit the constants in the `ModelConfig` dataclass:
- Lower `baseline_total_goals` → More conservative (fewer high edges)
- Raise `baseline_total_goals` → More aggressive
- Adjust `late_game_slowdown` → Earlier/later scoring trends

### **GUI Theme Customization**

Color scheme in `soccer_gui.py` (line 7-17):

```python
BG = "#111827"           # Main background
CARD = "#1f2937"         # Card background
CARD2 = "#0f172a"        # Darker card
TEXT = "#f9fafb"         # Main text (white)
MUTED = "#9ca3af"        # Muted text
GREEN = "#22c55e"        # High value edges
RED = "#ef4444"          # Avoid/Low edges
CYAN = "#22d3ee"         # Highlights
GOLD = "#fbbf24"         # Headers
PURPLE = "#6366f1"       # Buttons
PURPLE_HOVER = "#7c83ff" # Hover state
BORDER = "#374151"       # Card borders
```

---

## 📊 TEAM STATS DATABASE

The `team_stats.csv` file contains team strength profiles:

```csv
team,attack,defense,draw,late
Arsenal,1.15,0.95,0.90,1.05
Manchester City,1.20,0.90,0.85,1.10
Liverpool,1.10,0.92,0.88,1.08
...
```

**Multipliers explained:**
- **attack**: 1.0 = average, 1.2 = strong, 0.8 = weak
- **defense**: 1.0 = average, 0.9 = solid, 1.1 = porous
- **draw**: 1.0 = neutral, 0.8 = avoid draws, 1.2 = prone to draws
- **late**: 1.0 = consistent, 1.1 = strong late game, 0.9 = fades

**To add/update teams:**

1. Edit `team_stats.csv` with a CSV editor or text editor
2. Add new row: `NewTeam,1.0,1.0,1.0,1.0`
3. Save file
4. Profiles auto-reload on next analysis

---

## 🔄 DATA FLOW EXPLANATION

### **Current Manual Flow:**

```
User Input (GUI)
  ↓
MatchState + MarketInput
  ↓
SoccerEdgeEngine.full_analysis()
  ↓
Calculate probabilities (Poisson)
  ↓
Compare vs market prices
  ↓
Calculate edge = Model Fair Value - Market Price
  ↓
Log to CSV (analysis_history.csv)
  ↓
Display results in GUI
```

### **Target Live Flow (Phase 2+):**

```
[API-Football] Fetch live matches every 10s
  ↓
Extract match state (minute, score, etc.)
  ↓
[Odds APIs] Fetch current betting odds
  ↓
SoccerEdgeEngine.full_analysis()
  ↓
Calculate edge automatically
  ↓
Store in SQLite database
  ↓
Update GUI in real-time
  ↓
Trigger notifications for HIGH VALUE edges
```

---

## 💾 DATA PERSISTENCE

### **Current CSV System**

Files created after first analysis:
- `analysis_history.csv` - All analyses logged here
- Columns: timestamp, home_team, away_team, minute, scores, market prices, recommended, edge, confidence, result

### **Recommended Database Migration (Phase 2)**

Create SQLite database for 100x faster queries:

```python
import sqlite3

conn = sqlite3.connect('soccer_edge.db')
cursor = conn.cursor()

# Create analyses table
cursor.execute('''
CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    home_team TEXT,
    away_team TEXT,
    minute INTEGER,
    home_goals INTEGER,
    away_goals INTEGER,
    draw_price REAL,
    under_price REAL,
    over_price REAL,
    recommended TEXT,
    best_edge REAL,
    confidence TEXT,
    settled BOOLEAN
)
''')

conn.commit()
conn.close()
```

---

## 🧪 TESTING SCENARIOS

### **Test 1: Basic Edge Calculation**

Input:
- Match: Arsenal vs Manchester City, 45', 1-1 score
- Market: Draw 35c, Under 50c, Over 60c

Expected output:
- Edge calculation against each market
- Recommended pick with best edge highlighted
- Confidence level (HIGH/MEDIUM/LOW)

### **Test 2: Red Card Impact**

Input:
- Manchester United vs Liverpool, 60', 0-1 score
- Manchester United with 1 red card
- Market: Draw 45c, Under 40c, Over 65c

Expected output:
- Higher goal probability (+10% boost)
- Over edge should increase

### **Test 3: Late Game Deceleration**

Input:
- Barcelona vs Real Madrid, 85', 2-2 score
- Market: Draw 50c, Under 70c, Over 45c

Expected output:
- Lower remaining goal probabilities
- Under 2.5 edge should increase

### **Test 4: Live API**

Run:
```bash
python live_data.py
```

Expected:
- Lists 5-20 currently live matches
- Shows proper formatting
- No API errors

---

## 🐛 TROUBLESHOOTING

### **Issue: "ModuleNotFoundError: No module named 'requests'"**
**Solution:**
```bash
pip install requests
```

### **Issue: "ModuleNotFoundError: No module named 'dotenv'"**
**Solution:**
```bash
pip install python-dotenv
```

### **Issue: ".env file not found" - API returns empty**
**Solution:**
1. Ensure `.env` exists in project root
2. Check it contains: `API_FOOTBALL_KEY=your_actual_key`
3. Run `python live_data.py` to test

### **Issue: "Error: 403 Forbidden" from API**
**Cause:** API key is invalid or quota exceeded  
**Solution:**
1. Verify key from RapidAPI dashboard
2. Check plan limit (free = 30 req/day)
3. Consider upgrading subscription

### **Issue: GUI doesn't load (Tkinter error)**
**Solution:**
```bash
# Linux
sudo apt-get install python3-tk

# macOS
brew install python-tk

# Windows
# Usually pre-installed; check Python installer
```

### **Issue: CSV analysis_history.csv has errors**
**Solution:**
```bash
# Delete the corrupted file
rm analysis_history.csv

# GUI will recreate it on next analysis
python soccer_gui.py
```

---

## 📈 NEXT PHASE: IMPLEMENTATION CHECKLIST

- [ ] **Phase 2A: Database Migration**
  - [ ] Create SQLite schema
  - [ ] Migrate CSV data
  - [ ] Update history_logger.py to use DB

- [ ] **Phase 2B: 3-Column GUI Redesign**
  - [ ] Refactor soccer_gui.py with grid layout
  - [ ] Create LEFT panel (stats/leagues)
  - [ ] Create CENTER panel (scoreboard)
  - [ ] Create RIGHT panel (edges/recommendations)

- [ ] **Phase 2C: Live Data Integration**
  - [ ] Enhance live_data.py functions
  - [ ] Background thread for API polling
  - [ ] Real-time GUI updates

- [ ] **Phase 2D: Color Coding & Alerts**
  - [ ] Add edge classification UI
  - [ ] Color code by confidence
  - [ ] Add audio/visual alerts

- [ ] **Phase 3: Mobile & Performance**
  - [ ] API caching layer
  - [ ] Database indexing
  - [ ] Web dashboard (optional)

---

## 📞 USEFUL LINKS

- **API-Football Docs:** https://www.api-football.com/documentation-v3
- **RapidAPI:** https://rapidapi.com/api-sports/api/api-football
- **Poisson Distribution:** https://en.wikipedia.org/wiki/Poisson_distribution
- **Sports Betting Terminology:** https://en.wikipedia.org/wiki/Betting_exchange

---

**Ready to activate your APIs? Let's build the ultimate soccer edge finder!** ⚽🚀
