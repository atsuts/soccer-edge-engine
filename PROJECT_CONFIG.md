# Soccer Edge Engine - Project Configuration

## 🎯 Official Main Launcher

**`soccer_gui.py`** is the single official main GUI launcher for this project.

## 🚀 One-Click Execution

### Method 1: VS Code / Cursor
1. Open `soccer_gui.py` in editor
2. Press F5 or Run → Start Debugging
3. Uses `.vscode/launch.json` configuration

### Method 2: Double-Click (Windows)
- Double-click `run.bat` file
- Automatically launches `soccer_gui.py`

### Method 3: Command Line
```bash
python soccer_gui.py
```

## 📁 Project Files Status

### ✅ Active Files
- `soccer_gui.py` - **MAIN LAUNCHER** (official)
- `main.py` - Alternative wrapper launcher
- `.vscode/launch.json` - VS Code run configuration
- `run.bat` - Windows batch launcher

### 📦 Backup Files (Do NOT delete)
- `soccer_gui_clean.py` - Clean version copy
- `soccer_dashboard.py` - Experimental dashboard
- `LAUNCHER_GUIDE.md` - Detailed setup guide

## ⚙️ Run Configuration

### VS Code Settings
- Launch configuration targets `soccer_gui.py`
- Working directory set to project root
- Integrated terminal for output

### File Structure
```
DesktopSoccerEdgeEngine/
├── soccer_gui.py          # ← MAIN LAUNCHER (official)
├── main.py               # ← Alternative launcher
├── run.bat               # ← Windows batch launcher
├── .vscode/
│   └── launch.json       # ← VS Code config
├── soccer_gui_clean.py   # ← Backup copy
├── soccer_dashboard.py    # ← Experimental
└── PROJECT_CONFIG.md     # ← This file
```

## 🎮 Usage

**To run the Soccer Edge Engine:**
1. Open `soccer_gui.py` in your IDE
2. Press Run/Play button (F5)
3. OR double-click `run.bat` (Windows)
4. OR run `python soccer_gui.py` in terminal

**Result:** GUI launches immediately with full functionality.

## ✅ Verification

Tested and confirmed:
- ✅ `python soccer_gui.py` runs successfully
- ✅ VS Code launch configuration created
- ✅ Windows batch launcher created
- ✅ Error handling implemented
- ✅ One-click execution working

## 📋 Notes

- No UI redesign performed
- No app rewrite - only launcher setup
- Old files preserved as backups
- Single clear entry point established
- One-click run configured for IDEs
