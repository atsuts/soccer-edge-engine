# Soccer Edge Engine - File Roles

## MAIN LAUNCHER
- **soccer_gui.py** - Single official main launcher for the application
  - Enhanced left panel with scanner-style navigation
  - Full Soccer Edge Engine functionality
  - Run this file to start the application

## BACKUP FILES
- **main.py** - Backup launcher (use soccer_gui.py instead)
- **soccer_gui_clean.py** - Backup clean version (use soccer_gui.py instead)
- **soccer_gui_redesigned.py** - Old redesigned version (use soccer_gui.py instead)
- **soccer_dashboard.py** - Old dashboard prototype (use soccer_gui.py instead)

## TEST FILES
- **test.py** - Test file for development

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
- Use `python main.py` (backup launcher)

---

**IMPORTANT**: Always use `soccer_gui.py` as the main launcher. Other files are backups or test versions.
