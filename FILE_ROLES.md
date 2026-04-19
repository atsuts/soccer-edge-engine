# Soccer Edge Engine - File Roles

## MAIN LAUNCHER
- **soccer_gui.py** - Single official main launcher for the application
  - Enhanced left panel with scanner-style navigation
  - Full Soccer Edge Engine functionality
  - Run this file to start the application

## ALTERNATIVE LAUNCHER
- **main.py** - Small wrapper that launches the current GUI

## ARCHIVED REFERENCES
- **archive/** - Old GUI experiments and backup versions kept for reference

## SUPPORTING MODULES
- **soccer_phase1_engine.py** - Core analysis engine
- **history_logger.py** - History and accuracy tracking
- **watchlist.py** - Watchlist management
- **live_data.py** - Live match data fetching
- **team_profiles.py** - Team profile data

## CONFIGURATION
- **.vscode/launch.json** - VS Code launch configuration
- **run.bat** - Windows batch launcher
- **LAUNCHER_GUIDE.md** - Launcher setup guide
- **PROJECT_CONFIG.md** - Project configuration documentation

## DATA FILES
- **analysis_history.csv** - Analysis history
- **watchlist.json** - Watchlist data
- **team_stats.csv** - Team statistics

---

## HOW TO RUN

### Primary Method:
```bash
python soccer_gui.py
```

### Alternative Methods:
- Double-click `run.bat` (Windows)
- Use VS Code Run/Play button (configured to launch soccer_gui.py)
- Use `python main.py` (wrapper launcher)

---

**IMPORTANT**: Always use `soccer_gui.py` as the main launcher. Archived versions are reference only.
