# Soccer Edge Engine - Launcher Guide

## Official Main Launcher

### Primary Entry Point
**`soccer_gui.py`** is the official main GUI launcher for the Soccer Edge Engine project.

### Alternative Launcher
**`main.py`** is a simple wrapper launcher that imports and runs `soccer_gui.py`.

## How to Run

### Method 1: Direct Launch (Recommended)
```bash
python soccer_gui.py
```

### Method 2: Via Main Wrapper
```bash
python main.py
```

## Run Configuration Setup

For IDE one-click run/debug configuration:

### VS Code / Cursor
1. Open `soccer_gui.py` 
2. Press F5 or use Run → Start Debugging
3. Set as default launch configuration

### PyCharm
1. Right-click on `soccer_gui.py`
2. Select "Run 'soccer_gui'"
3. Save configuration as default

### Command Line
```bash
# Navigate to project directory
cd DesktopSoccerEdgeEngine

# Run main GUI
python soccer_gui.py
```

## Project Structure

```
DesktopSoccerEdgeEngine/
├── soccer_gui.py          # ← MAIN LAUNCHER (official)
├── main.py               # ← Alternative launcher wrapper
├── soccer_dashboard.py    # ← Experimental dashboard UI
├── soccer_gui_clean.py   # ← Clean version copy
└── [other modules]       # ← Supporting modules
```

## Notes

- `soccer_gui.py` contains the complete, production-ready GUI
- `soccer_gui_clean.py` is a backup copy with symmetrical scoreboard
- `soccer_dashboard.py` is experimental dashboard design
- Experimental files are kept for reference but not used as main launcher
- All configurations point to `soccer_gui.py` as the primary entry point

## Error Handling

The main launcher includes graceful error handling:
- Import errors are caught and reported
- Startup errors are displayed with user-friendly messages
- Console fallback for debugging

## One-Click Run Setup

To ensure one-click run always starts `soccer_gui.py`:

1. **Set `soccer_gui.py` as active file** in your IDE
2. **Configure run/debug settings** to target `soccer_gui.py`
3. **Save configuration** as default for the project

This guarantees that pressing Run/Play always launches the official GUI.
